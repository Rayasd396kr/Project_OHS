# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from app.services.rag_service import generate_rag_response

app = FastAPI(title="RAG AI Microservice", version="1.0.0")

class ChatRequest(BaseModel):
    query: str
    scenario: Optional[str] = "general"
    model: Optional[str] = "llama3"

class ChatResponse(BaseModel):
    query: str
    scenario: str
    context_length: int
    response: str

# 新增的資料模型
class ReferenceDoc(BaseModel):
    id: str
    name: str
    version: str
    pages: str

class ChatHistoryItem(BaseModel):
    id: int
    session_id: str
    channel_type: str
    user_query: str
    created_at: str

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "fastapi-rag-service"}

# --- 新增的歷史紀錄與參考資料 API ---
@app.get("/api/history", response_model=List[ChatHistoryItem])
def get_chat_history(keyword: Optional[str] = Query(None, description="搜尋關鍵字")):
    # 這裡未來可改為查詢 PostgreSQL 資料庫
    mock_history = [
        {"id": 1, "session_id": "s1", "channel_type": "建管合規規劃", "user_query": "請輸入建置合規規劃相關問題...", "created_at": "2026-10-28 10:00:00"},
        {"id": 2, "session_id": "s2", "channel_type": "SOP 合規檢查", "user_query": "高架作業安全防護規範檢查", "created_at": "2026-10-28 11:30:00"},
    ]
    
    if keyword:
        filtered = [item for item in mock_history if keyword in item["user_query"] or keyword in item["channel_type"]]
        return filtered
        
    return mock_history

@app.get("/api/references", response_model=List[ReferenceDoc])
def get_reference_documents():
    return [
        {"id": "1", "name": "職業安全衛生設施規則", "version": "2026 修訂版", "pages": "第 1-45 頁"},
        {"id": "2", "name": "高架作業勞工保護措施標準", "version": "v2.1", "pages": "第 3-8 頁"},
        {"id": "3", "name": "廠區新建工程安全規劃說明書", "version": "v1.0", "pages": "第 12-18 頁"},
        {"id": "4", "name": "局限空間作業 SOP 標準指引", "version": "2025 版", "pages": "第 5-10 頁"}
    ]

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        result = await generate_rag_response(
            query=req.query,
            scenario=req.scenario,
            model=req.model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)