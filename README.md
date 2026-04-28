# Feishu Image Bot

一个部署在飞书（Feishu/Lark）上的 AI 媒体生成机器人。

**v2.0 核心特性：通过本地 Hermes 调用各种生图工具**，不直接调用 OpenAI API，支持多模型切换。

## 功能特性

- **多工具调度**：通过 Hermes 自动选择 image_generate / 烈鸟 / Gemini / Nano Banana / 即梦 等工具
- **尺寸/比例解析**：支持 9:16、16:9、750x1200、PPT、淘宝详情页、小红书、抖音、竖版/横版/方图等
- **自定义尺寸后处理**：用 Pillow 将生成图片裁剪/缩放到目标尺寸
- **并发控制**：全局锁，防止同时多个任务导致 Hermes 冲突
- **消息去重**：防止飞书重复推送
- **视频占位**：v1.0 提示用户需要接入视频模型

## 项目结构

```
feishu-image-bot/
├── src/
│   ├── app.py              # Flask 主服务（飞书 webhook 入口）
│   ├── config.py           # 配置管理
│   ├── feishu_api.py       # 飞书 API 封装
│   ├── hermes_client.py    # Hermes CLI 调用客户端（核心）
│   ├── image_gen.py        # 图片生成适配器（调用 Hermes）
│   ├── video_gen.py        # 视频生成占位
│   └── utils.py            # 工具函数（尺寸解析、后处理、全局锁）
├── tests/
│   ├── test_utils.py       # 尺寸解析 + Pillow 后处理测试
│   └── test_hermes_client.py # IMAGE_PATH 解析测试
├── docs/
│   └── 飞书配置教程.md      # 飞书应用配置步骤
├── .env.example            # 配置模板
├── .gitignore
├── requirements.txt
├── README.md
└── run.py                  # 一键启动脚本
```

## 前置条件

本项目依赖 **Hermes Agent** 作为 AI 调用中枢。在部署前，请确保：

1. **已安装 Hermes Agent**（CLI 命令 `hermes` 可用）
   - Hermes 是本项目作者的 AI Agent 基础设施，负责调度各种生图/生视频工具
   - 如果你还没有 Hermes，需要先部署：[hermes-agent 部署指南](https://github.com/hermes-agent/hermes)
   - 或者你可以修改 `src/hermes_client.py`，将调用改为直接请求烈鸟/OpenAI API

2. **有可用的生图 API 密钥**（至少一种）
   - 烈鸟 API（Gemini / OpenAI 兼容端点）
   - 或 OpenAI API Key
   - 或即梦、Nano Banana 等其他支持的工具

3. **有公网可访问的服务器**（或内网穿透）
   - 飞书事件订阅需要回调到你的服务地址

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/fayeluyuan/feishu-image-bot.git
cd feishu-image-bot
```

### 2. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

`.env` 中需要填写的关键配置：

```env
# 飞书应用（在飞书开放平台创建应用后获取）
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Hermes 配置
HERMES_CMD=hermes                    # Hermes CLI 命令名
HERMES_TIMEOUT=300                   # 单次生成超时（秒）
DEFAULT_IMAGE_TOOL=image_generate    # 默认图片工具
DEFAULT_ASPECT_RATIO=portrait        # 默认比例
ENABLE_CUSTOM_SIZE_POSTPROCESS=true  # 启用自定义尺寸后处理
```

> **注意**：本项目不直接调用 OpenAI API，所有生图能力来自本地 Hermes 的 `image_generate` 或其他 skills。

### 4. 启动服务

```bash
python run.py
```

服务默认运行在 `http://0.0.0.0:5000`

### 5. 配置飞书事件订阅

1. 在飞书开放平台创建应用并开启机器人能力
2. 设置事件订阅 URL 为 `http://你的服务器IP:5000/webhook`
3. 订阅 `im.message.receive_v1` 事件
4. 发布应用到你的企业/团队

详细步骤见 [docs/飞书配置教程.md](docs/飞书配置教程.md)

## 使用方式

在飞书群聊或私聊中 @机器人：

```
@图片生成助手 生成一张 9:16 竖版的图：一只宇航员猫咪在月球上弹吉他
```

机器人会回复：
1. "正在生成图片（9:16），请稍候..."
2. 生成完成后发送图片预览
3. "已生成，模型/工具：image_generate，尺寸：9:16"

### 支持的尺寸/比例关键词

| 关键词 | 解析结果 |
|--------|---------|
| 9:16, 3:4, 2:3, 竖版, 小红书, 抖音, 视频号, 淘宝详情页, 电商长图 | portrait |
| 16:9, 21:9, 3:2, 4:3, 横版, PPT, banner, 头图, 封面 | landscape |
| 1:1, 方图, 正方形, 头像, 商品主图 | square |
| 750x1200, 1024x1536, 1536x1024 等 | custom + 目标尺寸 |

### 指定模型/工具

```
@图片生成助手 用即梦生成一张图：赛博朋克城市
@图片生成助手 用烈鸟 API 生成 1024x1536 的图：水彩风景
```

Hermes 会根据你的提示词自动调度到对应 skill。

### 视频请求

```
@图片生成助手 生成一段视频：橘猫在海边奔跑
```

机器人会回复：
> "当前 gpt-image-2-medium 是图片模型，不能直接生成视频。视频需要接入 Veo / 可灵 / Runway / Sora / Seedance 等视频模型。"

## 并发控制

项目使用全局锁防止同时多个生成任务：
- 如果当前有任务正在生成，新消息会回复："上一个生成任务还在跑，请稍后再发。"
- 适合个人/小团队使用，不需要复杂队列

## 测试

```bash
# 编译检查
python3 -m py_compile run.py src/*.py

# 运行测试
python3 tests/test_utils.py
python3 tests/test_hermes_client.py
```

## 生产环境部署

使用 Gunicorn：

```bash
gunicorn -w 2 -b 0.0.0.0:5000 "src.app:create_app()"
```

## 配置说明

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `FEISHU_APP_ID` | 飞书应用 ID | 是 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 是 |
| `HERMES_CMD` | Hermes CLI 命令名 | 否（默认 `hermes`） |
| `HERMES_TIMEOUT` | Hermes 执行超时（秒） | 否（默认 300） |
| `DEFAULT_IMAGE_TOOL` | 默认图片工具 | 否（默认 `image_generate`） |
| `DEFAULT_ASPECT_RATIO` | 默认比例 | 否（默认 `portrait`） |
| `ENABLE_CUSTOM_SIZE_POSTPROCESS` | 启用尺寸后处理 | 否（默认 `true`） |
| `PORT` | 服务端口 | 否（默认 5000） |

## License

MIT
