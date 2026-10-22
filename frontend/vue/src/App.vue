<template>
  <div class="app-viewport">
    <!-- 1. 左側 slim 導覽列 -->
    <aside class="sidebar">
      <div class="brand-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      </div>

      <nav class="nav-menu">
        <button
          v-for="item in menuItems"
          :key="item.id"
          @click="toggleDrawer(item.id)"
          :class="['nav-item', { active: activeDrawer === item.id }]"
          :title="item.title"
        >
          {{ item.icon }}
        </button>
      </nav>
    </aside>

    <!-- 2. 抽屜區塊 -->
    <transition name="drawer">
      <section v-if="activeDrawer" class="drawer">
        <header class="drawer-header">
          <h3>{{ currentDrawerTitle }}</h3>
          <button @click="activeDrawer = null" class="close-btn">✕</button>
        </header>

        <div v-if="activeDrawer === 'search'" class="drawer-body">
          <div class="form-group">
            <label class="form-label">搜尋歷史諮詢</label>
            <input type="text" placeholder="輸入關鍵字搜尋紀錄..." class="form-input" />
          </div>
        </div>

        <div v-if="activeDrawer === 'modules'" class="drawer-body">
          <div class="form-group">
            <label class="form-label">標準模組庫</label>
            <p class="form-hint">包含內部 SOP 規範與各項職安標準文件。</p>
          </div>
        </div>

        <div v-if="activeDrawer === 'references'" class="drawer-body">
          <div class="form-group">
            <label class="form-label">已載入之參考資料庫 (Context)</label>
            <p class="form-hint">AI 僅能根據以下明確記載之文件進行回答。</p>
          </div>
          
          <div class="reference-list">
            <div v-for="(refDoc, rIdx) in referenceDocuments" :key="rIdx" class="reference-card">
              <div class="ref-title">
                <span class="ref-id">[{{ refDoc.id }}]</span> {{ refDoc.name }}
              </div>
              <div class="ref-meta">版本：{{ refDoc.version }} | 頁碼：{{ refDoc.pages }}</div>
            </div>
          </div>
        </div>
      </section>
    </transition>

    <!-- 3. 主要工作區 -->
    <main class="main-stage">
      <header class="top-nav">
        <div class="header-title">
          <h2>數位職安顧問</h2>
          <span class="sub-title">分流專業諮詢系統</span>
        </div>

        <div class="mode-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTabId = tab.id"
            :class="['tab-btn', { active: activeTabId === tab.id }]"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.title }}</span>
          </button>
        </div>
      </header>

      <div class="workspace">
        <div class="chat-wrapper">
          <!-- 動態載入當前頁籤對應的頻道元件 -->
          <component :is="currentTabComponent" />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import CompliancePanel from "./components/CompliancePanel.vue";
import SopCheckPanel from "./components/SopCheckPanel.vue";
import AccidentAnalysisPanel from "./components/AccidentAnalysisPanel.vue";
import PreCheckPanel from "./components/PreCheckPanel.vue";

const activeDrawer = ref(null);

const menuItems = [
  { id: "search", icon: "🔍", title: "歷史紀錄" },
  { id: "modules", icon: "📁", title: "標準模組" },
  { id: "references", icon: "📚", title: "參考資料" },
];

const referenceDocuments = ref([
  { id: "1", name: "職業安全衛生設施規則", version: "2026 修訂版", pages: "第 1-45 頁" },
  { id: "2", name: "高架作業勞工保護措施標準", version: "v2.1", pages: "第 3-8 頁" },
  { id: "3", name: "廠區新建工程安全規劃說明書", version: "v1.0", pages: "第 12-18 頁" },
  { id: "4", name: "局限空間作業 SOP 標準指引", version: "2025 版", pages: "第 5-10 頁" },
]);

const currentDrawerTitle = computed(() => {
  const item = menuItems.find((m) => m.id === activeDrawer.value);
  return item ? item.title : "";
});

/* 頁籤清單與對應的 Component */
const tabs = [
  { id: "compliance", icon: "🏗️", title: "建置合規規劃", component: CompliancePanel },
  { id: "sop", icon: "📋", title: "SOP 合規檢查", component: SopCheckPanel },
  { id: "accident", icon: "🔍", title: "事故原因分析", component: AccidentAnalysisPanel },
  { id: "precheck", icon: "✅", title: "作業前安全檢核", component: PreCheckPanel },
];

const activeTabId = ref("compliance");

const currentTabComponent = computed(() => {
  const current = tabs.find((t) => t.id === activeTabId.value);
  return current ? current.component : CompliancePanel;
});

const toggleDrawer = (id) => {
  activeDrawer.value = activeDrawer.value === id ? null : id;
};
</script>

<style scoped>
:global(html),
:global(body),
:global(#app) {
  width: 100vw !important;
  height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  background-color: #f8fafc !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #0f172a;
}

.app-viewport {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  background-color: #f8fafc;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 52px;
  height: 100vh;
  background-color: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  z-index: 20;
  box-sizing: border-box;
}
.brand-icon { color: #2563eb; margin-bottom: 20px; }
.nav-menu { display: flex; flex-direction: column; gap: 8px; width: 100%; align-items: center; }
.nav-item {
  width: 36px; height: 36px; border-radius: 8px; border: none;
  background: transparent; color: #64748b; cursor: pointer; font-size: 15px;
  transition: all 0.15s ease;
}
.nav-item:hover { background: #f1f5f9; color: #0f172a; }
.nav-item.active { background: #eff6ff; color: #2563eb; }

/* Drawer */
.drawer {
  width: 300px; height: 100vh; background-color: #ffffff;
  border-right: 1px solid #e2e8f0; display: flex; flex-direction: column;
  padding: 18px; box-sizing: border-box; z-index: 10;
}
.drawer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-shrink: 0; }
.drawer-header h3 { font-size: 14px; font-weight: 700; margin: 0; color: #0f172a; }
.close-btn { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 12px; }
.drawer-body { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; text-align: left; }
.form-label { font-size: 12px; font-weight: 600; color: #0f172a; }
.form-hint { font-size: 11px; color: #64748b; margin: 0; line-height: 1.4; }
.reference-list { display: flex; flex-direction: column; gap: 10px; }
.reference-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; text-align: left; }
.ref-title { font-size: 12px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.ref-id { color: #2563eb; }
.ref-meta { font-size: 11px; color: #64748b; }

/* Main Stage */
.main-stage {
  flex: 1; height: 100vh; display: flex; flex-direction: column;
  background-color: #f8fafc; overflow: hidden;
}
.top-nav {
  height: 56px; border-bottom: 1px solid #e2e8f0; display: flex;
  justify-content: space-between; align-items: center; padding: 0 24px;
  background: #ffffff; flex-shrink: 0;
}
.header-title { display: flex; align-items: baseline; gap: 10px; }
.header-title h2 { font-size: 15px; font-weight: 700; margin: 0; color: #0f172a; }
.sub-title { font-size: 12px; color: #64748b; }

.mode-tabs { display: flex; gap: 6px; background: #f1f5f9; padding: 4px; border-radius: 10px; }
.tab-btn {
  display: flex; align-items: center; gap: 6px; border: none;
  background: transparent; padding: 6px 14px; border-radius: 7px;
  font-size: 12px; font-weight: 500; color: #64748b; cursor: pointer; transition: all 0.15s ease;
}
.tab-btn:hover { color: #0f172a; }
.tab-btn.active { background: #ffffff; color: #2563eb; font-weight: 600; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08); }

/* Workspace */
.workspace { flex: 1; height: calc(100vh - 56px); display: flex; flex-direction: column; overflow: hidden; }
.chat-wrapper {
  flex: 1; height: 100%; display: flex; flex-direction: column;
  max-width: 900px; width: 100%; margin: 0 auto; padding: 24px 20px 16px;
  box-sizing: border-box; overflow: hidden;
}
</style>