# 开发交接记录

日期：2026-10-14。由最初的项目安全评估会话迁入本项目。

## 用户目标

使用已有 Shadowrocket 和本地 CA 在 iOS 上通过 MitM 汉化 Limbus Company；掌握模块、资源及更新发布，避免无条件追随第三方 latest。

## 已实现与验证

- Python 3 标准库离线工具 prepare_release.py 与 19 项 unittest。
- 输入 ZIP、manifest 须提供精确 SHA-256；解析 JSON、检查路径、解压规模、文件集合、文件大小及 LF 规范化 MD5。
- 可将 LLC 中文 JSON 按稳定 ID 合并到匹配的日文槽位，保留结构/控制字段，补剧情说话人字段；支持记录缺字并可选应用显式字形映射。
- JP 槽位资源确定性重打包，更新清单 Hash/Size；`--refresh-jp-hashes` 在路径、集合、大小匹配时刷新底包 JP Hash。
- 输出仅重定向游戏 CDN 语言 ZIP 和清单的 Shadowrocket 模块，目标为用户自有仓库固定 Release 标签。
- 使用 ghcruise v1.116.2-alpha 的 2,412 个 ZIP 文件完成全量哈希及重打包检查，7,182 个清单文件均为语言 JSON。
- 测试命令：python3 -m unittest -v test_prepare_release.py test_llc_build.py。
- 实验产物：`work/llc-20261009-preserve-experimental`，输入 LLC ZIP SHA-256 `534ac2a4f020d7bde05a2d088b917fa24871d68b122927fc5b282a915a19d5ee`。该输入是固定旧快照，不是当前上游。
- 实验构建匹配 2,330 个槽位 / 101,596 条记录；参考字符集 4,620 字中有 1,447 个未覆盖字符，按字符与文本字段组合计数共命中 682,233 次（同字段同字重复只计一次）。报告通过结构验证，但带 `experimental: true`，不可发布或称为实机验证通过。

## 参考项目

- ghcruise/LimbusCompany-IOS-Localization：审查提交 839fa123c9992fa6d447c55ee55abf1ffe41ac24；普通版只有两条 302 + 游戏 CDN MitM。无节点直连版还覆写认证服务路由，不作为首选。
- TIMER-err/Limbus-Company-Mobile-Localization：参考提交 36671de080eca2567c4e5625c20943de207b6698；公开完整打包、字库与角色名处理实现。尚未完成全部构建脚本和 Actions 安全审查，未运行其代码。
- LocalizeLimbusCompany/LocalizeLimbusCompany：中文译文上游。

## 后续工作与边界

1. 审查完整参考构建实现；设计固定上游版本与人工批准的下载、构建、发布流程。
2. 获取并固定最新 LLC 与游戏日文资源输入，重新构建并审查缺字、字段匹配和变更报告；不要直接使用上游 latest 自动发布。
3. 评估目标游戏实际字体文件的提取/注入是否可行；当前只有资源观察所得覆盖下界，没有游戏字体文件或安全的通用简繁映射。
4. 在 iPhone 验证目标版本的资源下载、缓存刷新、缺字和简体显示，再决定能否发布。
5. 再考虑 CI；未经用户要求不启用自动发布、定时同步或设备更新。

当前是离线构建工具，不会修改/嵌入 iOS 字体，也不保证覆盖参考等同实际字体或译文语义安全。默认 preserve 保留 LLC 原字符，因此实验包本身不会把繁体自动转为简体。固定 Release 标签不是不可变附件，也不是设备端验签。本仓库没有游戏/译文资源附件、证书、账号凭据；后续分发须保留译文许可及署名。
