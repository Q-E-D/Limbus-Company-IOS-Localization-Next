# 开发交接记录

日期：2026-10-14。由最初的项目安全评估会话迁入本项目。

## 用户目标

使用已有 Shadowrocket 和本地 CA 在 iOS 上通过 MitM 汉化 Limbus Company；掌握模块、资源及更新发布，避免无条件追随第三方 latest。

## 已实现与验证

- Python 3 标准库离线工具 prepare_release.py 与 7 项 unittest。
- 输入 ZIP、manifest 须提供精确 SHA-256；解析 JSON、检查路径、解压规模、文件集合、文件大小及 LF 规范化 MD5。
- 可用已完成字库适配的 JSON 覆盖已有 JP 槽位，确定性重打包，更新清单 Hash/Size。
- 输出仅重定向游戏 CDN 语言 ZIP 和清单的 Shadowrocket 模块，目标为用户自有仓库固定 Release 标签。
- 使用 ghcruise v1.116.2-alpha 的 2,412 个 ZIP 文件完成全量哈希及重打包检查，7,182 个清单文件均为语言 JSON。
- 测试命令：python3 -m unittest -v test_prepare_release.py。

## 参考项目

- ghcruise/LimbusCompany-IOS-Localization：审查提交 839fa123c9992fa6d447c55ee55abf1ffe41ac24；普通版只有两条 302 + 游戏 CDN MitM。无节点直连版还覆写认证服务路由，不作为首选。
- TIMER-err/Limbus-Company-Mobile-Localization：参考提交 36671de080eca2567c4e5625c20943de207b6698；公开完整打包、字库与角色名处理实现。尚未完成全部构建脚本和 Actions 安全审查，未运行其代码。
- LocalizeLimbusCompany/LocalizeLimbusCompany：中文译文上游。

## 后续工作与边界

1. 审查完整参考构建实现；设计固定上游版本与人工批准的下载、构建、发布流程。
2. 补齐从官方日文底包及 LLC 译文独立生成资源的流程，字库覆盖、映射及剧情字段补全。
3. 验证当前游戏资源版本、iPhone 下载、缓存刷新及字形显示。
4. 再考虑 CI；未经用户要求不启用自动发布、定时同步或设备更新。

当前仅为离线原型，不保证字体兼容或译文语义安全；固定 Release 标签不是不可变附件，也不是设备端验签。本仓库没有资源附件、证书、账号凭据；后续分发须保留译文许可及署名。
