# 方框与英文残留根因调查

日期：2026-10-16。结论：**r5 没有根治缺字。本次没有发布新兼容包。**

## 已取得的证据

当前安装模块只有语言 ZIP 和 `LocalizePatchInfo.json` 两条重写。字体不在这些 JSON 中，
修改译文不能为客户端字体增加字形。r5 为规避缺字引入的 `Charon`、`Gregor`、
`Enkephalin` 也是部分英文的直接来源，不能把它们归因于缓存或上游漏翻。

对 r5 最终 ZIP 的全部 2,420 个文件重新审计，扫描 269,351 个已知可见文本字段：

- 481 种 CJK 字符不在观察参考集内，共 113,069 个字符/字段组合；这不是实机缺字计数。
- 33,039 个字段含拉丁字母候选，1,732 个含假名候选。它们包含术语、歌词、控制用途字符串，
  不能直接解释成漏翻数量。报告保留文件、JSON Pointer 及有限原文样本。
- 例：`StoryData/JP_3D309B.json` 中仍有日文。LLC 对应一句没有 `id`，之后的 ID 和官方资源不同，
  原构建器按 ID/model 拒绝错位覆盖；当前上游源码同一句仍是这种结构。盲目按数组下标合并会串台词。

旧的 `llc_build.missing_chars` 只检查有合并输出的覆盖层。现在的 `text_audit` 检查最终 ZIP，
包括未匹配文件和保留字段；缺字门禁也移到此步骤。没有改变任何译文或映射表。
门禁失败时给出有界的位置样本；独立只读命令可导出全部候选位置，无需放行缺字构建：

```sh
python3 inspect_release_text.py /path/to/localize_jp.zip \
  --font-charset data/mobile-font-charset.txt --all-candidates
```

报告中的有限样本按文本去重；`--all-candidates` 仍保留重复文本的全部字段位置。

## 实际 iOS 字体入口

来源为已有日志中的官方版本目录：

```text
https://downloadios.limbuscompanycdn.org/i20261015_TVKytScXZcbw9wpgb-Hv/catalog_S1.bin
```

文件大小 5,952,172 字节，SHA-256：

```text
87ef47e47eb1a23330fc3a85bf397c9480fbaf10b6991ef2fd144de4085edd81
```

按照 Unity Addressables 2.7.6 的 v2 二进制布局解析，得到 49,452 个 location。
`Assets/Resources_moved/Font/AddressableFallbackFont.asset` 的字体依赖为：

```text
{UnityEngine.AddressableAssets.Addressables.RuntimePath}/i20261015_TVKytScXZcbw9wpgb-Hv/addressablefonts_assets_all_3f124bb9c08213b9000693f1a6f471ab.bundle
```

这是本地 RuntimePath，**不是现有模块可拦截的 HTTPS 字体请求**。同名 Bundle 的官方 CDN
地址实际返回 404。另一个依赖是远端 `monoscripts` Bundle，不能把它误认为字体内容。
目录中同名字体 asset 有三个不同类型 location，共用上述依赖。

这证明当前两条 JSON 重写无法补字体，但不证明所有 MitM 字体方案都不可能。
可以研究修改远端 catalog，把本地字体依赖改到经过验证的自有 iOS Bundle；还需验证启动时序、
已加载字体、缓存、类型/PathID 引用、材质/atlas、Bundle Hash/CRC 和多字体回退链。
目前没有配套字体 Bundle，也没有实机加载证据，不能生成一个声称可用的字体模块。

复现目录检查（只读，不加载或修改 Bundle）：

```sh
python3 inspect_font_catalog.py /path/to/catalog_S1.bin
```

解析依据：[ContentCatalogData.cs](https://github.com/needle-mirror/com.unity.addressables/blob/f0fbfa922def906063627c201d2921d480ce72f4/Runtime/ResourceLocators/ContentCatalogData.cs)
中的 `ResourceLocator.Header / KeyData / ResourceLocation.Serializer.Data`，以及同版本
`BinaryStorageBuffer` 的长度前缀数组、ASCII/UTF-16 和分段字符串格式。只支持已核实的 v2。

## 参考项目的实际能力

| 项目与审查提交 | 证据与可用部分 |
| --- | --- |
| [ghcruise](https://github.com/ghcruise/LimbusCompany-IOS-Localization/tree/839fa123c9992fa6d447c55ee55abf1ffe41ac24) | 普通 module 两条 JSON 重写；README 明说受 iOS 字库限制，需要改写文本。没有字体注入实现。 |
| [Nginx](https://github.com/gongfuture/LimbusCompany-Nginx-Localization/tree/9f404bf95c7a14b4261252b820380a9113aa0257) | `nginx/conf/nginx.conf` 从 ghcruise 拉取同样的 ZIP/清单，没有额外字体替换。 |
| [LLC](https://github.com/LocalizeLimbusCompany/LocalizeLimbusCompany/tree/231a8bcfc347273e7769b70ebc4f9f3e2fecaa5a) | 提供 `Fonts/ChineseFont.ttf` 和 `LLCCN-Font.7z`；手动安装文档通过本地游戏目录加载自定义语言/字体，不是 iOS 语言 ZIP 字体入口。 |
| [ZSingularity](https://github.com/Vastrilliant/ZSingularity/tree/9b0bd2b28ad444c0fa9d354a0a773fc8b8d234b5) | `Mods/Mods.m` 的 `zs_load_custom_font` 调用 `CustomLocalizeManager.TryLoadFont`；写入 `_data`，给 TMP 字体注入 fallback 并刷新消费者。需客户端内代码执行，不能直接搬成 302 规则。 |
| [TIMER-err](https://github.com/TIMER-err/Limbus-Company-Mobile-Localization/tree/36671de080eca2567c4e5625c20943de207b6698) | 完整文本打包参考，仍是字符映射；部分映射如 `你→袮`、`卡→峠`、`肽→汰` 会损害原文。未将这份映射纳入本项目发布。 |

## 继续实作的必要输入与验收

下一步需要**配套 iOS 客户端中的上述字体 Bundle**，或可提取它的 IPA。
不能用一份 TTF 替代这个输入，也不能用 Android/Windows Bundle 冒充 iOS Bundle。
本机已检查的项目、下载目录和 PlayCover 常用目录中未找到该资源。

## iPhone 屏幕镜像复查

通过 macOS 的 iPhone 镜像查看了设备上的“文件”App。可见位置只有 iCloud 云盘和共享内容，
没有“我的 iPhone”、Limbus Company 文件夹或应用沙盒入口；镜像仅提供屏幕和输入，不能把
客户端私有 Bundle 导出到本机。切换到其他 App 后设备处于使用状态，镜像也会按系统规则断开，
这不改变资源结论。要继续验证字体替换，仍需用户通过 Finder/Apple Configurator 备份、设备端
导出或可提取的 IPA 提供上述 Bundle；屏幕镜像本身不能满足该输入。

## Stream 实机抓包复查

在 iPhone 上启动 Stream 的 HTTPS 抓包（CA 已安装并信任），再启动 Limbus Company 并等待资源
下载/进入主界面。最新会话为 `2026-10-16 12:33:13`，持续 3 分 51 秒，统计为 15 个请求、
上传 10.05 KB、下载 150.87 KB。Stream 按域名只显示四个来源：
`cdn.chinaliftoff-creatives.io`、`impression-asia.chinaliftoff.io`、`www.gstatic.com`、
`dispatcher.is.autonavi.com`；逐条请求是广告图片/脚本、遥测和地图相关资源，没有出现
`downloadios.limbuscompanycdn.org`、`catalog_S1.bin` 或 `addressablefonts_*.bundle`。

这次记录证明 Stream 的隧道可以工作，但没有取得游戏字体资源。游戏此前已完成大部分资源缓存，
启动时的 26 MB 下载随后显示 `Purchase Initialize Failed`，因此本轮不能把“没有字体请求”
解释为字体不存在；更可能是本地缓存、未触发资源更新，或游戏使用了 Stream 当前无法解析的
网络通道。需要在能触发版本资源更新的启动阶段重新抓包，或取得 IPA/设备备份后直接提取 Bundle。

取得资源后，先确定 TMP 字符表、源字体、atlas、材质与引用；再验证 catalog 重定向能否让原版客户端
加载替换后的 iOS 字体 Bundle。如果它在更新 catalog 前已加载，须进一步找到可用加载入口。
若客户端内执行 hook 是必要条件，必须明确报告纯 MitM 路线的限制，不能悄悄转向改包侧载。

根治版的验收必须包含：保留 LLC 中文姓名和术语；正文与 UI 使用的每条字体回退链覆盖完整译文；
最终包无未解释的漏翻/错位；目标 iPhone 实测正文、标题、姓名、技能及重启缓存行为。
静态参考集“零缺字”不满足这些验收条件。

本次本地证据保存在忽略目录 `work/root-cause-20261016/`：官方 catalog、r5 全包审计、
带新报告的 r5 复现构建。没有分发用户截图、日志或游戏字体资产。
