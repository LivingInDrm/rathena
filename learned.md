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
- 支持 `--dry-run`（不修改文件）、`--no-backup`、`--force-download`
- 翻译范围（扩展后）：cities/、airports/、battleground/、events/、guild/、guild2/、instances/、jobs/、kafras/、merchants/、mobs/、other/、quests/、warps/、custom/、pre-re/{airports,guides,jobs,kafras,merchants,mobs,other,quests,warps}/、re/{airports,guides,guild,instances,jobs,kafras,merchants,mobs,other,quests,warps,custom}/
- **zip 缓存**：首次运行下载整个 repo zip（~928 文件），缓存到 `tmp/cn_cache/`，后续运行秒级完成
- `tools/run_translate.py`：静默包装器，将输出重定向到 `tmp/translate_run2.log`

### 关键数字（扩展后）
- 处理文件：862 个；跳过（无中文源）：199 个
- mes 替换：77,704 条；select 替换：1,834 条
- 实际有中文的 NPC 文件：142 个（najoast 源库本身只有 446/928 文件含中文）

### najoast 源库覆盖率（实际含中文的文件比例）
- airports: 100%, battleground: 100%, cities: 92%, guild: 95%, guild2: 100%
- instances: 100%, kafras: 100%, mobs: 100%, merchants: 82%
- jobs: 3%（仅1/33文件），quests: 33%, events: 27%, warps: 0%

### 中文化资源汇总（网络调研）
- **NPC脚本**：najoast/rathena_npc_translate 是目前最好的来源（历史快照，非实时同步）
- **客户端物品名**：rAthenaCN/ROClientFullCN（含 iteminfo.lua、skillinfo 等 Lua 文件）
- **完整客户端工具**：PandasWS/LeeClient（自动化中文化，但不支持2020+客户端）
- **无完整翻译**：Pandas 和 rAthenaCN 官方均确认不存在完整的 NPC 脚本中文翻译

### 重要教训
- Python 在 Windows 上写文件时，`&&` 链式命令可能因输出为空而不执行后续命令，需分开执行
- 背景进程输出过大（exit code 2）不代表失败，需检查实际文件内容
- 翻译工具运行时输出量极大（3000行日志），必须重定向到文件
- 方案调研要区分“服务端 NPC 脚本汉化”和“客户端资源汉化”；`ROClientFullCN`、`LeeClient` 主要补客户端，不替代 NPC 脚本翻译
