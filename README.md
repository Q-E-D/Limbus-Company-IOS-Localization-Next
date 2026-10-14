# Limbus-Company-IOS-Localization-Next

面向 Shadowrocket / iOS MitM 汉化的离线资源审核与打包原型。当前不提供可直接安装的汉化发行版。

此工具支持两种操作：验证并原样暂存已审查的 ZIP/清单，或用已经适配移动端字库的 JSON 覆盖现有日文槽位、重新生成 ZIP 与清单。仅用 Python 3 标准库；不联网、不安装证书、不运行游戏、不发布 GitHub Release。

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

需要替换 JSON 时追加 `--overlay-jp /path/to/adapted-jp`。该目录使用 ZIP 中 `LocalizeTemp_jp/` 之后的相对路径，例如 `JP_AbDlg_DonQuixote.json` 或 `StoryData/JP_….json`。只能覆盖已有槽位；新游戏版本应重新获取配套底包和清单。译文目录的每个文件都必须是 JSON，不能直接传入 LLC 的未适配目录。

## 范围与限制

验证包括输入 SHA-256、重复 JSON 键、文件路径、非普通 ZIP 项、解压大小上限、JSON 语法、JP 文件集合、文件大小及换行规范化 MD5。通过这些检查只说明结构与记录一致，不证明译文语义安全或内容可信。摘要也不代替人工审查。

此原型没有实现完整的“官方日文资源 + LLC 中文译文 → 字形转换 → 剧情字段补全”流水线，也未在 iPhone 上验证。重打包后仍可能因字体覆盖、文本格式、游戏版本或缓存问题出现显示/下载异常。固定标签减少自动追随上游的变化，但 GitHub Release 附件本身仍可能被有权限的人替换；模块不执行 SHA-256 校验。

测试：`python3 -m unittest -v test_prepare_release.py`。

## 参考与许可

- 原模块与样本：[ghcruise/LimbusCompany-IOS-Localization](https://github.com/ghcruise/LimbusCompany-IOS-Localization)，CC BY-NC-SA 4.0。
- 中文译文上游：[LocalizeLimbusCompany](https://github.com/LocalizeLimbusCompany/LocalizeLimbusCompany)，CC BY-NC-SA 4.0。
- 完整构建参考：[TIMER-err/Limbus-Company-Mobile-Localization](https://github.com/TIMER-err/Limbus-Company-Mobile-Localization/tree/36671de080eca2567c4e5625c20943de207b6698)，公开字形映射、覆盖和打包流程。此原型为独立编写，未复制其源码或字库数据。

本目录不包含第三方译文、游戏资源或证书。资源重新发布时应遵守相关许可；本地生成的检查报告不是安全认证。
