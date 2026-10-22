import os
import re
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 讀取與本檔案同一個資料夾的 .env（backend/ai_service/.env）
load_dotenv(Path(__file__).parent / ".env")


# ─── LightRAG 連線設定 ───────────────────────────────────────────
def load_target(name: str, fallback_prefix: str = ""):
    """讀取一組 LightRAG 連線設定；沒有設定網址時回傳 None。"""
    url = os.getenv(f"LIGHTRAG_{name}_URL", "")
    key = os.getenv(f"LIGHTRAG_{name}_API_KEY", "")
    if not url and fallback_prefix:
        # 相容舊的變數名稱（LIGHTRAG_URL / LIGHTRAG_API_KEY）
        url = os.getenv(f"{fallback_prefix}_URL", "")
        key = os.getenv(f"{fallback_prefix}_API_KEY", "")
    if not url:
        return None
    return {"url": url.rstrip("/"), "key": key}


LIGHTRAG_TARGETS = {
    "public": load_target("PUBLIC", fallback_prefix="LIGHTRAG"),  # 雲端模型＋公開法規
    "company": load_target("COMPANY"),                            # 地端模型＋公司資料
}
SCOPE_LABELS = {"public": "公開法規", "company": "公司資料"}

# 地端模型回答較慢，逾時時間設長一點（秒）
LIGHTRAG_TIMEOUT = float(os.getenv("LIGHTRAG_TIMEOUT", "300"))

# 合規檢查中，雲端查法規那一步使用的查詢模式（mix 或 naive）
LAW_QUERY_MODE = os.getenv("LIGHTRAG_LAW_MODE", "mix")

# ─── 地端模型（Ollama）設定：合規檢查的最後比對步驟直接呼叫 ──────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b")
LOCAL_LLM_NUM_CTX = int(os.getenv("LOCAL_LLM_NUM_CTX", "8192"))

# 查不到資料時，模型會依提示詞回覆這些固定句子
LAW_NOT_FOUND = "知識庫中找不到相關條文"
FACTS_NOT_FOUND = "公司資料中找不到相關現況"


# ─── 提示詞 ──────────────────────────────────────────────────────
# 第一步（雲端 LightRAG）：只整理法規要求，不做合規判斷
LAW_PROMPT = (
    "你的任務是從知識庫的法規條文中，整理出與問題主題相關的法規要求。\n"
    "規則：\n"
    "1. 問題中的公司名稱、工地名稱、樓層和位置都請忽略。不要判斷是否符合規定，也不要提到你沒有現場資料。\n"
    "2. 不要開場白和結語，直接輸出條列。\n"
    "3. 每一點的格式為「法規名稱 第X條第X款：具體要求」，數值都要寫出來。\n"
    "4. 只能使用條文原文中的內容，而且一定要有條號。沒有條號的內容不要寫。\n"
    "5. 不要使用數學符號或 LaTeX，數值用文字表示，例如「30 平方公分以上」「不超過 2 公尺」。\n"
    "6. 不要出現「知識庫實體」「知識庫關係」這類字眼。\n"
    f"7. 如果找不到與問題主題直接相關的條文，只回答這一句：「{LAW_NOT_FOUND}」。"
)

# 第二步（地端 LightRAG）：只列出公司現況，不做判斷
FACTS_PROMPT = (
    "你的任務是從知識庫的公司資料中，找出與問題有關的現況。\n"
    "規則：\n"
    "1. 只列出公司資料中記載的事實，包含位置、項目和數值，盡量使用原文。\n"
    "2. 不要判斷是否符合法規，不要提到任何法規，也不要給建議。\n"
    "3. 不要開場白和結語，直接輸出條列。\n"
    f"4. 如果公司資料中沒有相關記載，只回答這一句：「{FACTS_NOT_FOUND}」。"
)

# 第三步（地端模型，直接呼叫 Ollama）：比對現況與法規要求
COMPARE_SYSTEM = (
    "你是營造工地的職業安全衛生稽核人員。"
    "你只能根據使用者提供的【公司現況】和【法規要求】進行比對，"
    "不得使用其他來源的法規或數值，也不得自行推測現況。"
    "請用繁體中文和臺灣用語回答，長度單位寫公分或公尺。"
)

COMPARE_TEMPLATE = (
    "【問題】\n{question}\n\n"
    "【公司現況】\n{facts}\n\n"
    "【法規要求】\n{law}\n\n"
    "請依照下列格式回答：\n\n"
    "一、現況摘要\n"
    "列出【公司現況】中與問題有關的事實。\n\n"
    "二、逐項比對\n"
    "每一項寫成一行：項目：現況 → 法規要求（法規名稱與條號）→ 符合 或 不符合。\n"
    "- 只比對【公司現況】有記載的項目。\n"
    "- 【法規要求】中的數字可能是國字，例如九十公分就是 90 公分，比對時請換算成阿拉伯數字。\n"
    "- 【法規要求】中有規定、但【公司現況】沒有記載的項目，集中列在最後，寫「公司資料未記載，無法判斷」。\n\n"
    "三、結論\n"
    "寫「符合」或「不符合」，並用一兩句話說明理由。\n\n"
    "四、改善建議\n"
    "針對不符合的項目，依【法規要求】的內容提出具體的改善方式。"
)


app = FastAPI()


# ─── 資料格式 ────────────────────────────────────────────────────
class PromptPayload(BaseModel):
    prompt: str = ""
    query: str = ""
    scope: Literal["public", "company"] = "public"


class CompliancePayload(BaseModel):
    prompt: str = ""
    query: str = ""


def get_question(query: str, prompt: str) -> str:
    """兼容前端傳送 query 或 prompt 欄位。"""
    question = (query or prompt).strip()
    if not question:
        raise HTTPException(status_code=400, detail="請提供 query 或 prompt")
    return question


def split_references(text: str) -> tuple[str, str]:
    """把回答拆成本文和 References 段落。"""
    parts = re.split(r"\n#+\s*References\s*\n", text, maxsplit=1, flags=re.IGNORECASE)
    return parts[0].strip(), (parts[1] if len(parts) > 1 else "")


def cited_references(text: str, references: list) -> list:
    """只保留回答中實際引用到的來源；判斷不出來時回傳全部。"""
    cited_ids = set(re.findall(r"\[(\d+)\]", text))
    cited = [r for r in references if str(r.get("reference_id")) in cited_ids]
    return cited or references


# ─── 共用：呼叫指定的 LightRAG 實例 ──────────────────────────────
async def ask_lightrag(scope: str, query: str, user_prompt: str = "", mode: str = "hybrid") -> dict:
    target = LIGHTRAG_TARGETS[scope]
    label = SCOPE_LABELS[scope]
    if target is None:
        raise HTTPException(status_code=503, detail=f"尚未設定{label}的 LightRAG 連線")

    body = {"query": query, "mode": mode}
    if user_prompt:
        body["user_prompt"] = user_prompt
    headers = {"X-API-Key": target["key"]} if target["key"] else {}

    async with httpx.AsyncClient(timeout=LIGHTRAG_TIMEOUT) as client:
        try:
            response = await client.post(f"{target['url']}/query", json=body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            hint = "，請檢查 API key 是否與該實例的設定一致" if status in (401, 403) else ""
            raise HTTPException(status_code=502, detail=f"{label}的 LightRAG 回傳錯誤 {status}{hint}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"{label}的 LightRAG 回應逾時")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"無法連線到{label}的 LightRAG: {str(e)}")


# ─── 共用：直接呼叫地端模型（Ollama）─────────────────────────────
async def ask_local_llm(system: str, user: str) -> str:
    body = {
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        # temperature 設為 0 讓輸出穩定；num_ctx 確保內容不會被截斷
        "options": {"temperature": 0, "num_ctx": LOCAL_LLM_NUM_CTX},
    }
    async with httpx.AsyncClient(timeout=LIGHTRAG_TIMEOUT) as client:
        try:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
            response.raise_for_status()
            return (response.json().get("message", {}).get("content") or "").strip()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"地端模型回傳錯誤 {e.response.status_code}，請確認模型 {LOCAL_LLM_MODEL} 已下載",
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="地端模型回應逾時")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"無法連線到地端模型（Ollama）: {str(e)}")


# ─── 端點一：單一來源問答（依 scope 選擇實例）────────────────────
@app.post("/api/forward-to-lightrag")
async def forward_to_lightrag(payload: PromptPayload):
    question = get_question(payload.query, payload.prompt)
    return await ask_lightrag(payload.scope, question)


# ─── 端點二：合規性檢查 ──────────────────────────────────────────
# 流程：雲端查法規 → 地端查公司現況 → 地端模型比對
@app.post("/api/compliance-check")
async def compliance_check(payload: CompliancePayload):
    question = get_question(payload.query, payload.prompt)

    # 第一步：雲端 LightRAG 整理相關的法規要求
    law_result = await ask_lightrag("public", question, LAW_PROMPT, mode=LAW_QUERY_MODE)
    law_full = (law_result.get("response") or "").strip()
    if not law_full:
        raise HTTPException(status_code=502, detail="公開法規的 LightRAG 沒有回傳內容")
    law_text, _ = split_references(law_full)
    law_refs = cited_references(law_full, law_result.get("references", []))

    if LAW_NOT_FOUND in law_text:
        return {
            "response": "法規知識庫中找不到與這個問題相關的條文，無法進行合規比對。",
            "law": law_text, "facts": "",
            "law_references": [], "company_references": [],
        }

    # 第二步：地端 LightRAG 找出公司資料中的相關現況
    facts_result = await ask_lightrag("company", question, FACTS_PROMPT)
    facts_full = (facts_result.get("response") or "").strip()
    if not facts_full:
        raise HTTPException(status_code=502, detail="公司資料的 LightRAG 沒有回傳內容")
    facts_text, _ = split_references(facts_full)
    company_refs = cited_references(facts_full, facts_result.get("references", []))

    if FACTS_NOT_FOUND in facts_text:
        return {
            "response": "公司資料中找不到與這個問題相關的現況，無法進行合規比對。",
            "law": law_text, "facts": facts_text,
            "law_references": law_refs, "company_references": [],
        }

    # 第三步：地端模型比對現況與法規要求，產生結論
    answer = await ask_local_llm(
        COMPARE_SYSTEM,
        COMPARE_TEMPLATE.format(question=question, facts=facts_text, law=law_text),
    )
    if not answer:
        raise HTTPException(status_code=502, detail="地端模型沒有回傳內容")

    return {
        "response": answer,            # 最終回答（地端模型產生）
        "law": law_text,               # 第一步：法規要求（雲端模型產生）
        "facts": facts_text,           # 第二步：公司現況（地端模型產生）
        "law_references": law_refs,
        "company_references": company_refs,
    }