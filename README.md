# Limbus-Company-IOS-Localization-Next

面向 Shadowrocket / iOS MitM 汉化的离线资源审核与打包工具。首个发行版使用已核查的 ghcruise `v1.116.2-alpha` 资源（2026-10-08），提供固定版本的安装模块。

此工具支持验证已审查资源、将 LocalizeLimbusCompany (LLC) 中文 JSON 按稳定 ID 合并进日文资源槽位，并重新生成 ZIP 与清单。它只改文本资源，不修改或嵌入游戏字体；字库文件目前以从已观察移动端资源推导的覆盖下界作为参考。仅用 Python 3 标准库；不联网、不安装证书、不运行游戏、不发布 GitHub Release。

构建工具版本：`v0.2.0-alpha.2`（实验版源码标签，补齐参考数据署名与许可）。该标签不提供新的 Shadowrocket 资源附件，手机安装地址仍为下面的 `reviewed-20261008`。源码升级、资源升级与回退步骤见 [升级验证说明](docs/UPGRADE.md)。

### LLC 原文实验包

当前候选版为 `llc-ios-20261016-r5-compat`：基于重新下载的配套官方资源，修正英文、韩文清单与实际 ZIP 的 Hash/Size 不一致，并补充 r4 截图中的两句剧情、月狂石说明及 Gregor 姓名适配。35 项测试及最终资源静态核验通过；重复启动和实际字体渲染仍待手机验证。关闭旧 Limbus 模块，只启用新版：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-ios-20261016-r5-compat/LimbusReviewed.module
```

四张截图已定位到 `复、吗、卡、你、胜、嗯、哐、哧` 缺字。新增 `llc-ios-20261015-r4-compat` 候选版：补上独立日文变体映射，并用 6 条整字段适配处理截图中的复制按钮、名片句型、卡戎姓名及三条开场台词。**它含少量措辞改写及官方英文名 `Charon`，不再只是单字简繁转换。** 目标文本静态检查通过，其他场景仍可能有方框，未做新包的手机渲染验证。关闭其他 Limbus 模块后安装：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-ios-20261015-r4-compat/LimbusReviewed.module
```

具体适配及限制见 [字符参考说明](data/README.md) 和 [升级说明](docs/UPGRADE.md)。r3 与 r2 仍保留作对照。

出现方框时可试用独立的缺字兼容候选版 `llc-ios-20261015-r3-compat`：沿用 r2 的官方底包和 LLC 快照，按保守参考集合，仅对单一对应的简体字做繁体 / 日文变体降级。原文版 r2 保留，默认构建模式也不变。兼容版的参考集外字符由 1,447 种降为 484 种，这不是实机方框计数，仍需手机验证；不修改字体，不保证消除所有方框。关闭其他 Limbus 模块后添加：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-ios-20261015-r3-compat/LimbusReviewed.module
```

映射来源、跳过多义转换的策略及复现步骤见 [字符参考说明](data/README.md)；安装和对照验证见 [升级说明](docs/UPGRADE.md)。

手机当前 `l20261015_xV9SErze50K09CmgQkCb` 资源目录请使用候选修订版 `llc-ios-20261015-r2`。它使用 10 月 15 日官方清单和日文底包，完整保留当前非 JP 条目，并把重写限定到该版本目录，避免旧清单覆盖以后游戏版本。译文仍为 LLC `2026100901`，未匹配内容保留日文；尚待连续启动验证重复下载是否消失。关闭旧模块后安装：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-ios-20261015-r2/LimbusReviewed.module
```

诊断证据与路由建议见 [升级验证说明](docs/UPGRADE.md)。

独立资源预发布版本：`llc-experimental-20261015`，使用固定的 LLC `2026100901` 快照与官方日文资源构建，保留原文、不应用字形替换。不是最新译文或已完成 iPhone 验证的稳定包。参考字符集合未覆盖 1,447 种输出字符，可能有缺字/方框；未合并部分保留日文。

在 Shadowrocket 模块页关闭旧汉化模块，再添加并启用此地址：

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/llc-experimental-20261015/LimbusReviewed.module
```

重新连接 Shadowrocket 并重启游戏，语言选日语；确认新版本清单和 ZIP 成功下载后，再检查主界面、技能与剧情字形。完整步骤与缓存回退限制见 [升级验证说明](docs/UPGRADE.md)。[实验包发布说明](https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/tag/llc-experimental-20261015)。

## Shadowrocket 安装

前提：已在 Shadowrocket 生成、安装并信任自己的 CA，已开启 HTTPS 解密。

1. 在 Shadowrocket 的“配置”页点击当前配置右侧 ⓘ，进入“模块”，点 ＋ 添加下方地址并启用。
2. 如有其他 Limbus 汉化模块，关闭它们，避免规则冲突。
3. 重新连接 Shadowrocket，完全退出并重新打开游戏，将游戏语言设为日语；允许下载语言资源。

```text
https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/download/reviewed-20261008/LimbusReviewed.module
```

[下载与校验记录](https://github.com/Q-E-D/Limbus-Company-IOS-Localization-Next/releases/tag/reviewed-20261008)

模块和资源均固定到 `reviewed-20261008`，不会自动追随第三方 `latest`。发布新资源后需改用新版本模块；旧版本继续使用旧资源。此发布已做离线结构校验，尚未在 iPhone 上实测；字库限制、资源版本变化或客户端缓存可能影响效果。游戏若未下载新资源，不要直接清除游戏数据，先检查模块命中和下载记录。

## 已验证的格式

- ZIP 内路径为 `LocalizeTemp_jp/…/JP_*.json`，对应清单中的 `Assets/Resources_moved/Localize/jp/…/JP_*.json`。
- `Size` 是文件原始字节数；`Hash` 是将 CRLF 换行替换为 LF 后的 MD5。已核对 ghcruise `v1.116.2-alpha` 全部 2,412 个 JP 文件，全部匹配。
- 默认保留非 JP 条目；显式指定 `--companion-locale en /path/to/en.zip <sha256>`（或 `kr`，可重复）时，仅按固定且文件集合一致的官方 ZIP 重建对应语言的 Hash/Size。版本、EncryptKey/EncryptIV 与 Crc 保留。它们的游戏内部语义没有重新实现。
- 生成的模块仅重定向语言 ZIP 与清单，限制游戏 CDN 域名，支持查询参数，指向你的固定 Release 标签。

## 使用

在此目录执行；将 `YOUR_OWNER/YOUR_REPO` 换成自己的公开 GitHub 仓库。先将两个附件下载到本地。下面的哈希仅适用于已检查的 ghcruise `v1.116.2-alpha`，以后更新必须重新核对。

```sh
python3 prepare_release.py \
  --zip /path/to/localize_jp.zip \
  --manifest /path/to/manifest.json \
  --zip-sha256 b1f4aa2ec48fd2cb51b1a6fcd92a421c29a6bdd9e89a20fb9b0fe4f5a08baff3 \
  --manifest-sha256 98ee30a75b05cf9ec1114ffa1ce143c63ff5e85351528f2b8242a1ad25ec17fb \
  --repo YOUR_OWNER/YOUR_REPO \
  --tag reviewed-20261008 \
  --out ./staged-release
```

输出 `localize_jp.zip`、`manifest.json`、`LimbusReviewed.module`、`validation.json`。输出目录必须不存在，防止覆盖之前的结果。上传附件时仍须保留原项目许可、来源、作者署名及修改说明；生成的模块需在相同标签的附件实际发布后才可使用。

### 从 LLC 构建

准备与目标游戏版本匹配的官方日文 ZIP、manifest、LLC 简体中文 ZIP，并为每个输入记录 SHA-256。构建必须使用固定输入；不要在构建时下载未经审查的 `latest`。示例：

```sh
python3 prepare_release.py \
  --zip /path/to/localize_jp.zip \
  --manifest /path/to/manifest.json \
  --zip-sha256 <official-jp-zip-sha256> \
  --manifest-sha256 <manifest-sha256> \
  --refresh-jp-hashes \
  --llc-zip /path/to/llc-zh-CN.zip \
  --llc-zip-sha256 <llc-zip-sha256> \
  --font-charset data/mobile-font-charset.txt \
  --allow-missing-glyphs \
  --repo YOUR_OWNER/YOUR_REPO \
  --tag llc-reviewed-YYYYMMDD \
  --out ./staged-llc-build
```

`--refresh-jp-hashes` 只在 ZIP/manifest 路径、文件集合和原始大小都匹配时重算 JP Hash。默认 `--glyph-mode preserve` 原样保留 LLC 字符，不会把繁體自動轉成簡體；若覆盖参考中有缺字，构建默认失败。`--allow-missing-glyphs` 只用于本地实验包，不代表这些字在 iPhone 上可显示。

发布固定清单时，应追加 `--official-localize-root https://downloadcommon.limbuscompanycdn.org/lYYYYMMDD_VERSION/Assets`，使用日志中确认的实际版本 URL。这样两条重写仅匹配配套资源目录；游戏改用新目录后将使用官方资源，需重新审查和构建相应汉化包。输入 SHA-256 验证不证明 URL 与输入配套，发布前还须核对来源和报告。省略此选项保留旧版通配匹配行为，不适合跨游戏版本长期启用固定清单。

可用 `--glyph-mode compatible --glyph-map data/mobile-safe-glyph-map.json` 显式启用内置保守映射，或提供自行审核的单字表。该替换可能影响词义、专名或语气，输出不再是严格的简体原文；内置表只接受固定 OpenCC 数据中的单一候选，不采用任意形似替换，但仍不能代替逐句审校或实际字体检查。

在上述 LLC 兼容构建中另加 `--text-fallbacks data/mobile-text-fallbacks.json` 可选择截图定位后的整字段措辞适配；这与单字简繁转换是两类改动，具体内容、来源与保护条件见 `data/README.md`。

之前构建的样例位于忽略目录 `work/llc-20261009-preserve-experimental`：输入 LLC ZIP SHA-256 为 `534ac2a4f020d7bde05a2d088b917fa24871d68b122927fc5b282a915a19d5ee`。它来自固定的 2026-10-09 资源快照，不代表 LLC 当前上游版本。样例匹配 2,330 个 JP 槽位、101,596 条记录；参考字符集有 4,620 字，仍发现 1,447 个未覆盖字符（按字符与文本字段组合计数，共命中 682,233 次；同一字在同一字段重复出现只计一次）。所以它是结构验证通过的实验构建，不可当作可发布或实机字库验证通过的版本。

需要手工覆盖 JSON 时仍可追加 `--overlay-jp /path/to/adapted-jp`。目录使用 ZIP 中 `LocalizeTemp_jp/` 之后的相对路径，例如 `JP_AbDlg_DonQuixote.json` 或 `StoryData/JP_….json`，只能覆盖已有槽位。

## 范围与限制

验证包括输入 SHA-256、重复 JSON 键、文件路径、非普通 ZIP 项、解压大小上限、JSON 语法、JP 文件集合、文件大小及换行规范化 MD5。通过这些检查只说明结构与记录一致，不证明译文语义安全或内容可信。摘要也不代替人工审查。

LLC 到 JP 槽位的合并、剧情说话人字段补全和资源重打包已实现；但实际字体文件提取/注入、完整简繁转换和 iPhone 字形验证没有实现。`data/mobile-font-charset.txt` 只是从观察到的资源推导出的覆盖下界，不是 iOS 字体本身。即使报告无缺字，也需用目标 iOS 版本、游戏版本和具体设备验证字形、下载及缓存行为。固定标签减少自动追随上游的变化，但 GitHub Release 附件仍可被有权限的人替换；模块不执行 SHA-256 校验。

测试：`python3 -m unittest -v`。

## 参考与许可

- 原模块与样本：[ghcruise/LimbusCompany-IOS-Localization](https://github.com/ghcruise/LimbusCompany-IOS-Localization)，CC BY-NC-SA 4.0。
- 中文译文上游：[LocalizeLimbusCompany](https://github.com/LocalizeLimbusCompany/LocalizeLimbusCompany)，CC BY-NC-SA 4.0。
- 完整构建参考：[TIMER-err/Limbus-Company-Mobile-Localization](https://github.com/TIMER-err/Limbus-Company-Mobile-Localization/tree/36671de080eca2567c4e5625c20943de207b6698)，公开字形映射、覆盖和打包流程。Python 构建工具为独立编写；参考字符集的来源、用途和许可见 [data/README.md](data/README.md)。

本目录不包含第三方译文、游戏资源或证书。资源重新发布时应遵守相关许可；本地生成的检查报告不是安全认证。
