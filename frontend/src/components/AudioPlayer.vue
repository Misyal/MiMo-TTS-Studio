<template>
  <div class="audio-player" v-if="audioSrc">
    <div class="player-row">
      <el-button circle :icon="isPlaying ? 'VideoPause' : 'VideoPlay'" @click="togglePlay" />
      <span class="time">{{ formatTime(currentTime) }}</span>
      <el-slider
        v-model="progress"
        :max="100"
        :show-tooltip="false"
        class="progress-slider"
        @input="onSeek"
      />
      <span class="time">{{ formatTime(duration) }}</span>
      <el-slider
        v-model="volume"
        :max="100"
        :show-tooltip="false"
        class="volume-slider"
        @input="onVolumeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from "vue";

const props = defineProps({
  audioSrc: { type: String, default: "" },
});

const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const progress = ref(0);
const volume = ref(80);

let audio = null;
let animFrame = null;

watch(() => props.audioSrc, (newSrc) => {
  cleanup();
  if (!newSrc) return;
  audio = new Audio(newSrc);
  audio.volume = volume.value / 100;
  audio.addEventListener("loadedmetadata", () => {
    duration.value = audio.duration;
  });
  audio.addEventListener("ended", () => {
    isPlaying.value = false;
    currentTime.value = 0;
    progress.value = 0;
  });
});

function togglePlay() {
  if (!audio) return;
  if (isPlaying.value) {
    audio.pause();
    isPlaying.value = false;
    cancelAnimationFrame(animFrame);
  } else {
    audio.play();
    isPlaying.value = true;
    updateProgress();
  }
}

function updateProgress() {
  if (!audio) return;
  currentTime.value = audio.currentTime;
  progress.value = duration.value ? (audio.currentTime / duration.value) * 100 : 0;
  if (isPlaying.value) {
    animFrame = requestAnimationFrame(updateProgress);
  }
}

function onSeek(val) {
  if (audio && duration.value) {
    audio.currentTime = (val / 100) * duration.value;
  }
}

function onVolumeChange(val) {
  if (audio) audio.volume = val / 100;
}

function formatTime(sec) {
  if (!sec || isNaN(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function cleanup() {
  if (audio) {
    audio.pause();
    audio.src = "";
    audio = null;
  }
  isPlaying.value = false;
  currentTime.value = 0;
  duration.value = 0;
  progress.value = 0;
  cancelAnimationFrame(animFrame);
}

onUnmounted(cleanup);

defineExpose({ cleanup });
</script>

<style scoped>
.audio-player {
  padding: 12px 0;
}

.player-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time {
  font-size: 12px;
  color: #666;
  min-width: 36px;
  text-align: center;
}

.progress-slider {
  flex: 1;
}

.volume-slider {
  width: 80px;
}
</style>
