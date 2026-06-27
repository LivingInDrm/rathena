# EP13.2 中文化技术设计

## 目标
- 基于 `rAthena master` 搭建 `EP13.2 / Encounter with the Unknown / Pre-Renewal` 服务端。
- 核心要求是“尽可能完整的中文体验”，但不能牺牲当前 `rAthena master` 的脚本结构、坐标、精灵 ID 与逻辑兼容性。

## 设计原则
- **服务端脚本结构以当前 rAthena 为准**：不直接覆盖 `npc/` 原文件。
- **翻译仅替换文本层**：优先替换 `mes`、`select`、`caption` 等对话字符串。
- **客户端显示兼容优先**：NPC 中文脚本输出必须使用 `GBK` 编码。
- **Pre-Renewal 与 EP13.2 并行校验**：凡涉及 `pre-re/`、13.2 区域、任务链、传送与相关提示，都要单独验证。
- **可持续补全**：现成资源不完整时，应采用“历史翻译底座 + 自动抽取 + 人工/AI 校对”的增量流程。

## 方案分层

### 1. 服务端 NPC 文本层
- 基础文本源：`najoast/rathena_npc_translate`
- 应用方式：使用仓库内的 `tools/npc_cn_translate.py` 做“结构保留、对话替换、GBK 输出”的安全合并
- 禁止方式：直接用旧汉化仓库覆盖当前 `npc/`

### 2. 客户端中文资源层
- 客户端资源基线：`rAthenaCN/ROClientFullCN`
- 用途：物品名、技能名、系统 Lua、部分文本资源
- 备注：这是客户端资源方案，不等价于完整服务端 NPC 脚本翻译

### 3. 客户端打包/补丁辅助层
- 参考工具：`PandasWS/LeeClient`
- 用途：完整客户端资源整合、版本切换、按钮/UI 资源处理
- 限制：并非现成的 EP13.2 服务端 NPC 中文化方案

### 4. 未翻译文本补全层
- 以当前 `rAthena master` 脚本为源抽取可翻译文本
- 自动生成待翻译清单
- 用 AI/人工翻译回填
- 再经过脚本校验、GBK 编码校验、13.2 流程回归

## 不采纳的方案
- **直接使用旧 rAthena 中文分支替换当前 master**
  - 原因：脚本年代老、与当前 master 差异大，极易破坏 NPC 坐标、脚本头与逻辑。
- **只做客户端汉化**
  - 原因：只能解决 UI、物品、技能与部分资源，不解决服务端 NPC 对话缺失。
- **等待现成完整仓库**
  - 原因：当前公开资料显示不存在完整、持续维护、可直接用于 `rAthena master + EP13.2 pre-re` 的中文 NPC 全量方案。

## 推荐实施顺序
1. 保持 `rAthena master` 作为服务端主线。
2. 使用现有安全合并工具导入 `najoast` 可用翻译。
3. 用覆盖率工具统计未汉化区域，优先补 `quests`、`jobs`、`warps`、`pre-re`、13.2 相关链路。
4. 配套接入 `ROClientFullCN` 解决客户端中文资源。
5. 对未覆盖文本建立增量翻译流水线，持续补齐。

### 5. 客户端文件管理层
- 管理目录：`client/`
- 配置档案：`client/profiles/*.json` 记录各方案的完整配置（EXE、PACKETVER、GRF 来源、补丁列表）
- data.ini 模板：`client/data-ini/data.ini.template` 标准 GRF 加载顺序
- 补丁清单：`client/patches/` 各方案必须的 NEMO/WARP 补丁
- 管理脚本：`client/scripts/verify_client.py`（完整性校验）、`client/scripts/switch_profile.py`（方案切换）
- 当前激活方案：方案A（2021-11-03 Ragexe + 匹配版本 data.grf）
- 方案切换原则：通过 Profile JSON 管理，切换时只生成指导不自动执行破坏性操作
- GRF/EXE 等二进制文件不纳入 Git（已在 .gitignore 排除）