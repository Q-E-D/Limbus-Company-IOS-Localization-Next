# 升级与验证

## llc-ios-20261015-r2：当前资源目录适配候选版

2026-10-15 导出的 Shadowrocket 路由数据库记录了 15:39:26–15:40:44 的一次启动。清单和日文 ZIP 的两条重写实际指向 `reviewed-20261008`，而官方请求已在 `l20261015_xV9SErze50K09CmgQkCb` 目录；随后有英文、韩文、日文 ZIP 请求。48 条路由记录均为 `PROXY # 香港 2`。数据库没有 HTTP 状态码、响应内容、字节数或多次启动记录，因此不能单凭它证明下载成功或每次必然重复。

取日志中的官方当前清单比较后，旧清单与英文有 34 项差异、韩文有 37 项差异，公共索引也有差异；当前各语言新增 8 个文件。旧清单与当前官方 ZIP 不配套，符合反复校验/下载的表现，实际缓存机制仍需实测。原 `llc-experimental-20261015` 也沿用了旧底包，切换到该包不能消除版本冲突。

修订候选版使用当前官方 ZIP 和清单，包含 2,420 个日文文件、7,206 个清单条目；非 JP 条目和元数据逐项与当前官方清单一致。LLC 仍固定为 `2026100901`，合并 2,330 个文件、101,607 条记录；其余使用当前官方日文。不应用字形替换，1,447 种字符不在参考集合内，实际字体覆盖未验证。

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-ios-20261015-r2/LimbusReviewed.module
```

模块只重写上述官方版本目录的清单与日文 ZIP，MITM 仅追加 `downloadcommon.limbuscompanycdn.org`。将来资源目录改变时这两条重写不会命中，需配套构建新版。旧模块若仍开启，其通配规则仍可能覆盖新版请求，升级前必须关闭所有其他 Limbus 汉化模块。

安装后第一次可能下载配套资源。下载完成后完全退出并再次启动两次，分别保存下载容量和请求记录，确认后两次没有重复语言 ZIP 下载，才能判定修复有效。当前只通过离线校验，不能称为实机修复验证通过。

### 路由与速度

汉化需要 Shadowrocket 连接、HTTPS 解密和模块保持开启，不要求游戏流量经代理节点。这份只有重写和 MITM 的模块可尝试全局路由“直连”；是否实际生效应检查新请求命中重写及 DIRECT，中文缓存本身不足以证明。

如 GitHub 附件直连不畅，可使用“配置”模式，针对已观察到的游戏 CDN/API 域名设置 DIRECT，GitHub 及附件域名按需代理。示例需放在会覆盖它们的通用规则之前，并使用当前配置中实际存在的策略名称：

```ini
DOMAIN-SUFFIX,limbuscompanycdn.org,DIRECT
DOMAIN-SUFFIX,limbuscompanyapi.com,DIRECT
DOMAIN,github.com,PROXY
DOMAIN,release-assets.githubusercontent.com,PROXY
```

`PROXY` 须替换成实际策略（如已有代理策略组）；以上只是一段规则示例，不是完整配置或测速结论。不要把 GitHub/API 加到 MITM；当前模块仅解密所需 CDN。音频 `FmodPatchInfo.json` 是另一份官方清单，其存在不能证明音频包重复下载。

## v0.2.0-alpha.2

此版本标记 LLC 译文合并、剧情字段补齐、字形参考检查和确定性打包工具的源码状态。19 项单元测试通过；没有游戏字体注入，也没有新的手机可安装资源附件。

`v0.2.0-alpha.1` 为初始实现标签；`v0.2.0-alpha.2` 补齐参考字符数据的来源与许可说明，不改变打包行为。两个标签均保留。

已安装的 `reviewed-20261008` 模块继续使用原资源。更新模块或拉取源码不会自动切换到 LLC 实验包，不要把源码标签拼成 Release 附件地址。

## 可安装实验包 llc-experimental-20261015

该资源版本与源码标签独立，使用 LLC `2026100901` 固定快照重新构建，保留原文且不做字形替换。模块地址：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-experimental-20261015/LimbusReviewed.module
```

这是供实机验证的预发布包。覆盖 2,330 个日文槽位，匹配 101,596 条记录；有 1,447 种字符未被观察参考集合覆盖，实际字库支持与当前游戏兼容性未验证。请按本文手机测试步骤操作，保留旧模块回退。

## 本地源码验证

先用 `git status --short` 检查并保存本地修改，再执行：

```sh
git fetch origin --tags
git show --stat v0.2.0-alpha.2
git switch --detach v0.2.0-alpha.2
python3 -m unittest -v test_prepare_release.py test_llc_build.py
python3 -m py_compile prepare_release.py test_prepare_release.py test_llc_build.py
```

完成后可用 `git switch main` 回到开发分支。

## 后续手机测试包

准备手机测试包时，须固定与目标游戏版本匹配的官方日文 ZIP、manifest 和 LLC 译文版本，记录输入 SHA-256，重新构建并核对报告。现有 2026-10-09 输入实验包存在参考覆盖缺口，未验证与当前客户端匹配，不能作为稳定升级包。

测试包应使用独立的实验标签和附件地址，标明游戏版本、译文版本、未合并项、字形限制与 SHA-256；保留旧版模块作为回退入口。附件实际可下载后，手机按以下步骤验证：

1. 完全退出游戏；在 Shadowrocket 当前配置的模块页关闭旧 Limbus 汉化模块，添加并启用新测试版本的 `LimbusReviewed.module` 地址，避免同时启用两套重写。
2. 保持 HTTPS 解密开启，重新连接 Shadowrocket，使用“配置”路由模式和已验证节点；无需为汉化切换全局路由。
3. 启动游戏，语言设为日语，观察是否触发语言资源下载。检查 Shadowrocket 请求记录，确认语言 ZIP 和 `LocalizePatchInfo.json` 命中新模块并成功下载固定标签附件；仅看到中文不能证明已切换新包，可能仍在使用缓存。
4. 检查主界面、技能/人格描述以及一段带说话人和称号的剧情。对照 LLC 输入文本，检查简体文字、方框/空白/乱码、日文残留、富文本标签和断行，同时验证登录和资源下载正常。
5. 若没有新下载或显示异常，先保存对应界面截图、游戏版本及相关请求的状态码；不要直接清除游戏数据或卸载。分享日志时隐藏账号、令牌、订阅和节点地址。

回退时关闭实验模块、重新启用原 `reviewed-20261008` 模块并重连、重启游戏。模块回退不会主动删除游戏已缓存的新文本，仍需确认原资源重新下载后才能认定回退完成。
