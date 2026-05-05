<template>
  <div class="page-header">
    <h2>历史记录</h2>
    <p class="desc">查看、播放、管理所有历史合成记录</p>
  </div>

  <el-card>
    <template #header>
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="search"
            placeholder="搜索文本内容..."
            clearable
            style="width: 240px"
            @input="debouncedFetch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="modelFilter" placeholder="模型类型" clearable style="width: 140px" @change="fetchHistory">
            <el-option label="全部" value="" />
            <el-option label="文本合成" value="preset" />
            <el-option label="音色设计" value="voice_design" />
            <el-option label="音色克隆" value="voice_clone" />
          </el-select>
        </div>
        <el-button type="danger" plain :disabled="!records.length" @click="handleClearAll">
          清空全部
        </el-button>
      </div>
    </template>

    <el-table :data="records" v-loading="loading" empty-text="还没有合成记录，去试试文本合成吧！">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="model_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="typeTagColor(row.model_type)" size="small">
            {{ typeLabel(row.model_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="voice_info" label="音色" width="120" show-overflow-tooltip />
      <el-table-column prop="style_tags" label="风格" width="120" show-overflow-tooltip />
      <el-table-column prop="text_content" label="文本内容" show-overflow-tooltip />
      <el-table-column prop="duration" label="时长" width="80">
        <template #default="{ row }">
          {{ row.duration ? `${row.duration.toFixed(1)}s` : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="playRecord(row)">播放</el-button>
          <el-button link type="primary" size="small" @click="downloadRecord(row)">下载</el-button>
          <el-button
            link
            :type="row.is_favorite ? 'warning' : 'info'"
            size="small"
            @click="toggleFavorite(row)"
          >
            {{ row.is_favorite ? '★ 已收藏' : '☆ 收藏' }}
          </el-button>
          <el-button link type="danger" size="small" @click="deleteRecord(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchHistory"
      />
    </div>
  </el-card>

  <!-- 播放弹窗 -->
  <el-dialog v-model="showPlayer" title="播放音频" width="480px">
    <AudioPlayer :audio-src="currentAudioUrl" />
    <template #footer>
      <el-button @click="showPlayer = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import axios from "axios";
import AudioPlayer from "../components/AudioPlayer.vue";

const records = ref([]);
const loading = ref(false);
const search = ref("");
const modelFilter = ref("");
const page = ref(1);
const pageSize = 20;
const total = ref(0);

const showPlayer = ref(false);
const currentAudioUrl = ref("");

let debounceTimer = null;

function debouncedFetch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    page.value = 1;
    fetchHistory();
  }, 300);
}

function typeLabel(type) {
  const map = { preset: "文本合成", voice_design: "音色设计", voice_clone: "音色克隆" };
  return map[type] || type;
}

function typeTagColor(type) {
  const map = { preset: "", voice_design: "success", voice_clone: "warning" };
  return map[type] || "info";
}

async function fetchHistory() {
  loading.value = true;
  try {
    const params = { page: page.value, size: pageSize };
    if (modelFilter.value) params.model_type = modelFilter.value;
    if (search.value) params.search = search.value;
    const { data } = await axios.get("/api/history", { params });
    records.value = data.records;
    total.value = data.total;
  } catch {
    // 错误已被拦截器处理
  } finally {
    loading.value = false;
  }
}

function playRecord(row) {
  currentAudioUrl.value = `/api/audio/${row.audio_path}`;
  showPlayer.value = true;
}

function downloadRecord(row) {
  const a = document.createElement("a");
  a.href = `/api/audio/${row.audio_path}`;
  a.download = `tts_${row.id}.${row.audio_format || "wav"}`;
  a.click();
}

async function toggleFavorite(row) {
  try {
    await axios.put(`/api/history/${row.id}/favorite`);
    row.is_favorite = !row.is_favorite;
  } catch {
    // 错误已被拦截器处理
  }
}

async function deleteRecord(row) {
  try {
    await ElMessageBox.confirm("确定删除该记录？", "提示", { type: "warning" });
    await axios.delete(`/api/history/${row.id}`);
    ElMessage.success("已删除");
    fetchHistory();
  } catch {
    // 取消或失败
  }
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm("确定清空所有历史记录？此操作不可恢复。", "警告", { type: "warning" });
    await axios.delete("/api/history");
    ElMessage.success("已清空");
    fetchHistory();
  } catch {
    // 取消或失败
  }
}

onMounted(fetchHistory);
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
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toolbar-left {
  display: flex;
  gap: 12px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
