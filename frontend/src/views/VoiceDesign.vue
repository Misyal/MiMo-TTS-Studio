<template>
  <div class="page-header">
    <h2>音色设计</h2>
    <p class="desc">通过自然语言描述生成全新音色，无需提供音频样本</p>
  </div>

  <el-row :gutter="20">
    <el-col :span="14">
      <el-card>
        <template #header>音色描述与文本</template>

        <el-form label-position="top">
          <el-form-item label="音色描述">
            <el-input
              v-model="form.voice_description"
              type="textarea"
              :rows="3"
              placeholder="请描述你想要的音色特征，例如：年轻女性，温柔治愈系，语速缓慢，像幼儿园老师一样亲切"
            />
          </el-form-item>

          <el-form-item label="描述模板">
            <div class="templates">
              <el-tag
                v-for="tpl in templates"
                :key="tpl"
                class="tpl-tag"
                @click="form.voice_description = tpl"
              >
                {{ tpl }}
              </el-tag>
            </div>
          </el-form-item>

          <el-form-item label="描述要素">
            <div class="templates">
              <el-tag
                v-for="dim in dimensions"
                :key="dim"
                type="info"
                class="tpl-tag"
                @click="appendDimension(dim)"
              >
                + {{ dim }}
              </el-tag>
            </div>
          </el-form-item>

          <el-form-item label="合成文本">
            <el-input
              v-model="form.text"
              type="textarea"
              :rows="4"
              placeholder="请输入希望用这个音色说出的内容"
              maxlength="2000"
              show-word-limit
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSynthesize"
            style="width: 100%"
          >
            {{ loading ? loadingText : '设计音色并合成' }}
          </el-button>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="10">
      <el-card>
        <template #header>输出</template>

        <div v-if="resultAudio">
          <el-descriptions :column="1" border size="small" style="margin-bottom: 12px">
            <el-descriptions-item label="音色描述">{{ form.voice_description }}</el-descriptions-item>
          </el-descriptions>
          <AudioPlayer :audio-src="resultAudio" ref="playerRef" />
          <div class="result-actions">
            <el-button @click="handleDownload">
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button @click="resultAudio = ''">
              <el-icon><RefreshRight /></el-icon> 重新合成
            </el-button>
          </div>
        </div>
        <el-empty v-else description="设计音色后将在此显示结果" />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import axios from "axios";
import AudioPlayer from "../components/AudioPlayer.vue";

const loading = ref(false);
const loadingText = ref("正在合成...");
const resultAudio = ref("");
const playerRef = ref(null);

const form = ref({
  voice_description: "",
  text: "",
  audio_format: "wav",
});

const templates = [
  "年轻女性，甜美可爱，语速适中",
  "中年男性，低沉磁性，语速缓慢，像纪录片旁白",
  "老年女性，慈祥温和，语速慢，带笑意",
  "少年，活泼开朗，语速快，充满活力",
];

const dimensions = ["男性", "女性", "年轻", "中年", "老年", "温柔", "磁性", "甜美", "活泼", "沉稳", "语速慢", "语速快", "治愈系", "播音腔"];

function appendDimension(dim) {
  if (form.value.voice_description) {
    form.value.voice_description += "，" + dim;
  } else {
    form.value.voice_description = dim;
  }
}

async function handleSynthesize() {
  if (!form.value.voice_description.trim()) {
    ElMessage.warning("请填写音色描述");
    return;
  }
  if (!form.value.text.trim()) {
    ElMessage.warning("请输入合成文本");
    return;
  }
  loading.value = true;
  loadingText.value = "正在合成...";
  const loadingStages = [
    { text: "正在分析音色描述...", delay: 2000 },
    { text: "正在生成语音...", delay: 5000 },
    { text: "即将完成...", delay: 10000 },
  ];
  const timers = loadingStages.map((stage) =>
    setTimeout(() => { loadingText.value = stage.text; }, stage.delay)
  );

  try {
    const { data } = await axios.post("/api/voice-design", form.value);
    resultAudio.value = `data:audio/wav;base64,${data.audio_base64}`;
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
  a.download = `voice_design_${Date.now()}.wav`;
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
.templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tpl-tag {
  cursor: pointer;
}
.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
