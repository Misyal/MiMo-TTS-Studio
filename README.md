# MiMo TTS Studio 开发日志

## 一、已完成内容

### 1. 项目目录结构

```
MiMo-TTS-Studio/
├── backend/                        # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口、CORS、路由挂载、日志配置、全局异常处理、前端静态文件挂载
│   ├── config.py                   # 配置管理（API地址、端口、数据库路径、默认参数、预览目录）
│   ├── database.py                 # SQLite 数据库初始化、读写、设置项存取
│   ├── models.py                   # Pydantic 请求/响应模型定义
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── synthesize.py           # 合成接口：文本合成、音色设计、音色克隆、Key验证（含 API Key 检查、细分错误处理）
│   │   ├── voices.py               # 音色接口：预置音色列表、试听（调用 API 生成并缓存）
│   │   ├── history.py              # 历史记录接口：列表、详情、删除、清空、收藏
│   │   └── settings.py             # 设置接口：获取、更新
│   └── services/
│       ├── __init__.py
│       ├── tts_client.py           # MiMo API 调用封装（三种模型）、Key验证、API 响应自动适配
│       └── audio_processor.py      # 音频处理：PCM16转WAV、Base64解码、自动检测 WAV 头
├── frontend/                       # Vue 3 前端
│   ├── .gitignore
│   ├── index.html                  # HTML 入口
│   ├── package.json                # 依赖声明（Vue3、Router、Pinia、ElementPlus、Axios）
│   ├── vite.config.js              # Vite 配置（代理 /api → 18700端口）
│   └── src/
│       ├── main.js                 # Vue 应用初始化（注册插件、图标）
│       ├── App.vue                 # 根组件（引入布局、中文国际化）
│       ├── router/index.js         # 路由配置（5个页面）
│       ├── stores/app.js           # Pinia 全局状态（API Key、主题、连接状态、axios 拦截器、API Key 弹窗控制）
│       ├── components/
│       │   ├── AppLayout.vue       # 整体布局：左侧导航栏 + 右侧内容区 + 连接状态 + API Key 配置引导弹窗
│       │   └── AudioPlayer.vue     # 音频播放器组件（播放/暂停、进度条、音量）
│       └── views/
│           ├── TextSynthesis.vue   # 文本合成页面（音色选择、试听、风格标签、唱歌模式、分阶段加载、收藏）
│           ├── VoiceDesign.vue     # 音色设计页面（描述输入、模板、要素标签云、合成）
│           ├── VoiceClone.vue      # 音色克隆页面（文件上传、文件更换提示、对比播放）
│           ├── History.vue         # 历史记录页面（搜索防抖、筛选、分页、收藏、删除）
│           └── Settings.vue        # 设置页面（API Key、默认参数、主题、数据导出）
├── desktop/
│   └── main.py                     # PyWebView 桌面壳（端口探测、服务启动、窗口创建）
├── data/                           # 运行时数据目录
│   ├── audio/                      # 合成音频文件存储
│   ├── preview/                    # 音色试听音频缓存
│   └── logs/                       # 应用日志（app.log、backend.log）
├── start.py                        # 一键启动脚本（依赖检查、npm 自动探测、进程管理）
├── start.bat                       # Windows 启动入口（调用 start.py）
├── start-prod.bat                  # 生产模式启动入口
├── diagnose.py                     # 环境诊断工具
├── diagnose.bat                    # 诊断入口
├── .gitignore                      # Git 忽略规则
├── requirements.txt                # Python 依赖清单
├── run.py                          # 开发入口（uvicorn 热重载启动）
├── TTS计划书.md                     # 原始需求计划书
├── TTS-V2.md                       # 优化版计划书
└── 开发日志.md                      # 本文件
```

### 2. 后端已完成

| 模块 | 文件 | 实现内容 |
|------|------|----------|
| 应用入口 | `backend/main.py` | FastAPI 实例、CORS 中间件、路由挂载、音频静态文件挂载（`/api/audio`）、日志系统（控制台+文件）、全局异常处理中间件、生产模式前端静态文件挂载 |
| 配置管理 | `backend/config.py` | Pydantic Settings，支持 .env 文件，自动创建 data/audio、data/preview、data/logs 目录 |
| 数据库 | `backend/database.py` | SQLite 建表（history、settings）、异步读写、设置项存取 |
| 数据模型 | `backend/models.py` | 6个请求模型：SynthesizeRequest、VoiceDesignRequest、VoiceCloneRequest、ValidateKeyRequest、HistoryRecord、SettingsUpdate |
| 合成路由 | `backend/routers/synthesize.py` | POST /api/synthesize、/api/voice-design、/api/voice-clone、/api/validate-key；API Key 未配置时返回 401；httpx 超时/HTTPStatusError 细分处理；自动保存音频文件、写入历史记录 |
| 音色路由 | `backend/routers/voices.py` | GET /api/voices（返回8种预置音色）、GET /api/voice-preview/{id}（调用 API 生成试听音频并缓存到 data/preview/） |
| 历史路由 | `backend/routers/history.py` | GET /api/history（分页+搜索+筛选）、GET/DELETE /api/history/{id}、DELETE /api/history（清空）、PUT 收藏切换 |
| 设置路由 | `backend/routers/settings.py` | GET/PUT /api/settings |
| API客户端 | `backend/services/tts_client.py` | 封装三种模型的调用方法（支持 api_key 参数化）、消息构造逻辑、风格标签注入、Key验证；自动适配 API 响应中 audio 字段的 dict/str/list 格式 |
| 音频处理 | `backend/services/audio_processor.py` | Base64 解码、自动检测 RIFF 头（已是 WAV 则直接返回，裸 PCM16 则添加 WAV 头） |

### 3. 前端已完成

| 模块 | 文件 | 实现内容 |
|------|------|----------|
| 入口 | `main.js` | Vue3 + Pinia + Router + ElementPlus + 图标全局注册 |
| 布局 | `AppLayout.vue` | 侧边栏导航（5个菜单项）、API 连接状态指示灯、API Key 配置引导弹窗（含验证功能） |
| 播放器 | `AudioPlayer.vue` | 播放/暂停、进度条拖拽、音量控制、时间显示 |
| 文本合成 | `TextSynthesis.vue` | 文本输入（字数统计、时长预估、清洗）、音色下拉、试听按钮、风格标签多选、自定义风格、唱歌模式、输出格式、分阶段加载提示、合成+下载+收藏 |
| 音色设计 | `VoiceDesign.vue` | 音色描述输入、4个模板标签、描述要素标签云（14个维度）、合成文本、分阶段加载提示、结果展示 |
| 音色克隆 | `VoiceClone.vue` | 拖拽/点击上传、文件校验（格式+大小）、试听原声、文件更换提示、风格控制、分阶段加载提示、对比播放 |
| 历史记录 | `History.vue` | 搜索框（防抖）、类型筛选、分页表格、风格标签列、播放/下载/收藏/删除操作、清空确认 |
| 设置 | `Settings.vue` | API Key（显示/隐藏/验证）、默认音色、输出格式、主题切换、历史记录 JSON 导出、保存时同步全局状态 |
| 状态管理 | `stores/app.js` | 全局状态：apiKey、theme、apiConnected、showApiKeyDialog；全局 axios 响应拦截器（401 弹窗、404/502/500 统一错误提示、网络错误提示）；installInterceptors、saveApiKey 方法 |
| 路由 | `router/index.js` | 5条路由，懒加载 |

### 4. 桌面壳

| 文件 | 实现内容 |
|------|----------|
| `desktop/main.py` | PyWebView 窗口创建、端口自动探测（18700-18800）、后端服务就绪等待、daemon 线程启动 uvicorn |

### 5. 启动与运维工具

| 文件 | 实现内容 |
|------|----------|
| `start.py` | 一键启动脚本：Python/Node.js/npm 检测（npm 自动探测 PATH 及常见安装路径）、pip/前端依赖自动安装、数据目录创建、后端启动+健康检查、前端启动、Windows Job Object 进程绑定（窗口关闭自动杀后端）、atexit/signal 清理 |
| `start.bat` | Windows 启动入口，调用 start.py，窗口不会自动关闭 |
| `start-prod.bat` | 生产模式入口，构建前端后由后端托管 |
| `diagnose.py` | 环境诊断：Python/Node.js/npm 版本、pip 依赖、项目文件完整性、后端模块导入测试 |
| `diagnose.bat` | 诊断入口 |
| `run.py` | 开发入口，uvicorn 热重载模式启动后端 |
| `requirements.txt` | fastapi、uvicorn、httpx、pydantic、pydantic-settings、aiosqlite、pywebview |
| `.gitignore` | 排除缓存、密钥、构建产物、数据库、音频文件、试听缓存、日志 |
