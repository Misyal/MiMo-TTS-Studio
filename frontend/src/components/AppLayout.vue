<template>
  <el-container class="app-container">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>MiMo TTS</h2>
        <span class="subtitle">Studio</span>
      </div>

      <el-menu
        :default-active="currentRoute"
        router
        class="nav-menu"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/synthesize">
          <el-icon><Microphone /></el-icon>
          <span>文本合成</span>
        </el-menu-item>
        <el-menu-item index="/voice-design">
          <el-icon><MagicStick /></el-icon>
          <span>音色设计</span>
        </el-menu-item>
        <el-menu-item index="/voice-clone">
          <el-icon><CopyDocument /></el-icon>
          <span>音色克隆</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>历史记录</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>

      <div class="status-bar">
        <span :class="['status-dot', store.apiConnected ? 'online' : 'offline']"></span>
        <span class="status-text">{{ store.apiConnected ? 'API 已连接' : 'API 未连接' }}</span>
      </div>
    </el-aside>

    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>

  <!-- API Key 配置引导弹窗 -->
  <el-dialog
    v-model="store.showApiKeyDialog"
    title="配置 API Key"
    width="480px"
    :close-on-click-modal="false"
    :show-close="true"
  >
    <div class="api-key-guide">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        未检测到有效的 API Key，请先配置才能使用语音合成功能。
      </el-alert>

      <p class="guide-text">
        请前往 <a href="https://api.xiaomimimo.com" target="_blank">MiMo 开放平台</a> 申请 API Key，然后在下方输入。
      </p>

      <el-input
        v-model="dialogApiKey"
        :type="showDialogKey ? 'text' : 'password'"
        placeholder="请输入 API Key"
        style="margin-top: 12px"
      >
        <template #append>
          <el-button @click="showDialogKey = !showDialogKey">
            {{ showDialogKey ? '隐藏' : '显示' }}
          </el-button>
        </template>
      </el-input>

      <div v-if="dialogValidateResult !== null" class="validate-result">
        <span v-if="dialogValidateResult === true" class="result-ok">API Key 验证成功</span>
        <span v-if="dialogValidateResult === false" class="result-fail">验证失败，请检查 Key 是否正确</span>
      </div>
    </div>

    <template #footer>
      <el-button @click="store.showApiKeyDialog = false">稍后配置</el-button>
      <el-button type="primary" :loading="dialogSaving" @click="handleDialogSave">
        保存并验证
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useAppStore } from "../stores/app";
import axios from "axios";

const route = useRoute();
const store = useAppStore();

const currentRoute = computed(() => route.path);

const dialogApiKey = ref("");
const showDialogKey = ref(false);
const dialogSaving = ref(false);
const dialogValidateResult = ref(null);

async function handleDialogSave() {
  if (!dialogApiKey.value.trim()) {
    dialogValidateResult.value = false;
    return;
  }

  dialogSaving.value = true;
  dialogValidateResult.value = null;

  try {
    // 先验证
    const { data } = await axios.post("/api/validate-key", { api_key: dialogApiKey.value.trim() });
    if (data.valid) {
      dialogValidateResult.value = true;
      await store.saveApiKey(dialogApiKey.value.trim());
      dialogApiKey.value = "";
    } else {
      dialogValidateResult.value = false;
    }
  } catch {
    dialogValidateResult.value = false;
  } finally {
    dialogSaving.value = false;
  }
}

onMounted(() => {
  store.installInterceptors();
  store.loadSettings();
  store.checkHealth();
});
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #1d1e1f;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logo {
  padding: 20px 16px 16px;
  text-align: center;
  border-bottom: 1px solid #2d2d2d;
}

.logo h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

.subtitle {
  color: #666;
  font-size: 12px;
}

.nav-menu {
  flex: 1;
  border-right: none;
}

.status-bar {
  padding: 12px 16px;
  border-top: 1px solid #2d2d2d;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background-color: #67c23a;
}

.status-dot.offline {
  background-color: #f56c6c;
}

.status-text {
  color: #999;
  font-size: 12px;
}

.main-content {
  background-color: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}

/* API Key 弹窗样式 */
.api-key-guide {
  padding: 8px 0;
}

.guide-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.guide-text a {
  color: #409eff;
  text-decoration: none;
}

.guide-text a:hover {
  text-decoration: underline;
}

.validate-result {
  margin-top: 8px;
  font-size: 13px;
}

.result-ok {
  color: #67c23a;
}

.result-fail {
  color: #f56c6c;
}
</style>
