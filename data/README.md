# 字符覆盖参考

`mobile-font-charset.txt` 用于构建时的保守字符检查，不是字体文件、字体 cmap 或实机逐字验证结果。输入文本使用过某个字符，不证明游戏字体一定支持它；不在集合内也不证明游戏一定缺字。

参考来源为 TIMER-err/Limbus-Company-Mobile-Localization 的移动端适配研究（参考提交 `36671de080eca2567c4e5625c20943de207b6698`），以及官方日文资源、ghcruise 已发布移动端汉化文本的字符观察。文件头注释已为本工具修改。上游署名和第三方材料说明保留于 `UPSTREAM-NOTICE.txt`，Apache 2.0 许可文本见 `LICENSE-APACHE-2.0.txt`；该许可不改变其列明的游戏资源及译文权利。ghcruise 参考材料适用 CC BY-NC-SA 4.0：<https://creativecommons.org/licenses/by-nc-sa/4.0/>。

本版本未分发通用字形替换表。`compatible` 模式须由使用者显式提供经人工审核的映射；不能据字形相似认定词义等价。
