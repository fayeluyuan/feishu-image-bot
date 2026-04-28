# Feishu Image Bot

Feishu Image Bot 是一个飞书图片生成机器人模板。用户在飞书群里 @机器人发送提示词，机器人会调用烈鸟 API / Gemini / gpt-image-2 生成图片，并自动回传到飞书。

当前版本默认通过 Python provider 直接调用 API，不要求安装 Hermes CLI。

## 功能特性

- 飞书 webhook 接收消息
- 支持文本生图
- 支持先发参考图，再发提示词做图生图/参考图生成
- 支持烈鸟 Gemini：`gemini-3-pro-image-preview`
- 支持烈鸟 image2：`gpt-image-2-all`
- 支持提示词触发 image2 / gpt-image-2
- 支持生成图上传回飞书
- 支持比例/尺寸解析（9:16、16:9、1:1、750x1200 等）
- 支持并发锁，适合个人/小团队

## 项目结构

```
feishu-image-bot/
├── src/
│   ├── app.py              # Flask 主服务（飞书 webhook 入口）
│   ├── config.py           # 配置管理
│   ├── feishu_api.py       # 飞书 API 封装
│   ├── image_gen.py        # 图片生成适配器（调用 provider）
│   ├── providers/          # 生图 provider 目录
│   │   ├── lieniao.py      # 烈鸟 API（Gemini + Image2）
│   │   ├── openai.py       # OpenAI 官方
│   │   ├── dashscope.py    # 阿里云百炼
│   │   └── registry.py     # provider 注册器
│   ├── video_gen.py        # 视频生成占位
│   └── utils.py            # 工具函数（尺寸解析、后处理、全局锁）
├── tests/                  # 测试目录
├── docs/
│   ├── 飞书配置教程.md      # 飞书应用配置步骤
│   └── FAQ.md              # 常见问题
├── .env.example            # 配置模板
├── .gitignore
├── requirements.txt
├── README.md
├── QUICKSTART.md           # 10 分钟本地跑通指南
├── DEPLOY.md               # 云服务器部署指南
└── run.py                  # 一键启动脚本
```

## 项目背景

本项目最初由 Faye 使用 Hermes/Claude 协助开发和调试，但当前运行时**不依赖 Hermes CLI**，直接通过 Python provider 调用图片生成 API。

## 前置条件

1. **飞书应用**：在[飞书开放平台](https://open.feishu.cn/app)创建企业自建应用，获取 App ID / App Secret
2. **至少一个图片生成 API Key**：支持烈鸟 Gemini / 烈鸟 image2（见下方支持列表）
3. **公网可访问地址**（或内网穿透）：飞书事件订阅需要回调到你的服务地址

## 支持的图片生成服务

| 服务 | 环境变量 | 说明 |
|------|---------|------|
| **烈鸟 Gemini** | `LIENIAO_GEMINI_API_KEY` | 推荐，支持文本生图 + 参考图 |
| **烈鸟 image2** | `LIENIAO_IMAGE2_API_KEY` | gpt-image-2 兼容端点，文本生图 |
| **OpenAI 官方** | `OPENAI_API_KEY` | DALL-E 3，质量好但价格较高 |
| **阿里云百炼** | `DASHSCOPE_API_KEY` | 通义万相，国内网络稳定 |
| **自定义** | 自己写插件 | 放在 `PROVIDERS_DIR` 目录，自动加载 |

> 可同时配置多个服务，一个失败时自动 fallback 到下一个。

## 快速开始

详细步骤见 [QUICKSTART.md](QUICKSTART.md)。简要流程：

```bash
git clone https://github.com/fayeluyuan/feishu-image-bot.git
cd feishu-image-bot
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入你的密钥
python run.py
```

## 使用方式

在飞书群聊或私聊中 @机器人：

### 文本生图

```
@图片生成助手 生成一张 9:16 竖版的图：一只宇航员猫咪在月球上弹吉他
```

机器人会回复：
1. "正在生成图片（9:16），请稍候..."
2. 生成完成后发送图片
3. "已生成，模型/工具：lieniao/gemini-3-pro-image-preview，尺寸：9:16"

### 支持的尺寸/比例关键词

| 关键词 | 解析结果 |
|--------|---------|
| 9:16, 3:4, 2:3, 竖版, 小红书, 抖音, 视频号, 淘宝详情页, 电商长图 | portrait |
| 16:9, 21:9, 3:2, 4:3, 横版, PPT, banner, 头图, 封面 | landscape |
| 1:1, 方图, 正方形, 头像, 商品主图 | square |
| 750x1200, 1024x1536, 1536x1024 等 | custom + 目标尺寸 |

### 如何触发 gpt-image-2 / image2

默认后端由 `LIENIAO_DEFAULT_BACKEND` 控制，默认是 `gemini`。

如果想在某条消息中临时使用 gpt-image-2，在提示词里加入以下任一关键词：

- image2
- image 2
- gpt-image-2
- gpt image 2
- openai

示例：

```
@机器人 用 gpt-image-2 生成一张 1:1 白色极简风商品图：...
@机器人 image2 生成一张 9:16 视频号封面：...
```

如果希望默认就走 image2，可在 `.env` 中设置：

```env
LIENIAO_DEFAULT_BACKEND=image2
```

### 参考图 / 图生图怎么用

1. 在飞书群里先发送一张图片给机器人。
2. 机器人回复：收到参考图。
3. 在有效期内发送文字提示词，例如：
   "按刚才那张图，改成白色极简风商品主图。"
4. 机器人会把最近一张参考图传给生成端点生成新图。

**路由规则**：
- 如果提示词包含 `image2` / `gpt image 2` / `gpt-image-2` 等关键词，带参考图会走 **image2 edits**（`/v1/images/edits`）端点。
- 如果不写，则按 `LIENIAO_DEFAULT_BACKEND` 配置走 Gemini 或 image2。
- image2 图生图依赖烈鸟 `/v1/images/edits` 端点和对应分组授权。

参考图缓存有效期由：

```env
REFERENCE_IMAGE_TTL_SECONDS=1800
```

控制。

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
python3 -m compileall -q src tests run.py

# 运行测试
for t in tests/test_*.py; do echo "--- $t ---"; python3 "$t" || exit 1; done
```

> 部分测试需要外部 API key 的集成测试放在 `tests/integration/`，默认不运行。

## 生产环境部署

详细步骤见 [DEPLOY.md](DEPLOY.md)。简要命令：

```bash
venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 "src.app:create_app()"
```

## 配置说明

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `FEISHU_APP_ID` | 飞书应用 ID | 是 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 是 |
| `LIENIAO_GEMINI_API_KEY` | 烈鸟 Gemini 端点密钥 | 否（至少填一个生图服务） |
| `LIENIAO_IMAGE2_API_KEY` | 烈鸟 Image2 (OpenAI兼容) 密钥 | 否 |
| `LIENIAO_DEFAULT_BACKEND` | 默认后端：`gemini` 或 `image2` | 否（默认 `gemini`） |
| `OPENAI_API_KEY` | OpenAI 官方 API 密钥 | 否 |
| `DASHSCOPE_API_KEY` | 阿里云百炼 API 密钥 | 否 |
| `PORT` | 服务端口 | 否（默认 5000） |
| `REFERENCE_IMAGE_TTL_SECONDS` | 参考图缓存有效期（秒） | 否（默认 1800） |

## 常见问题

见 [docs/FAQ.md](docs/FAQ.md)。

## License

MIT
