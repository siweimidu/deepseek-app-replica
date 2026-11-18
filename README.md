<div align="center">

# DeepSleep

尽可能复刻 DeepSeek 官方手机端（Android）交互与视觉体验的客户端

[![Release](https://img.shields.io/github/v/release/LiJiaHua1024/deepseek-app-replica?style=flat-square&color=2563eb&label=Release)](https://github.com/LiJiaHua1024/deepseek-app-replica/releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Android%2011%2B-3DDC84?style=flat-square&logo=android&logoColor=white)](https://github.com/LiJiaHua1024/deepseek-app-replica)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=flat-square)](LICENSE)

<br />

[**📥 前往 Releases 下载 APK 安装包**](https://github.com/LiJiaHua1024/deepseek-app-replica/releases/latest) · [**反馈问题**](https://github.com/LiJiaHua1024/deepseek-app-replica/issues)

</div>

---

与官方客户端的区别在于未接入官方账号体系，改为直接输入用户自己的 DeepSeek 开放平台 API Key。官方 App 通过账号登录受限于日常用量配额，而直接接入个人 API Key 采用按量计费（Pay-as-you-go），只要账户额度充裕即可自由使用不受限额打断；同时所有会话数据均保存在设备本地。

## 下载与安装

请前往 [GitHub Releases](https://github.com/LiJiaHua1024/deepseek-app-replica/releases) 页面获取最新发布的 APK 文件，安装至 Android 设备即可使用。

> 当前源码构建的 APK 支持 Android 11（API 级别 30）及以上版本。已在 Android 11 模拟器的预装 WebView 83 上验证。

## 使用步骤

1. 安装并打开应用，点击左上角抽屉菜单进入「设置」。
2. 在 API 配置中填入你在 DeepSeek 开放平台申请的 API Key。
3. 返回主页面即可开始对话，支持深度思考、联网搜索、语音对讲与相册多模态等功能。

## 导入历史对话

数据管理里提供两个入口，效果完全一致，区别只是 ZIP 的来源：

- **选择导出文件（.zip）**：从系统文件选择器挑一个 DeepSeek 导出的压缩包。
- **从链接导入**：直接粘贴 DeepSeek 官网给出的下载链接，App 自己下载、解压并导入，不用再去文件夹里找 ZIP。

导入行为：

- 进度显示在页面顶部的状态条与「导入进度」卡片里；离开数据管理页后任务继续在后台跑，进度条跟随。
- 已经导入过的对话再次导入时按会话 ID 合并：用导出包里的标题、创建时间、更新时间与消息补齐，**不会新建、不会重复**，只会显示「新增 0 个，更新 N 个」。
- 会话长按 → 「详情」可以看到来源、创建时间（导入时取导出包里的原始时间）、最后更新、消息数与会话 ID。

---

## 技术架构

项目采用 Android 原生容器承载高性能 Web 交互内核的架构：

- **Android 原生层**：基于 Java 17 与 Android SDK 36（最低兼容 Android 11 / API 30）。通过 WebView 加载本地构建产物，并封装系统级能力：API Key 经 Android Keystore 加密存储、原生麦克风录音采集（`AudioRecord`）、系统相册快速预取、导出包后台下载（`__download` 同源分发，带 Range 支持）以及独立的网页浏览器（`SourceBrowserActivity`）。
- **Web 交互层**：React 18 + TypeScript + Zustand 状态管理，基于 CSS Modules 进行交互细节调优，引入 KaTeX、Mermaid 与 Prism.js 提供排版渲染。
- **构建系统**：Rspack 2 高速打包，与 Gradle `buildWeb` 构建任务无缝联动。

## 源码构建

如果你希望自行从源码编译 APK：

### 环境要求
- Node.js 22.12+ 与 pnpm
- JDK 17+
- Android SDK Platform 36

### 构建步骤
```powershell
# 1. 克隆代码并安装前端依赖
git clone https://github.com/siweimidu/deepseek-app-replica.git
cd deepseek-app-replica
pnpm install

# 2. 编译生成 Android Debug APK（会自动触发前端构建打包）
.\android\gradlew.bat -p android :app:assembleDebug
```

编译输出路径：`android/app/build/outputs/apk/debug/app-debug.apk`

---

## 项目结构

```text
├── android/            # Android 原生容器源码与 Gradle 工程
│   └── app/src/main/   # 原生代码（Keystore 存储、录音机、相册、沙箱浏览器）
├── src/
│   ├── app/            # 应用整体布局、主题体系与 Android 平台适配
│   ├── components/     # UI 组件库（聊天流、输入框、搜索抽屉、设置面板等）
│   ├── services/       # 业务逻辑（API 请求、流式解析、会话存储与备份）
│   ├── i18n/           # 多语言文案（中/英）
│   └── utils/          # 通用工具函数
├── rspack.config.ts    # Rspack 打包配置
└── package.json        # 项目配置与脚本入口
```

---

## 免责声明

本项目仅供个人技术研究与前端/移动端交互学习交流使用，非 DeepSeek 官方发布版本。项目内所有商标、标识及版权均归其各自所有者所有。

## 开源协议

本项目采用 [GPL-3.0 许可证](LICENSE)。部分基础代码源自 DeepSeek 官方开源的 [chat-demo](https://github.com/deepseek-ai/chat-demo)（基于 MIT 许可证），依其条款保留原作者版权声明。
