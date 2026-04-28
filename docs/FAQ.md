# 常见问题 FAQ

## 1. 飞书 challenge 失败

排查步骤：

1. 服务是否已启动？`curl http://127.0.0.1:5000/health` 应返回 `{"status":"ok"}`
2. `/webhook` 路径是否可访问？
3. ngrok/公网 URL 是否带 `/webhook`？例如 `https://xxxx.ngrok-free.app/webhook`
4. 飞书事件订阅是否使用 HTTPS（本地 ngrok 会自动提供 HTTPS）
5. Flask 日志是否收到 challenge 请求？查看服务输出是否有 POST /webhook 的日志

---

## 2. 机器人收不到消息

排查步骤：

1. 是否订阅了 `im.message.receive_v1` 事件？
2. 机器人能力是否开启？（应用详情页 → 机器人 → 启用机器人）
3. 应用是否已发布/测试企业是否可用？
4. 机器人是否已加入群聊？
5. 群里是否 @了机器人？
6. 权限是否申请并审批？以下权限必须申请并通过管理员审批：
   - `im:message`
   - `im:message.group_msg`
   - `im:message:send_as_bot`

---

## 3. 图片生成成功但上传飞书失败

排查步骤：

1. 飞书图片上传接口需要 multipart 字段：`image_type=message`
2. 检查是否有图片上传/消息发送权限
3. 检查图片大小和格式（建议 PNG/JPG，不超过一定大小限制）
4. 检查 `tenant_access_token` 是否正常获取（查看日志中的 token 相关错误）

---

## 4. gpt-image-2 模型不可用

排查步骤：

1. `LIENIAO_IMAGE2_API_KEY` 是否已配置？
2. `LIENIAO_IMAGE2_MODEL` 是否为当前可用模型，例如 `gpt-image-2-all`
3. 如果返回"无可用渠道"，尝试切换模型或确认烈鸟分组余额/权限
4. 提示词里是否包含 `gpt-image-2` / `image2` / `openai` 触发关键词？
5. 是否设置了 `LIENIAO_DEFAULT_BACKEND=image2`？

### image2 图生图失败

- 图生图使用 `/v1/images/edits` 端点，需要烈鸟分组支持 edits 能力
- 如果 edits 端点返回 404 或 503，说明当前分组不支持图生图，可尝试换分组或改用 Gemini
- 带参考图时如果提示词明确写了 `gpt image 2` / `image2`，会优先尝试 image2 edits；不写则按默认后端走

---

## 5. 没有公网地址

解决方案：

- 本地测试用 ngrok / cpolar / frp 做内网穿透
- 长期运行建议部署到云服务器（阿里云、腾讯云、AWS 等）
- 飞书事件订阅必须能访问你的 `/webhook`，所以需要公网可访问的地址
