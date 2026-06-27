# rAthena 项目教训记录

## NPC 中文汉化 (2026-06)

### 失败方案
1. **直接覆盖 npc/ 目录**：najoast/rathena_npc_translate 的翻译来自旧版 rAthenaCN，NPC 坐标与当前版本不一致，导致NPC不显示。
2. **安全合并但编码错误**：将中文翻译文件以 UTF-8 写入，RO服务端读取后客户端用 GBK 显示乱码。

### 正确方案：结构保留 + 对话替换 + GBK 输出
- **保留英文文件结构**（坐标、精灵ID、脚本逻辑），仅替换 `mes "..."` 和 `select("...")` 对话字符串。
- **匹配策略**：优先用 `::label` 精确匹配 NPC，其次按文件内顺序位置匹配。
- **输出编码**：始终用 `file.encode('gbk', errors='replace')` + `wb` 模式写入，避免 Windows 换行符。
- **备份**：修改前先备份原英文文件到 `npc_backup_en/`，方便回滚。
- **pre-re/cities/ 问题**：这些文件只含 `duplicate()` 条目（无 mes），不需要单独翻译。
- **rAthena NPC 精灵ID**：可能是纯数字（`105`）或带宽高（`45,1,1`），正则要兼容两种格式。

### 工具
- `tools/npc_cn_translate.py`：一键下载 najoast 翻译、智能合并、输出 GBK
- 支持 `--dry-run`（不修改文件）和 `--no-backup`
- 翻译范围：cities/、airports/、battleground/、pre-re/cities/、re/cities/

### 关键数字（本次）
- 处理文件：58 个；跳过（无中文源）：8 个
- mes 替换：~4851 条；select 替换：~68 条
- prontera.txt：3426 个汉字，211 条中文 mes，GBK 编码验证通过
