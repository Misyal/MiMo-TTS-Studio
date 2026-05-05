<template>
  <div class="page-header">
    <h2>设置</h2>
    <p class="desc">管理 API Key、默认参数和应用偏好</p>
  </div>

  <el-card>
    <template #header>API 配置</template>
    <el-form label-width="120px">
      <el-form-item label="API Key">
        <el-input
          v-model="form.api_key"
          :type="showKey ? 'text' : 'password'"
          placeholder="请输入 MiMo TTS API Key"
          style="max-width: 480px"
        >
          <template #append>
            <el-button @click="showKey = !showKey">
              {{ showKey ? '隐藏' : '显示' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="validating" @click="handleValidate">验证</el-button>
        <span v-if="validateResult === true" class="result-ok">API Key 验证成功</span>
        <span v-if="validateResult === false" class="result-fail">验证失败，请检查 Key 是否正确</span>
      </el-form-item>
    </el-form>
  </el-card>

  <el-card style="margin-top: 16px">
    <template #header>默认参数</template>
    <el-form label-width="120px">
      <el-form-item label="默认音色">
        <el-select v-model="form.default_voice" style="width: 240px">
          <el-option
            v-for="v in voices"
            :key="v.id"
            :label="`${v.name} (${v.lang === 'zh' ? '中文' : '英文'})`"
            :value="v.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="输出格式">
        <el-radio-group v-model="form.default_format">
          <el-radio value="wav">WAV</el-radio>
          <el-radio value="pcm16">PCM16</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </el-card>

  <el-card style="margin-top: 16px">
    <template #header>界面偏好</template>
    <el-form label-width="120px">
      <el-form-item label="主题">
        <el-radio-group v-model="form.theme">
          <el-radio value="light">浅色</el-radio>
          <el-radio value="dark">深色</el-radio>
          <el-radio value="system">跟随系统</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </el-card>

  <el-card style="margin-top: 16px">
    <template #header>数据管理</template>
    <el-form label-width="120px">
      <el-form-item>
        <el-button @click="handleExport">导出历史记录</el-button>
        <el-button @click="handleImport">导入历史记录</el-button>
      </el-form-item>
    </el-form>
  </el-card>

  <div style="margin-top: 20px; text-align: right">
    <el-button type="primary" size="large" :loading="saving" @click="handleSave">保存设置</el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import axios from "axios";
import { useAppStore } from "../stores/app";

const store = useAppStore();

const showKey = ref(false);
const validating = ref(false);
const validateResult = ref(null);
const saving = ref(false);
const voices = ref([]);

const form = ref({
  api_key: "",
  default_voice: "bingtang",
  default_format: "wav",
  theme: "light",
});

async function loadSettings() {
  try {
    const { data } = await axios.get("/api/settings");
    form.value.api_key = data.api_key || "";
    form.value.default_voice = data.default_voice || "bingtang";
    form.value.default_format = data.default_format || "wav";
    form.value.theme = data.theme || "light";
  } catch {
    // 静默
  }
}

async function loadVoices() {
  try {
    const { data } = await axios.get("/api/voices");
    voices.value = data.voices;
  } catch {
    // 静默
  }
}

async function handleValidate() {
  if (!form.value.api_key) {
    ElMessage.warning("请先输入 API Key");
    return;
  }
  validating.value = true;
  validateResult.value = null;
  try {
    const { data } = await axios.post("/api/validate-key", { api_key: form.value.api_key });
    validateResult.value = data.valid;
  } catch {
    validateResult.value = false;
  } finally {
    validating.value = false;
  }
}

async function handleSave() {
  saving.value = true;
  try {
    await axios.put("/api/settings", form.value);
    // 同步到全局 store
    store.apiKey = form.value.api_key;
    store.theme = form.value.theme;
    store.defaultVoice = form.value.default_voice;
    store.defaultFormat = form.value.default_format;
    ElMessage.success("设置已保存");
  } catch {
    // 错误已被拦截器处理
  } finally {
    saving.value = false;
  }
}

function handleExport() {
  axios.get("/api/history", { params: { page: 1, size: 9999 } })
    .then(({ data }) => {
      const blob = new Blob([JSON.stringify(data.records, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mimo_tts_history_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      ElMessage.success("导出成功");
    })
    .catch(() => {
      ElMessage.error("导出失败");
    });
}

function handleImport() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        JSON.parse(ev.target.result);
        ElMessage.info("导入功能暂未实现，请等待后续版本");
      } catch {
        ElMessage.error("文件格式错误，请选择有效的 JSON 文件");
      }
    };
    reader.readAsText(file);
  };
  input.click();
}

onMounted(() => {
  loadSettings();
  loadVoices();
});
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 20px;
  margin-bottom: 4px;
}
.desc {
  color: #999;
  font-size: 14px;
}
.result-ok {
  margin-left: 12px;
  color: #67c23a;
  font-size: 14px;
}
.result-fail {
  margin-left: 12px;
  color: #f56c6c;
  font-size: 14px;
}
</style>
