<template>
  <div class="page-header">
    <h2>音色克隆</h2>
    <p class="desc">上传一段音频样本，克隆该声音来说出任意文本</p>
  </div>

  <el-row :gutter="20">
    <el-col :span="14">
      <el-card>
        <template #header>音频样本与文本</template>

        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          accept=".mp3,.wav"
          :on-change="handleFileChange"
          v-if="!audioFile"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">将文件拖到此处，或<em>点击选择</em></div>
          <div class="upload-hint">支持 mp3、wav 格式，Base64 后不超过 10MB</div>
        </el-upload>

        <div v-else class="file-info">
          <div class="file-meta">
            <el-icon><Document /></el-icon>
            <span class="file-name">{{ audioFile.name }}</span>
            <span class="file-size">{{ fileSize }}</span>
          </div>
          <div class="file-actions">
            <el-button size="small" @click="playOriginal">试听</el-button>
            <el-button size="small" type="danger" @click="removeFile">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
          <el-alert
            v-if="fileChanged"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 8px"
          >
            更换音频样本将开启新的克隆会话
          </el-alert>
        </div>

        <el-form label-position="top" style="margin-top: 16px">
          <el-form-item label="合成文本">
            <el-input
              v-model="form.text"
              type="textarea"
              :rows="4"
              placeholder="请输入希望用克隆声音说出的内容"
              maxlength="2000"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="风格控制">
            <div class="tag-row">
              <el-check-tag
                v-for="tag in styleTags"
                :key="tag"
                :checked="form.style_tags.includes(tag)"
                @change="toggleTag(tag)"
                class="style-tag"
              >
                {{ tag }}
              </el-check-tag>
            </div>
            <el-input
              v-model="form.custom_style"
              placeholder="自定义风格描述"
              style="margin-top: 8px"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!audioFile"
            @click="handleSynthesize"
            style="width: 100%"
          >
            {{ loading ? loadingText : '克隆音色并合成' }}
          </el-button>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="10">
      <el-card>
        <template #header>对比播放</template>

        <div v-if="resultAudio">
          <div class="compare-section">
            <h4>原声音频</h4>
            <AudioPlayer :audio-src="originalAudioUrl" />
          </div>
          <el-divider />
          <div class="compare-section">
            <h4>克隆结果</h4>
            <AudioPlayer :audio-src="resultAudio" ref="playerRef" />
          </div>
          <div class="result-actions">
            <el-button @click="handleDownload">
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button @click="resultAudio = ''">
              <el-icon><RefreshRight /></el-icon> 重新合成
            </el-button>
          </div>
        </div>
        <el-empty v-else description="上传音频并合成后将在此显示结果" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import axios from "axios";
import AudioPlayer from "../components/AudioPlayer.vue";

const loading = ref(false);
const loadingText = ref("正在合成...");
const audioFile = ref(null);
const audioBase64 = ref("");
const originalAudioUrl = ref("");
const resultAudio = ref("");
const playerRef = ref(null);
const fileChanged = ref(false);

const form = ref({
  text: "",
  style_tags: [],
  custom_style: "",
  audio_format: "wav",
});

const styleTags = ["温柔", "兴奋", "悲伤", "愤怒", "低语", "慢速", "快速"];

const fileSize = computed(() => {
  if (!audioFile.value) return "";
  const kb = audioFile.value.size / 1024;
  return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb.toFixed(1)} KB`;
});

function toggleTag(tag) {
  const idx = form.value.style_tags.indexOf(tag);
  if (idx >= 0) form.value.style_tags.splice(idx, 1);
  else form.value.style_tags.push(tag);
}

function handleFileChange(file) {
  const raw = file.raw;
  const validTypes = ["audio/mpeg", "audio/wav", "audio/x-wav"];
  const validExts = [".mp3", ".wav"];
  const ext = raw.name.substring(raw.name.lastIndexOf(".")).toLowerCase();

  if (!validTypes.includes(raw.type) && !validExts.includes(ext)) {
    ElMessage.error("仅支持 mp3 和 wav 格式");
    return;
  }

  const maxSize = 7.5 * 1024 * 1024;
  if (raw.size > maxSize) {
    ElMessage.error("文件过大，建议时长 10~30 秒");
    return;
  }

  if (audioFile.value) {
    fileChanged.value = true;
  }

  audioFile.value = raw;
  const reader = new FileReader();
  reader.onload = (e) => {
    const b64 = e.target.result.split(",")[1];
    audioBase64.value = b64;
    originalAudioUrl.value = e.target.result;
  };
  reader.readAsDataURL(raw);
}

function removeFile() {
  audioFile.value = null;
  audioBase64.value = "";
  originalAudioUrl.value = "";
  fileChanged.value = false;
}

function playOriginal() {
  if (originalAudioUrl.value) {
    const audio = new Audio(originalAudioUrl.value);
    audio.play();
  }
}

async function handleSynthesize() {
  if (!audioBase64.value) {
    ElMessage.warning("请先上传音频样本");
    return;
  }
  if (!form.value.text.trim()) {
    ElMessage.warning("请输入合成文本");
    return;
  }

  loading.value = true;
  loadingText.value = "正在合成...";
  const loadingStages = [
    { text: "正在分析音频样本...", delay: 2000 },
    { text: "正在克隆音色...", delay: 5000 },
    { text: "即将完成...", delay: 10000 },
  ];
  const timers = loadingStages.map((stage) =>
    setTimeout(() => { loadingText.value = stage.text; }, stage.delay)
  );

  try {
    const { data } = await axios.post("/api/voice-clone", {
      audio_base64: audioBase64.value,
      filename: audioFile.value.name,
      text: form.value.text,
      style_tags: form.value.style_tags,
      custom_style: form.value.custom_style,
      audio_format: form.value.audio_format,
    });
    resultAudio.value = `data:audio/wav;base64,${data.audio_base64}`;
    fileChanged.value = false;
    ElMessage.success("合成完成");
  } catch {
    // 错误已被 axios 拦截器处理
  } finally {
    loading.value = false;
    timers.forEach(clearTimeout);
  }
}

function handleDownload() {
  if (!resultAudio.value) return;
  const a = document.createElement("a");
  a.href = resultAudio.value;
  a.download = `voice_clone_${Date.now()}.wav`;
  a.click();
}
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
.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
}
.upload-text {
  margin-top: 8px;
  color: #606266;
}
.upload-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}
.file-info {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
}
.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.file-name {
  font-weight: 500;
}
.file-size {
  color: #999;
  font-size: 12px;
}
.file-actions {
  display: flex;
  gap: 8px;
}
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.style-tag {
  cursor: pointer;
}
.compare-section h4 {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}
.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
