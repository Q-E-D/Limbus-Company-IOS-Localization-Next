# 升级与验证

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
