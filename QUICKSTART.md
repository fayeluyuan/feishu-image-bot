# QUICKSTART：10 分钟本地跑通

目标读者：有一点命令行基础，但不熟悉飞书开放平台部署的人。

---

## 前置准备

- Python 3.10+ / 3.11+ / 3.12 可用
- 一个飞书企业自建应用（后面会教你创建）
- 一个烈鸟 API Key，至少填以下之一：
  - `LIENIAO_GEMINI_API_KEY` 或
  - `LIENIAO_IMAGE2_API_KEY`
- [ngrok](https://ngrok.com/) 或其他内网穿透工具

---

## 1. 本地启动

```bash
git clone https://github.com/fayeluyuan/feishu-image-bot.git
cd feishu-image-bot
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的配置。

---

## 2. 最小 `.env`

### 方案 A：默认走 image2（gpt-image-2）

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=your_secret
LIENIAO_IMAGE2_API_KEY=your_lieniao_image2_key
LIENIAO_DEFAULT_BACKEND=image2
PORT=5000
```

### 方案 B：默认走 Gemini

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=your_secret
LIENIAO_GEMINI_API_KEY=your_lieniao_gemini_key
LIENIAO_DEFAULT_BACKEND=gemini
PORT=5000
```

> 不要把 `.env` 提交到 Git。

---

## 3. 启动服务

```bash
python run.py
```

健康检查：

```bash
curl http://127.0.0.1:5000/health
```

应返回：

```json
{"status":"ok"}
```

---

## 4. ngrok 内网穿透

```bash
ngrok http 5000
```

把 ngrok 提供的 HTTPS 地址加 `/webhook` 填入飞书事件订阅：

```text
https://xxxx.ngrok-free.app/webhook
```

> 注意：ngrok 免费版的域名每次重启会变，所以只适合本地测试。长期使用请部署到云服务器。

---

## 5. 飞书配置关键项

完整步骤见 [docs/飞书配置教程.md](docs/飞书配置教程.md)。这里只列最短必要步骤：

1. 在[飞书开放平台](https://open.feishu.cn/app)创建**企业自建应用**
2. **开启机器人能力**：应用详情页 → 机器人 → 启用机器人
3. **添加消息接收事件**：事件与回调 → 事件订阅 → 添加 `im.message.receive_v1`
4. **申请权限**（需要管理员审批）：
   - `im:message` — 收发消息
   - `im:message.group_msg` — 发送群消息
   - `im:message:send_as_bot` — 以机器人身份发送消息
5. **发布应用**或在测试企业中启用
6. **把机器人拉进群聊**，群里 @机器人发消息测试

---

## 6. 参考图测试（图生图）

1. 先发送一张参考图到群里。
2. 机器人回复"收到参考图"。
3. 再发：

```text
@机器人 调用 gpt image 2 生成，按这张图改成白色极简风
```

如果提示词包含 `gpt image 2` / `image2` / `gpt-image-2`，带参考图时会尝试走 image2 edits 端点。

## 7. 测试消息

```text
@机器人 用 gpt-image-2 生成一张 1:1 白色极简风商品图：一瓶高端护肤精华，干净背景，商业摄影
```

或：

```text
@机器人 生成一张 9:16 小红书风格穿搭图：夏日清爽连衣裙
```

---

## 下一步

本地测试通过后，参考 [DEPLOY.md](DEPLOY.md) 部署到云服务器长期运行。
