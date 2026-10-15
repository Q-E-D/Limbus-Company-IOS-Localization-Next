# Limbus-Company-IOS-Localization-Next

面向 Shadowrocket / iOS MitM 汉化的离线资源审核与打包工具。首个发行版使用已核查的 ghcruise `v1.116.2-alpha` 资源（2026-10-08），提供固定版本的安装模块。

此工具支持验证已审查资源、将 LocalizeLimbusCompany (LLC) 中文 JSON 按稳定 ID 合并进日文资源槽位，并重新生成 ZIP 与清单。它只改文本资源，不修改或嵌入游戏字体；字库文件目前以从已观察移动端资源推导的覆盖下界作为参考。仅用 Python 3 标准库；不联网、不安装证书、不运行游戏、不发布 GitHub Release。

构建工具版本：`v0.2.0-alpha.1`（实验版源码标签）。该标签不提供新的 Shadowrocket 资源附件，手机安装地址仍为下面的 `reviewed-20261008`。源码升级、资源升级与回退步骤见 [升级验证说明](docs/UPGRADE.md)。

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
- 清单中非 JP 资源、版本、EncryptKey/EncryptIV 与 Crc 原样保留。它们的游戏内部语义没有重新实现。
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

如有人工审核的单字替换表，可用 `--glyph-mode compatible --glyph-map /path/to/map.json` 显式替换参考字库不含的字符。该替换可能改变词义、专名或语气，输出不会是严格的简体原文，必须逐项审校。仓库没有内置通用替换表，因为无法从字形相似可靠推出语义等价。

之前构建的样例位于忽略目录 `work/llc-20261009-preserve-experimental`：输入 LLC ZIP SHA-256 为 `534ac2a4f020d7bde05a2d088b917fa24871d68b122927fc5b282a915a19d5ee`。它来自固定的 2026-10-09 资源快照，不代表 LLC 当前上游版本。样例匹配 2,330 个 JP 槽位、101,596 条记录；参考字符集有 4,620 字，仍发现 1,447 个未覆盖字符（按字符与文本字段组合计数，共命中 682,233 次；同一字在同一字段重复出现只计一次）。所以它是结构验证通过的实验构建，不可当作可发布或实机字库验证通过的版本。

需要手工覆盖 JSON 时仍可追加 `--overlay-jp /path/to/adapted-jp`。目录使用 ZIP 中 `LocalizeTemp_jp/` 之后的相对路径，例如 `JP_AbDlg_DonQuixote.json` 或 `StoryData/JP_….json`，只能覆盖已有槽位。

## 范围与限制

验证包括输入 SHA-256、重复 JSON 键、文件路径、非普通 ZIP 项、解压大小上限、JSON 语法、JP 文件集合、文件大小及换行规范化 MD5。通过这些检查只说明结构与记录一致，不证明译文语义安全或内容可信。摘要也不代替人工审查。

LLC 到 JP 槽位的合并、剧情说话人字段补全和资源重打包已实现；但实际字体文件提取/注入、完整简繁转换和 iPhone 字形验证没有实现。`data/mobile-font-charset.txt` 只是从观察到的资源推导出的覆盖下界，不是 iOS 字体本身。即使报告无缺字，也需用目标 iOS 版本、游戏版本和具体设备验证字形、下载及缓存行为。固定标签减少自动追随上游的变化，但 GitHub Release 附件仍可被有权限的人替换；模块不执行 SHA-256 校验。

测试：`python3 -m unittest -v test_prepare_release.py test_llc_build.py`。

## 参考与许可

- 原模块与样本：[ghcruise/LimbusCompany-IOS-Localization](https://github.com/ghcruise/LimbusCompany-IOS-Localization)，CC BY-NC-SA 4.0。
- 中文译文上游：[LocalizeLimbusCompany](https://github.com/LocalizeLimbusCompany/LocalizeLimbusCompany)，CC BY-NC-SA 4.0。
- 完整构建参考：[TIMER-err/Limbus-Company-Mobile-Localization](https://github.com/TIMER-err/Limbus-Company-Mobile-Localization/tree/36671de080eca2567c4e5625c20943de207b6698)，公开字形映射、覆盖和打包流程。此原型为独立编写，未复制其源码或字库数据。

本目录不包含第三方译文、游戏资源或证书。资源重新发布时应遵守相关许可；本地生成的检查报告不是安全认证。
