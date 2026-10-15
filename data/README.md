# 字符覆盖参考

`mobile-font-charset.txt` 用于构建时的保守字符检查，不是字体文件、字体 cmap 或实机逐字验证结果。输入文本使用过某个字符，不证明游戏字体一定支持它；不在集合内也不证明游戏一定缺字。

参考来源为 TIMER-err/Limbus-Company-Mobile-Localization 的移动端适配研究（参考提交 `36671de080eca2567c4e5625c20943de207b6698`），以及官方日文资源、ghcruise 已发布移动端汉化文本的字符观察。文件头注释已为本工具修改。上游署名和第三方材料说明保留于 `UPSTREAM-NOTICE.txt`，Apache 2.0 许可文本见 `LICENSE-APACHE-2.0.txt`；该许可不改变其列明的游戏资源及译文权利。ghcruise 参考材料适用 CC BY-NC-SA 4.0：<https://creativecommons.org/licenses/by-nc-sa/4.0/>。

## 保守的简繁 / 日文字形降级表

`mobile-safe-glyph-map.json` 是可选的 1,283 项映射，不是字体文件，也不保证实机显示或所有语境下的语义正确。它由 Open Chinese Convert (OpenCC), Copyright BYVoid and contributors 的 `ver.1.1.9` / 提交 `556ed22496d650bd0b13b6c163be9814637970ae` 中 `data/dictionary/STCharacters.txt`、`JPVariants.txt` 筛选得到，适用 Apache 2.0（见本目录许可文本及 `UPSTREAM-NOTICE.txt`）。修改方式：仅保留源字符不在参考集合内、单一候选且最终字符在参考集合内的条目；优先繁体，繁体不在参考集合时才考虑 OpenCC 列出的单一日文变体。源字符没有简繁条目时，也独立考虑单一日文变体，如 `增 → 増`。仍跳过多候选简繁条目，不通过日文表绕过歧义限制。不是从未审核的本地 `mobile-glyph-map.json` 派生。

此策略保留已在参考集合内的简体字；遇到 `发 → 發 / 髮` 一类多候选条目直接跳过，不拿相似但不同义的字替换，例如不使用 `你 → 袮`。因此输出会混合简体、繁体和少量日文汉字形，仍有未覆盖字符。字典单一候选不等同于完成逐句审校，参考集合也不等同于字体 cmap。

来源：<https://github.com/BYVoid/OpenCC/tree/556ed22496d650bd0b13b6c163be9814637970ae/data/dictionary>。原始文件 SHA-256 固定在 `build_glyph_map.py`，生成时只读取本地文件、不联网、不引入依赖。将上述提交的两个文件下载到本地后，可复现到一个不存在的新路径，再与分发映射比较：

```sh
python3 build_glyph_map.py \
  --st-characters /path/to/STCharacters.txt \
  --jp-variants /path/to/JPVariants.txt \
  --font-charset data/mobile-font-charset.txt \
  --out /tmp/mobile-safe-glyph-map-rebuilt.json
cmp data/mobile-safe-glyph-map.json /tmp/mobile-safe-glyph-map-rebuilt.json
```

构建资源时显式加入 `--glyph-mode compatible --glyph-map data/mobile-safe-glyph-map.json`；默认 `preserve` 仍保留 LLC 原文。尚未实机验证的兼容资源须继续标为实验包，不能把报告中的参考集外字符数说成实际方框数。

## 截图定位后的整字段文本适配

`mobile-text-fallbacks.json` 是另行选择的 10 条人工适配，**包含措辞改写与官方英文姓名，不是纯简繁转换**。来源为 LLC `2026100901` 及官方 `l20261015_xV9SErze50K09CmgQkCb` 资源，按用户提供的界面定位。译文及其修改继续适用 CC BY-NC-SA 4.0，受底层游戏资源权利限制。没有分发用户截图、账号信息或日志。

- `JP_UserInfo_Friends.json` / `Uid_Copy`：复制 → 複製。
- `JP_IntroductionPreset.json` / `introduce_sentence_1` 及 `StoryData/JP_S101B.json` / `id=1`：可以吗？ → 可以？；保留模板 `{0}` 和完整句子其余内容。
- `StoryData/JP_S101B.json` / `id=3`：当你想战胜枯燥感时 → 要克服枯燥感。对应官方日文原义为克服无聊，避免截图实证缺字“你、胜”。
- 同文件 / `id=8`：嗯。哐哧哐哧。 → 唔。轟隆轟隆。对应官方 `うん、がたんがたん。`，是确认回应与行车拟声的兼容改写。
- `ScenarioModelCodes-AutoCreated.json` / `id=카론` 的姓名“卡戎”及精确同值的说话人字段：改用官方英文名 `Charon`。已读取配套官方英文 ZIP 核实该记录的 `Hash` 与 `Size`；英文 ZIP SHA-256 为 `851abb93f8d1fdc26f0d83268095e535dd1aabc6c70efb7b6d23c69b68844897`。不改角色 ID，也不在长句内全局替换“卡”。
- r5：`JP_Items.json` / `id=1/2/3` 同值说明中的“能够”改为“可”，术语“脑啡肽”使用配套官方英文 `Enkephalin`，避开截图缺字“够、肽”。
- r5：`StoryData/JP_S101B.json` / `id=17` 省略指向对话人的“你”，并把“对吧”改为“对不对”；`id=35` 改为“有没有意识到现在声音最大的是谁？”。这两句是保持对话含义的措辞调整，避免“你、吧、吵、呢”缺字。
- r5：姓名“格里高尔”按配套英文 `EN_ScenarioModelCodes-AutoCreated.json` / `id=그레고르` 使用 `Gregor`，避免“尔”缺字；整字段适配共命中 1,991 次，角色 ID 不变。

用 `--text-fallbacks data/mobile-text-fallbacks.json` 显式选择，只允许 `--llc-zip` 配合 `--glyph-mode compatible`。先整字段精确匹配，再执行单字映射；仅作用于既有可见文本白名单，不改变 ID、路径、未知字段或其他句子的子串。加载时检查格式占位符/标签不变，且最终 CJK 字符都在参考集内；命中次数和未使用条目写入报告。默认不启用，不能据此声称完整原文或全游戏无方框。
