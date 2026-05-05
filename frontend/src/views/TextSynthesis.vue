<template>
  <div class="page-header">
    <h2>文本合成</h2>
    <p class="desc">使用预置音色进行语音合成，支持风格控制和唱歌模式</p>
  </div>

  <el-row :gutter="20">
    <el-col :span="14">
      <el-card>
        <template #header>输入配置</template>

        <el-form label-position="top">
          <el-form-item label="合成文本">
            <el-input
              v-model="form.text"
              type="textarea"
              :rows="6"
              placeholder="请输入要合成的文本内容..."
              maxlength="2000"
              show-word-limit
            />
            <div class="text-meta">
              <span>预估时长：{{ estimatedDuration }}</span>
              <el-button text size="small" @click="cleanText">清洗文本</el-button>
            </div>
          </el-form-item>

          <el-form-item label="选择音色">
            <el-select v-model="form.voice" style="width: 100%">
              <el-option
                v-for="v in voices"
                :key="v.id"
                :label="`${v.name} | ${v.lang === 'zh' ? '中文' : '英文'} | ${v.gender === 'female' ? '女性' : '男性'}`"
                :value="v.id"
              />
            </el-select>
            <div class="voice-info-row">
              <span v-if="selectedVoiceDesc" class="voice-desc">{{ selectedVoiceDesc }}</span>
              <el-button
                text
                size="small"
                type="primary"
                :loading="previewLoading"
                @click="handlePreview"
                class="preview-btn"
              >
                <el-icon><VideoPlay /></el-icon> 试听
              </el-button>
            </div>
          </el-form-item>

          <el-form-item label="风格控制">
            <div class="tag-section">
              <div class="tag-row">
                <span class="tag-label">情绪：</span>
                <el-check-tag
                  v-for="tag in emotionTags"
                  :key="tag"
                  :checked="form.style_tags.includes(tag)"
                  @change="toggleTag(tag)"
                  class="style-tag"
                >
                  {{ tag }}
                </el-check-tag>
              </div>
              <div class="tag-row">
                <span class="tag-label">方言：</span>
                <el-check-tag
                  v-for="tag in dialectTags"
                  :key="tag"
                  :checked="form.style_tags.includes(tag)"
                  @change="toggleTag(tag)"
                  class="style-tag"
                >
                  {{ tag }}
                </el-check-tag>
              </div>
              <div class="tag-row">
                <span class="tag-label">语速：</span>
                <el-check-tag
                  v-for="tag in speedTags"
                  :key="tag"
                  :checked="form.style_tags.includes(tag)"
                  @change="toggleTag(tag)"
                  class="style-tag"
                >
                  {{ tag }}
                </el-check-tag>
              </div>
            </div>
            <el-input
              v-model="form.custom_style"
              placeholder="自定义风格描述，如：像老朋友聊天一样轻松"
              style="margin-top: 8px"
            />
            <div v-if="tagPreview" class="tag-preview">标签预览：{{ tagPreview }}</div>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="form.singing">唱歌模式</el-checkbox>
            <span v-if="form.singing" class="singing-hint">建议使用中文歌词以获得最佳效果</span>
          </el-form-item>

          <el-form-item label="输出格式">
            <el-radio-group v-model="form.audio_format">
              <el-radio value="wav">WAV</el-radio>
              <el-radio value="pcm16">PCM16</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSynthesize"
            style="width: 100%"
          >
            {{ loading ? loadingText : '开始合成' }}
          </el-button>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="10">
      <el-card>
        <template #header>输出</template>

        <div v-if="resultAudio">
          <AudioPlayer :audio-src="resultAudio" ref="playerRef" />
          <div class="result-actions">
            <el-button @click="handleDownload">
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button @click="handleFavorite" :type="isFavorite ? 'warning' : 'default'">
              <el-icon><Star /></el-icon> {{ isFavorite ? '已收藏' : '收藏' }}
            </el-button>
            <el-button @click="handleReset">
              <el-icon><RefreshRight /></el-icon> 重新合成
            </el-button>
          </div>
        </div>
        <el-empty v-else description="合成后将在此显示结果" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import axios from "axios";
import AudioPlayer from "../components/AudioPlayer.vue";

const voices = ref([]);
const loading = ref(false);
const loadingText = ref("正在合成...");
const resultAudio = ref("");
const playerRef = ref(null);
const previewLoading = ref(false);
const lastRecordId = ref(null);
const isFavorite = ref(false);

const emotionTags = ["温柔", "兴奋", "悲伤", "愤怒", "低语"];
const dialectTags = ["东北话", "四川话", "河南话", "陕西话", "粤语"];
const speedTags = ["慢速", "快速"];

const form = ref({
  text: "",
  voice: "bingtang",
  style_tags: [],
  custom_style: "",
  singing: false,
  audio_format: "wav",
});

const selectedVoiceDesc = computed(() => {
  const v = voices.value.find((v) => v.id === form.value.voice);
  return v ? v.desc : "";
});

const tagPreview = computed(() => {
  if (!form.value.style_tags.length) return "";
  return `（${form.value.style_tags.join("，")}）`;
});

const estimatedDuration = computed(() => {
  const text = form.value.text;
  if (!text) return "0秒";
  const chars = text.length;
  const seconds = Math.ceil(chars / 4);
  return seconds > 60 ? `${Math.floor(seconds / 60)}分${seconds % 60}秒` : `${seconds}秒`;
});

function toggleTag(tag) {
  const idx = form.value.style_tags.indexOf(tag);
  if (idx >= 0) form.value.style_tags.splice(idx, 1);
  else form.value.style_tags.push(tag);
}

function cleanText() {
  form.value.text = form.value.text
    .replace(/<[^>]+>/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

async function handlePreview() {
  previewLoading.value = true;
  try {
    const resp = await fetch(`/api/voice-preview/${form.value.voice}`);
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new Error(data.detail || "试听失败");
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
    audio.addEventListener("ended", () => URL.revokeObjectURL(url));
  } catch (err) {
    ElMessage.error(err.message || "试听失败");
  } finally {
    previewLoading.value = false;
  }
}

async function handleSynthesize() {
  if (!form.value.text.trim()) {
    ElMessage.warning("请输入要合成的文本");
    return;
  }
  loading.value = true;
  loadingText.value = "正在合成...";
  const loadingStages = [
    { text: "正在分析文本情感...", delay: 2000 },
    { text: "正在生成语音波形...", delay: 5000 },
    { text: "即将完成...", delay: 10000 },
  ];
  const timers = loadingStages.map((stage) =>
    setTimeout(() => { loadingText.value = stage.text; }, stage.delay)
  );

  try {
    const { data } = await axios.post("/api/synthesize", form.value);
    resultAudio.value = `data:audio/wav;base64,${data.audio_base64}`;
    lastRecordId.value = data.audio_path ? null : null; // 需要后端返回 record id
    isFavorite.value = false;
    ElMessage.success("合成完成");
  } catch (err) {
    // 错误已被 axios 拦截器处理
  } finally {
    loading.value = false;
    timers.forEach(clearTimeout);
  }
}

async function handleFavorite() {
  // TODO: 需要后端返回 record ID 才能收藏
  ElMessage.info("收藏功能需要记录 ID 支持");
}

function handleDownload() {
  if (!resultAudio.value) return;
  const a = document.createElement("a");
  a.href = resultAudio.value;
  a.download = `tts_${Date.now()}.wav`;
  a.click();
}

function handleReset() {
  resultAudio.value = "";
  lastRecordId.value = null;
  isFavorite.value = false;
}

onMounted(async () => {
  try {
    const { data } = await axios.get("/api/voices");
    voices.value = data.voices;
  } catch {
    // 错误已被拦截器处理
  }
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
.text-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}
.voice-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}
.voice-desc {
  font-size: 12px;
  color: #999;
}
.preview-btn {
  font-size: 12px;
}
.tag-section {
  width: 100%;
}
.tag-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.tag-label {
  font-size: 13px;
  color: #666;
  min-width: 40px;
}
.style-tag {
  cursor: pointer;
}
.tag-preview {
  margin-top: 4px;
  font-size: 12px;
  color: #409eff;
}
.singing-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #e6a23c;
}
.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
