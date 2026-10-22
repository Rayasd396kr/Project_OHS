<template>
  <div class="channel-container">
    <div class="chat-feed" ref="chatFeedRef">
      <!-- 歡迎卡片 -->
      <div v-if="messages.length === 0 && !isLoading" class="welcome-card">
        <div class="welcome-icon-circle">🏗️</div>
        <div class="welcome-info">
          <h3>建置合規規劃 頻道</h3>
          <p>請在此輸入建置階段的規劃需求或欲比對之法規項目。</p>
        </div>
      </div>

      <!-- 對話訊息列表 -->
      <div v-for="(msg, idx) in messages" :key="idx" :class="['chat-item', msg.role]">
        <div class="author-tag">
          {{ msg.role === "user" ? "提問者" : "建置合規規劃 顧問" }}
        </div>

        <div v-if="msg.role === 'user'" class="bubble user-bubble">
          <div class="text-content">{{ msg.text }}</div>
        </div>

        <div v-else class="assistant-wrapper">
          <div v-if="isNotFound(msg.text)" class="not-found-card">
            <div class="alert-header">
              <span class="alert-icon">🚫</span>
              <strong class="alert-title">我無法回答你的問題</strong>
            </div>
            <p class="alert-sub">Context 檔案中無對應記載，系統已強制停止自動生成回答。</p>
          </div>

          <div v-else class="consultant-card">
            <div class="card-header">
              <div class="header-badge-group">
                <span class="channel-badge">數位職安顧問</span>
                <span class="topic-title">建置合規規劃 · 分析報告</span>
              </div>
            </div>

            <div class="native-card-body">
              <div v-for="(block, bIdx) in parseTextBlocks(msg.text)" :key="bIdx" class="content-block">
                <div v-if="block.type === 'item-card'" class="item-detail-card">
                  <div class="card-item-header">
                    <span class="blue-indicator"></span>
                    <span class="blue-tag">條款</span>
                    <span class="card-item-title">{{ block.title }}</span>
                  </div>
                  <div class="card-item-body">{{ block.body }}</div>
                </div>
                <div v-else-if="block.type === 'conclusion'" class="conclusion-box">
                  <div class="box-label">💡 結論</div>
                  <div class="box-content">{{ block.text }}</div>
                </div>
                <div v-else-if="block.type === 'reference'" class="reference-box">
                  <div class="box-label">📚 參考資料</div>
                  <div class="box-content">{{ block.text }}</div>
                </div>
                <p v-else class="normal-paragraph">{{ block.text }}</p>
              </div>
            </div>

            <div class="card-actions">
              <button @click="copyToClipboard(msg.text)" class="action-btn">📋 一鍵複製純文字</button>
              <button @click="exportOrPrint" class="action-btn">🖨️ 匯出報告 / 列印</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isLoading" class="loading-indicator">資料處理與比對中，請稍候...</div>
    </div>

    <!-- 輸入區域 -->
    <div class="chat-input-area">
      <div v-if="selectedFile" class="file-preview-tag">
        <span class="file-icon">📎</span>
        <span class="file-name" :title="selectedFile.name">{{ selectedFile.name }}</span>
        <button @click="removeSelectedFile" class="remove-file-btn">✕</button>
      </div>

      <div class="input-container">
        <input type="file" ref="fileInputRef" @change="handleFileSelect" style="display: none" accept=".txt,.pdf,.docx,.doc,.md,.csv,.xlsx,.xls,.json,.html" />
        <button @click="triggerFileInput" class="attach-btn" title="上傳檔案/文件">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <input ref="queryInputRef" type="text" v-model="userQuery" @keyup.enter="runQuery" placeholder="請輸入建置合規規劃相關問題..." />
        <button @click="runQuery" :disabled="isLoading" class="send-action">發送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const messages = ref([])
const userQuery = ref('')
const isLoading = ref(false)
const selectedFile = ref(null)
const chatFeedRef = ref(null)
const queryInputRef = ref(null)
const fileInputRef = ref(null)

const triggerFileInput = () => fileInputRef.value?.click()
const handleFileSelect = (e) => { if (e.target.files[0]) selectedFile.value = e.target.files[0] }
const removeSelectedFile = () => { selectedFile.value = null; if (fileInputRef.value) fileInputRef.value.value = '' }

const scrollToBottom = () => {
  nextTick(() => {
    if (chatFeedRef.value) chatFeedRef.value.scrollTop = chatFeedRef.value.scrollHeight
  })
}

const isNotFound = (text) => text && (text.includes("我無法回答你的問題") || text.includes("檔案內找不到對應資訊") || text.includes("已停止自動生成"))

const parseTextBlocks = (rawText) => {
  if (!rawText) return []
  const lines = rawText.split("\n").filter(l => l.trim() !== "")
  const blocks = []
  let currentCard = null

  lines.forEach((line) => {
    const trimmed = line.trim()
    if (trimmed.startsWith("結論：") || trimmed.startsWith("結論:")) {
      if (currentCard) { blocks.push(currentCard); currentCard = null }
      blocks.push({ type: "conclusion", text: trimmed.replace(/^結論[：:]\s*/, "") })
    } else if (trimmed.startsWith("參考資料：") || trimmed.startsWith("參考資料:")) {
      if (currentCard) { blocks.push(currentCard); currentCard = null }
      blocks.push({ type: "reference", text: trimmed.replace(/^參考資料[：:]\s*/, "") })
    } else if (/^(#{1,6}|第\d+[條条]|[\d]+\.|\*|\-)/.test(trimmed)) {
      if (currentCard) blocks.push(currentCard)
      currentCard = { type: "item-card", title: trimmed.replace(/^#{1,6}\s*/, "").replace(/[*_]/g, ""), body: "" }
    } else {
      if (currentCard) {
        currentCard.body += (currentCard.body ? "\n" : "") + trimmed.replace(/[*_]/g, "")
      } else {
        blocks.push({ type: "paragraph", text: trimmed.replace(/[*_]/g, "") })
      }
    }
  })
  if (currentCard) blocks.push(currentCard)
  return blocks
}

const copyToClipboard = (text) => {
  if (!text) return
  navigator.clipboard.writeText(text.replace(/[#*_`]/g, ""))
  alert("📋 已複製純文字內容至剪貼簿！")
}

const exportOrPrint = () => window.print()

const runQuery = async () => {
  if ((!userQuery.value.trim() && !selectedFile.value) || isLoading.value) return
  const queryText = userQuery.value.trim()
  const attachedFile = selectedFile.value

  const userDisplayMsg = attachedFile ? `[已夾帶檔案：${attachedFile.name}]\n${queryText || "請協助分析此檔案。"}` : queryText
  messages.value.push({ role: "user", text: userDisplayMsg })

  userQuery.value = ""
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ""
  isLoading.value = true
  scrollToBottom()

  if (!attachedFile && (queryText.length < 3 || /^\d+$/.test(queryText) || /^[a-zA-Z]+$/.test(queryText))) {
    setTimeout(() => {
      isLoading.value = false
      messages.value.push({
        role: "assistant",
        text: `【建置合規規劃 - 輸入引導】\n您輸入的內容「${queryText}」資訊較少。\n\n請提供您預計建置的「場域類型或設備」（例如：高架作業區、化學品儲槽），我將為您整理對應的法定防護設施清單與合規要求。`
      })
      scrollToBottom()
    }, 400)
    return
  }

  try {
    const res = await fetch("http://localhost:8000/api/forward-to-lightrag", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText || (attachedFile ? `請分析檔案：${attachedFile.name}` : "請協助分析") })
    })
    const data = await res.json()
    messages.value.push({ role: "assistant", text: data.response || "我無法回答你的問題" })
  } catch (err) {
    messages.value.push({ role: "assistant", text: "⚠️ 系統連線異常，請確認 FastAPI 與 LightRAG 是否已發布啟動。" })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.channel-container { display: flex; flex-direction: column; height: 100%; width: 100%; }
.chat-feed { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 22px; padding-right: 6px; }
.welcome-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 28px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 12px; margin: auto; max-width: 480px; width: 100%; box-sizing: border-box; }
.welcome-icon-circle { width: 48px; height: 48px; background: #eff6ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.chat-item { display: flex; flex-direction: column; gap: 6px; text-align: left; }
.author-tag { font-size: 11px; font-weight: 600; color: #94a3b8; }
.chat-item.user .author-tag { color: #2563eb; text-align: right; }
.user-bubble { background: #0f172a; color: #fff; border-radius: 12px 12px 2px 12px; padding: 12px 18px; font-size: 13.5px; margin-left: auto; max-width: 80%; white-space: pre-wrap; }
.assistant-wrapper { width: 100%; }
.consultant-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9; }
.header-badge-group { display: flex; align-items: center; gap: 10px; }
.channel-badge { background: #2563eb; color: #fff; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
.topic-title { font-size: 13px; color: #475569; font-weight: 600; }
.native-card-body { display: flex; flex-direction: column; gap: 16px; }
.item-detail-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.card-item-header { display: flex; align-items: center; gap: 8px; }
.blue-indicator { width: 4px; height: 14px; background: #2563eb; border-radius: 2px; }
.blue-tag { background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.card-item-title { font-weight: 700; color: #0f172a; font-size: 14.5px; }
.card-item-body { font-size: 13.5px; line-height: 1.75; color: #334155; white-space: pre-wrap; padding-left: 12px; }
.normal-paragraph { font-size: 13.5px; line-height: 1.7; color: #475569; margin: 0; padding-left: 4px; }
.conclusion-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px 18px; margin-top: 10px; }
.conclusion-box .box-label { font-size: 12.5px; font-weight: 700; color: #166534; margin-bottom: 4px; }
.conclusion-box .box-content { font-size: 13px; color: #15803d; line-height: 1.6; }
.reference-box { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 14px 18px; margin-top: 6px; }
.reference-box .box-label { font-size: 12.5px; font-weight: 700; color: #075985; margin-bottom: 4px; }
.reference-box .box-content { font-size: 12px; color: #0369a1; line-height: 1.6; }
.card-actions { display: flex; gap: 10px; margin-top: 20px; padding-top: 14px; border-top: 1px dashed #e2e8f0; }
.action-btn { background: #fff; border: 1px solid #cbd5e1; color: #475569; border-radius: 7px; padding: 6px 14px; font-size: 11.5px; font-weight: 600; cursor: pointer; }
.not-found-card { background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 18px 20px; }
.alert-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.alert-title { font-size: 14px; font-weight: 700; color: #991b1b; }
.alert-sub { font-size: 12px; color: #b91c1c; margin: 0; }
.loading-indicator { font-size: 12px; color: #64748b; text-align: center; padding: 12px; }
.chat-input-area { padding-top: 12px; flex-shrink: 0; display: flex; flex-direction: column; gap: 8px; }
.file-preview-tag { display: flex; align-items: center; gap: 6px; background: #eff6ff; border: 1px solid #bfdbfe; padding: 4px 10px; border-radius: 6px; width: fit-content; font-size: 12px; color: #1e40af; }
.file-name { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.remove-file-btn { background: none; border: none; color: #3b82f6; cursor: pointer; font-size: 12px; }
.input-container { background: #fff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 8px 12px; display: flex; align-items: center; gap: 10px; }
.attach-btn { background: transparent; border: none; color: #64748b; display: flex; align-items: center; justify-content: center; padding: 6px; border-radius: 6px; cursor: pointer; }
.input-container input[type="text"] { flex: 1; background: transparent; border: none; outline: none; color: #0f172a; font-size: 13.5px; }
.send-action { background: #0f172a; color: #fff; border: none; padding: 8px 18px; border-radius: 8px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
</style>