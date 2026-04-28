# DEPLOY.md：云服务器部署

目标：让用户把服务部署到云服务器长期运行。

---

## 1. 推荐运行环境

- Ubuntu 22.04 / 24.04
- Python 3.10+
- 开放 5000 端口，或使用 Nginx 反代到 80/443
- 需要公网 IP 或域名
- 建议配置 HTTPS（可使用 Nginx + Let's Encrypt）

---

## 2. 拉代码和安装

```bash
git clone https://github.com/fayeluyuan/feishu-image-bot.git
cd feishu-image-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

然后编辑 `.env`，填入生产环境的配置。不要把 `.env` 提交到 Git。

---

## 3. 配置 `.env`

生产环境最小配置示例：

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=your_secret
LIENIAO_IMAGE2_API_KEY=your_lieniao_image2_key
LIENIAO_DEFAULT_BACKEND=image2
PORT=5000
LOG_LEVEL=INFO
```

---

## 4. Gunicorn 启动

安装 Gunicorn：

```bash
pip install gunicorn
```

手动启动（测试用）：

```bash
venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 "src.app:create_app()"
```

---

## 5. systemd 服务示例

创建服务文件：

```bash
sudo tee /etc/systemd/system/feishu-image-bot.service << 'EOF'
[Unit]
Description=Feishu Image Bot
After=network.target

[Service]
WorkingDirectory=/opt/feishu-image-bot
Environment="PATH=/opt/feishu-image-bot/venv/bin"
ExecStart=/opt/feishu-image-bot/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 "src.app:create_app()"
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF
```

> 注意：如果代码放在其他目录（如 `/home/ubuntu/feishu-image-bot`），请修改 `WorkingDirectory` 和 `ExecStart` 中的路径。

加载并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable feishu-image-bot
sudo systemctl start feishu-image-bot
sudo systemctl status feishu-image-bot
```

---

## 6. 日志查看

```bash
# 实时查看日志
sudo journalctl -u feishu-image-bot -f

# 查看最近 100 行
sudo journalctl -u feishu-image-bot -n 100
```

---

## 7. Nginx 反代（推荐）

如果你使用 Nginx 反代到 80/443 端口：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

然后飞书事件订阅填写：

```text
http://your-domain.com/webhook
```

建议配置 HTTPS（使用 Let's Encrypt / certbot）。

---

## 8. 安全提醒

- **不要公开 `.env`**：确保 `.gitignore` 中已排除 `.env`
- **生产建议用 HTTPS**：飞书事件订阅支持 HTTP，但生产环境强烈建议 HTTPS
- **云服务器安全组只开放必要端口**：如果只使用 Nginx 反代，安全组只需开放 80/443，不需要直接暴露 5000
- **不要在日志中打印敏感内容**：API key、app secret、飞书 message_id 等不应出现在日志中
