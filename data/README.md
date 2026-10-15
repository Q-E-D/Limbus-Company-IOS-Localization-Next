# 字符覆盖参考

`mobile-font-charset.txt` 用于构建时的保守字符检查，不是字体文件、字体 cmap 或实机逐字验证结果。输入文本使用过某个字符，不证明游戏字体一定支持它；不在集合内也不证明游戏一定缺字。

参考来源为 TIMER-err/Limbus-Company-Mobile-Localization 的移动端适配研究（参考提交 `36671de080eca2567c4e5625c20943de207b6698`），以及官方日文资源、ghcruise 已发布移动端汉化文本的字符观察。文件头注释已为本工具修改。上游署名和第三方材料说明保留于 `UPSTREAM-NOTICE.txt`，Apache 2.0 许可文本见 `LICENSE-APACHE-2.0.txt`；该许可不改变其列明的游戏资源及译文权利。ghcruise 参考材料适用 CC BY-NC-SA 4.0：<https://creativecommons.org/licenses/by-nc-sa/4.0/>。

## 保守的简繁 / 日文字形降级表

`mobile-safe-glyph-map.json` 是可选的 1,048 项映射，不是字体文件，也不保证实机显示或所有语境下的语义正确。它由 Open Chinese Convert (OpenCC), Copyright BYVoid and contributors 的 `ver.1.1.9` / 提交 `556ed22496d650bd0b13b6c163be9814637970ae` 中 `data/dictionary/STCharacters.txt`、`JPVariants.txt` 筛选得到，适用 Apache 2.0（见本目录许可文本及 `UPSTREAM-NOTICE.txt`）。修改方式：仅保留源字符不在参考集合内、单一候选且最终字符在参考集合内的条目；优先繁体，繁体不在参考集合时才考虑 OpenCC 列出的单一日文变体。不是从未审核的本地 `mobile-glyph-map.json` 派生。

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
