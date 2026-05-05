import { defineStore } from "pinia";
import { ref, computed } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";

export const useAppStore = defineStore("app", () => {
  const apiKey = ref("");
  const theme = ref("light");
  const defaultVoice = ref("bingtang");
  const defaultFormat = ref("wav");
  const apiConnected = ref(false);
  const showApiKeyDialog = ref(false);

  const hasApiKey = computed(() => !!apiKey.value);

  // 安装全局 axios 拦截器（仅安装一次）
  let interceptorsInstalled = false;

  function installInterceptors() {
    if (interceptorsInstalled) return;
    interceptorsInstalled = true;

    // 响应拦截器：统一错误处理
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (!error.response) {
          // 网络错误
          ElMessage.error("网络连接失败，请检查网络设置");
          return Promise.reject(error);
        }

        const { status, data } = error.response;
        const detail = data?.detail || "";

        switch (status) {
          case 401:
            // API Key 未配置或无效
            showApiKeyDialog.value = true;
            ElMessage.warning(detail || "请先配置 API Key");
            break;
          case 404:
            ElMessage.error(detail || "请求的资源不存在");
            break;
          case 408:
          case 504:
            ElMessage.error(detail || "请求超时，请稍后重试");
            break;
          case 502:
            ElMessage.error(detail || "API 服务异常，请稍后重试");
            break;
          case 500:
            ElMessage.error(detail || "服务器错误，请稍后重试");
            break;
          default:
            if (detail) {
              ElMessage.error(detail);
            }
        }

        return Promise.reject(error);
      }
    );
  }

  async function loadSettings() {
    try {
      const { data } = await axios.get("/api/settings");
      apiKey.value = data.api_key || "";
      theme.value = data.theme || "light";
      defaultVoice.value = data.default_voice || "bingtang";
      defaultFormat.value = data.default_format || "wav";
    } catch {
      // 静默处理
    }
  }

  async function checkHealth() {
    try {
      const { data } = await axios.get("/api/health");
      apiConnected.value = data.status === "ok";
    } catch {
      apiConnected.value = false;
    }
  }

  async function saveApiKey(key) {
    try {
      await axios.put("/api/settings", { api_key: key });
      apiKey.value = key;
      showApiKeyDialog.value = false;
      ElMessage.success("API Key 已保存");
      return true;
    } catch {
      ElMessage.error("保存 API Key 失败");
      return false;
    }
  }

  return {
    apiKey,
    theme,
    defaultVoice,
    defaultFormat,
    apiConnected,
    showApiKeyDialog,
    hasApiKey,
    loadSettings,
    checkHealth,
    installInterceptors,
    saveApiKey,
  };
});
