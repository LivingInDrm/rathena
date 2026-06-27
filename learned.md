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
- 方案调研要区分"服务端 NPC 脚本汉化"和"客户端资源汉化"；`ROClientFullCN`、`LeeClient` 主要补客户端，不替代 NPC 脚本翻译
- 运营中的中文 RO 服首页通常不公开服务端内核；调研结论必须区分"站点实锤样本"和"基于中文 rAthena 生态的保守推断"

## 客户端稳定性 (2026-06)

### 崩溃根因
- **data.grf 版本与客户端 EXE 不匹配是最常见的崩溃原因**：kRO 持续更新 data.grf，新版 RSW 格式老客户端无法解析
- `0xc0000005` access violation 通常是客户端尝试加载不支持的资源格式导致的内存访问错误
- `payon.rsw` 等地图在 kRO 更新后可能被重制，与老客户端不兼容

### 关键教训
- **客户端 EXE 日期必须与 data.grf 版本匹配**：用 2021-11-03 的 EXE 就应该用 2021年11月左右的 data.grf
- **NEMO 补丁 #71 Ignore Resource Errors 是必打补丁**：让缺失/不兼容资源不崩溃只报警告
- **自定义 GRF 排在 data.ini 第一位**：优先加载自定义/修复的资源，覆盖 data.grf 中的问题文件
- **RSW 降级可用 GRF Editor 完成**：个别问题地图可提取 RSW/GAT/GND 文件降级版本后重新打入 GRF
- **PACKETVER 在 src/config/packets.hpp 定义**，自定义覆盖放 `src/custom/defines_pre.hpp`
- **20211103 自动启用 PACKETVER_RE（Sakray 模式）**：因为落在 20200902-20211118 区间内

## AI 翻译工具链 (2026-06)

### 设计决策
- **复用 `npc_cn_translate.py` 的 `parse_blocks()` 解析器**：已验证的 NPC 脚本解析器，避免重复造轮子
- **JSON 中间格式**：结构化、支持断点续传和校验，比纯文本更可靠
- **按 NPC block 粒度翻译**：保持对话上下文连贯，比逐行翻译质量更高
- **无 pip 依赖**：仅用 Python 标准库 + OpenAI REST API（urllib），降低部署门槛
- **术语表独立 JSON**：可持续维护，被 translate.py 的 system prompt 引用
- **验证器前置于回填**：pipeline 中 validate 在 apply 之前，有 error 则阻止回填

### 关键教训
- **翻译粒度选择**：逐行翻译会丢失上下文（NPC 对话有前后文关联），按 block 翻译效果更好
- **GBK 编码校验必须在回填前做**：AI 可能生成 GBK 不支持的字符（如某些 emoji 或罕见汉字）
- **select 选项数校验**：`:` 分隔符数量必须与原文一致，否则游戏逻辑会错乱
- **颜色代码 `^RRGGBB` 保留**：AI 容易把颜色代码当作文本翻译或丢弃，需在 prompt 中强调并在验证中检查
- **断点续传设计**：大量文件翻译时 API 可能中断，每 5 个文件保存 checkpoint，重跑时跳过已完成的

### Code Review 教训
- **高字节 ≠ 中文**：`is_file_translated()` 不能用 `byte > 0x80` 判断，latin-1 特殊字符也有高字节，必须解码后用中文字符正则检测
- **重试耗尽必须抛异常**：`return []` 会导致下游静默回退到原文，掩盖 API 失败
- **429 最后一次重试也要 raise**：否则 sleep 后落入循环末尾返回空结果
- **跨文件重复函数要抽取到公共模块**：`read_npc_file`、`backup_file` 在多处定义会导致修一处漏一处
- **GBK 编码校验要报告所有错误字符**：`UnicodeEncodeError` 只报第一个，需逐字符检查
- **正则模式要避免误匹配**：`@\w+` 会匹配 `.@var` 中的 `@var`，需用 `(?<!\.)@\w+`；`#\w+` 会匹配颜色代码，需用 `(?<!\^)#\w+`
- **argparse `store_true` + `default=True` 是无效参数**：该 flag 永远为 True，应删除
- **AI 返回的 markdown 代码块要用正则提取**：简单删首尾行不够健壮，应用 `re.match` 提取 fence 内容

## 客户端文件管理框架 (2026-06)

### 设计教训
- **方案管理用 Profile JSON 而非硬编码**：多方案并存时，用结构化配置档案记录每个方案的完整参数（EXE、PACKETVER、GRF 来源、补丁列表），方便切换和对比。
- **切换工具只生成指导不执行破坏性操作**：客户端文件替换涉及 GB 级二进制文件，自动化风险高，工具应只提供步骤指导。
- **GRF/EXE 不入 Git**：二进制大文件用 .gitignore 排除，通过文档和脚本管理。
- **data.ini 模板化**：标准 GRF 加载顺序（custom.grf > rdata.grf > data.grf）应作为模板提供，避免每次手动配置出错。
