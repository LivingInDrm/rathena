# RO 客户端稳定性调研

## 当前问题

当前使用 `2021-11-03_Ragexe_patched.exe` + kRO `data.grf`，存在以下问题：
- 频繁崩溃，错误码 `0xc0000005`（access violation）
- `payon.rsw` 等地图资源加载失败
- 整体稳定性差，影响开发和测试

## 崩溃根因分析

### 1. RSW 版本不匹配（最可能的主因）

**核心问题**：kRO 持续更新 `data.grf`，新版 GRF 中的地图文件（`.rsw`/`.gat`/`.gnd`）使用了更高版本的 RSW 格式。而 `2021-11-03 Ragexe` 客户端无法解析这些新格式文件，导致 `C3dWorldRes :: Unsupported Version` 错误和 access violation 崩溃。

**社区报告的典型案例**：
- `payon.rsw`、`morocc.rsw` 等经典地图在 kRO 更新后被重制，老客户端加载崩溃
- `airplane.rsw`、`aldebaran` 等地图也有类似报告
- `nif_dun01`、`nif_dun02` 等新地图使用了 RSM2 模型格式，老客户端完全无法加载

**验证方法**：如果崩溃主要发生在传送到特定地图时，基本可确认是此问题。

### 2. 客户端 EXE 与 data.grf 版本脱节

- `2021-11-03 Ragexe` 发布时间：2021年11月
- kRO `data.grf` 在之后持续更新（2022-2025），加入新地图、新模型格式
- 使用与 EXE 版本差距过大的 `data.grf` 是不稳定的根源

### 3. NEMO/WARP 补丁不完整

- `2021-11-03_Ragexe_1635824489` 在 NEMO 上仅 284/361 个补丁成功
- 缺少关键补丁（如 `Ignore Resource Errors`、`Restore Model Culling`）可能导致崩溃而非优雅降级

## 可选客户端方案对比

### 方案 A：修复当前 2021-11-03 客户端（推荐优先尝试）

**做法**：保留 `2021-11-03 Ragexe`，但替换 `data.grf` 为与该客户端匹配的版本。

| 项目 | 说明 |
|---|---|
| 客户端 EXE | 继续使用 `2021-11-03_Ragexe_patched.exe` |
| data.grf | 使用 2021年11月前后的 kRO full client（`RAG_SETUP_211105.exe`）中的 data.grf |
| 来源 | `http://nemo.herc.ws/downloads` 或 `http://rofull.gnjoy.com/RAG_SETUP_211105.exe` |
| PACKETVER | 保持 `20211103`（当前 rAthena 默认值） |
| 服务端改动 | 无需改动 |
| 优点 | 零服务端改动、rAthena 默认支持、社区支持最多 |
| 风险 | 需要重新下载 ~2GB 完整客户端 |

**关键补丁列表**（NEMO/WARP 必须打）：
- `Ignore Resource Errors`（#71）——让缺失资源不崩溃只报警告
- `Ignore Missing Palette Error`（#72）
- `Restore Model Culling`（#214）——修复模型渲染问题
- `Ignore Lua Errors`（#234）
- `Read Data Folder First`（#35）——方便用本地文件覆盖 GRF 中的问题资源
- `Enable Multiple GRFs`（#49）

**RSW 降级方案**：如果仍有个别地图崩溃，可用 GRF Editor 将新版 RSW 降级：
- 工具：[GRF Editor v1.8.9.7](https://rathena.org/board/files/file/2766-grf-editor/)
- 参考：[Map RSW Downgrade Tutorial](https://www.youtube.com/watch?v=A37mVFm2RlM)
- 操作：提取问题地图的 `.rsw`/`.gat`/`.gnd`，用 GRF Editor 降级 RSW 版本，重新打入自定义 GRF

### 方案 B：降级到 2018-06-20 RagexeRE

**适用场景**：追求经典 Pre-Renewal 手感，且不需要 2021 客户端的新功能。

| 项目 | 说明 |
|---|---|
| 客户端 EXE | `2018-06-20eRagexeRE` |
| PACKETVER | `20180620` |
| data.grf | 使用 2018 年版 kRO full client（`kRO_FullClient_20180813`）中的 data.grf |
| 服务端改动 | 需改 PACKETVER 并重新编译 |
| 优点 | Pre-Renewal 社区最广泛使用、稳定性经验证、更经典的 UI 风格 |
| 缺点 | robe costume 显示不如 2021、部分新功能不可用、需重新编译服务端 |

**PACKETVER 修改方法**：
```cpp
// 在 src/custom/defines_pre.hpp 中添加：
#define PACKETVER 20180620
```
然后重新编译服务端。

### 方案 C：降级到 2020-05-20b Ragexe

**适用场景**：介于 2018 和 2021 之间的折中方案。

| 项目 | 说明 |
|---|---|
| 客户端 EXE | `2020-05-20bRagexe` |
| PACKETVER | `20200520` |
| 来源 | [Ragnarok Offline Pre-Renewal Pack](https://ragnarokoffline.github.io/) 使用此版本 |
| 优点 | 较新的功能、有现成 WARP profile、有 Pre-Renewal Pack 参考 |
| 缺点 | 非 rAthena 默认、社区案例较 2021/2018 少 |

### 方案 D：升级到 2025 客户端（不推荐当前使用）

| 项目 | 说明 |
|---|---|
| 客户端 EXE | `2025-06-04 Ragexe` 或 `2025-07-16 Ragexe` |
| 工具 | 需要 WARP 2025 版本 |
| 优点 | 最新功能、解决所有旧版 RSW 问题 |
| 缺点 | 尚在开发中、稳定性未验证、可能有未修复的包错误、社区经验极少 |

## 与中文化的兼容性考量

| 方案 | 中文化兼容性 |
|---|---|
| **A（修复 2021）** | 最佳。`ROClientFullCN` 直接支持，当前 NPC 中文化（GBK 输出）已验证 |
| **B（2018）** | 良好。`ROClientFullCN` 和 `LeeClient` 都支持 2018 客户端 |
| **C（2020）** | 可行。需要额外适配 Lua 文件路径 |
| **D（2025）** | 未知。中文资源包尚未适配 |

## 推荐实施方案

### 第一步：确认崩溃原因（立即可做）

1. 启用 NEMO 补丁 `#71 Ignore Resource Errors`，观察是否仍然崩溃
2. 如果变为"报警告但不崩溃"→ 确认是 RSW/资源版本问题
3. 如果仍然崩溃 → 可能是 EXE 本身问题或 data.grf 严重不匹配

### 第二步：替换匹配版本的 data.grf（推荐方案 A）

1. 下载 2021 年 11 月版 kRO 完整客户端
2. 提取其中的 `data.grf` 和 `rdata.grf`
3. 替换当前客户端目录中的对应文件
4. 保留当前 `2021-11-03_Ragexe_patched.exe` 和自定义 GRF（中文资源等）

### 第三步：处理个别问题地图

1. 如果 Pre-Renewal 需要的旧版地图（如旧版 payon、morocc）在新 data.grf 中被替换
2. 用 GRF Editor 从旧版 data.grf 中提取这些地图的 `.rsw`/`.gat`/`.gnd`
3. 打入自定义 GRF，让 `data.ini` 优先加载自定义 GRF

### 备选：如果方案 A 仍不稳定

考虑切换到方案 B（`2018-06-20 RagexeRE`），这需要：
1. 修改 `src/custom/defines_pre.hpp` 设置 `PACKETVER 20180620`
2. 重新编译服务端（`MSBuild` / `make`）
3. 下载 2018 版 kRO 完整客户端
4. 重新打补丁（NEMO/WARP）
5. 重新适配中文客户端资源

## 工具与资源汇总

| 工具 | 用途 | 来源 |
|---|---|---|
| **WARP** | 客户端补丁工具（NEMO 后继） | [github.com/Neo-Mind/WARP](https://github.com/Neo-Mind/WARP) |
| **NEMO** | 客户端补丁工具（经典） | [gitlab.com/4144/Nemo](https://gitlab.com/4144/Nemo) |
| **GRF Editor** | GRF 文件编辑、RSW 降级 | [rathena.org/board/files/file/2766-grf-editor/](https://rathena.org/board/files/file/2766-grf-editor/) |
| **ROenglishRE** | 英文翻译项目（含 Pre-Renewal 支持） | [github.com/llchrisll/ROenglishRE](https://github.com/llchrisll/ROenglishRE) |
| **ROClientFullCN** | 中文客户端资源 | [github.com/rAthenaCN/ROClientFullCN](https://github.com/rAthenaCN/ROClientFullCN) |
| **kRO Full Client** | 官方韩服完整客户端 | [nemo.herc.ws/downloads](http://nemo.herc.ws/downloads) |

## 关键技术参数

### 当前服务端 PACKETVER 配置

```
文件：src/config/packets.hpp 第16行
默认值：#define PACKETVER 20211103
覆盖位置：src/custom/defines_pre.hpp（当前为空）
```

### PACKETVER_RE 自动判定逻辑

```cpp
// src/config/packets.hpp 第22行
#if ( PACKETVER > 20151104 && PACKETVER < 20180704 ) || ( PACKETVER >= 20200902 && PACKETVER <= 20211118 )
    #define PACKETVER_RE
#endif
```

注意：`20211103` 落在第二个区间内，因此当前自动启用了 `PACKETVER_RE`（Sakray 模式）。

### data.ini 推荐配置

```ini
0 = custom.grf    ; 中文资源、自定义覆盖
1 = rdata.grf
2 = data.grf       ; kRO 原始数据（版本需匹配客户端 EXE）
```

优先级：编号小的 GRF 覆盖编号大的。中文资源放 `custom.grf` 并排第一位。

## 社区稳定性评级（综合多个 rAthena 论坛帖子）

| 等级 | 客户端 | PACKETVER | 说明 |
|---|---|---|---|
| **Tier 1** | 2021-11-03 Ragexe | 20211103 | rAthena 默认、最多社区支持 |
| **Tier 1** | 2018-06-20e RagexeRE | 20180620 | Pre-Renewal 经典选择、最广泛验证 |
| **Tier 2** | 2020-04-01 RagexeRE | 20200401 | Renewal 常用 |
| **Tier 2** | 2020-05-20b Ragexe | 20200520 | 有现成 Pre-Renewal Pack |
| **Tier 2** | 2015-11-04a Ragexe | 20151104 | 极经典、功能最少 |
| **Tier 3** | 2025-06-04 Ragexe | 20250604 | 前沿、不推荐生产 |

## 结论

**当前崩溃最可能的原因是 kRO data.grf 版本与 2021-11-03 客户端 EXE 不匹配**（新版 GRF 包含老客户端无法解析的 RSW 格式）。

**推荐方案**：先尝试方案 A（替换匹配版本的 data.grf + 确保关键 NEMO 补丁到位），这是零服务端改动、最低风险的修复路径。如果方案 A 仍不稳定，再考虑降级到 2018 客户端（方案 B）。
