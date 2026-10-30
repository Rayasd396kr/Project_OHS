<template>
  <aside class="history-sidebar" :class="{ 'is-open': isOpen }">
    <!-- 頂部標題與關閉按鈕 -->
    <div class="sidebar-header">
      <div class="title-group">
        <svg class="icon" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6a7 7 0 1 1 7 7 7 7 0 0 1-4.93-2.03l-1.42 1.42A9 9 0 1013 3m-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8Z"/></svg>
        <span>歷史紀錄</span>
      </div>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>

    <!-- 關鍵字搜尋框 -->
    <div class="search-box">
      <label>搜尋歷史諮詢</label>
      <div class="input-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.516 6.516 0 0 1 9.5 16C5.91 16 3 13.09 3 9.5S5.91 3 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5Z"/></svg>
        <input 
          type="text" 
          v-model="searchKeyword" 
          @input="handleSearch" 
          placeholder="輸入關鍵字搜尋紀錄..." 
        />
      </div>
    </div>

    <!-- 歷史紀錄列表 -->
    <div class="history-list">
      <div 
        v-for="item in filteredHistory" 
        :key="item.id" 
        class="history-item"
        @click="selectSession(item.session_id)"
      >
        <span class="channel-tag">[{{ item.channel_type }}]</span>
        <p class="query-text">{{ item.user_query }}</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close', 'select-session'])

const searchKeyword = ref('')
const filteredHistory = ref([
  // 測試假資料，之後可改接後端 API
  { id: 1, session_id: 's1', channel_type: '建管合規規劃', user_query: '請輸入建置合規規劃相關問題...' },
  { id: 2, session_id: 's2', channel_type: 'SOP 合規檢查', user_query: '高架作業安全防護規範檢查...' }
])

const handleSearch = () => {
  // 串接關鍵字過濾或後端搜尋
}

const selectSession = (sessionId) => {
  emit('select-session', sessionId)
}
</script>

<style scoped>
.history-sidebar {
  width: 280px;
  background: #f8f9fa;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
  padding: 16px;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}
.close-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6b7280;
}
.search-box {
  margin-bottom: 12px;
}
.search-box label {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}
.input-wrapper {
  position: relative;
  margin-top: 4px;
}
.search-box input {
  width: 100%;
  padding: 8px 10px 8px 30px;
  background: #374151;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  box-sizing: border-box;
}
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}
.history-list {
  flex: 1;
  overflow-y: auto;
}
.history-item {
  background: #ffffff;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  transition: background 0.2s;
}
.history-item:hover {
  background: #f3f4f6;
}
.channel-tag {
  font-size: 11px;
  color: #2563eb;
  font-weight: 600;
}
.query-text {
  font-size: 12px;
  color: #374151;
  margin: 4px 0 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>