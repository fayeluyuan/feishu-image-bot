# Legacy 文件说明

此目录存放历史遗留文件，主运行链路不再使用。

## hermes_client.py

旧版媒体生成客户端，曾用于直接调用烈鸟 API。
当前主链路已改为 `src/image_gen.py` → `src/providers/*`，直接通过 provider 调用 API。

保留此文件仅作历史参考，新项目不应依赖它。
