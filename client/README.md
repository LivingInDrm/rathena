# RO 客户端文件管理

## 概述

本目录提供 RO 客户端的标准化管理框架，包括：
- 客户端方案配置档案（Profile）
- data.ini 模板
- NEMO/WARP 补丁清单
- 客户端校验和方案切换工具

## 当前方案

**方案A: 2021-11-03 Ragexe + 匹配版本 data.grf**

这是当前推荐的客户端方案，零服务端改动、最低风险。

## 目录结构

```
client/
├── README.md                    # 本文件
├── profiles/                    # 客户端配置档案
│   ├── 2021-11-03.json          # 方案A (当前激活)
│   ├── 2018-06-20.json.example  # 方案B 模板
│   └── 2020-05-20.json.example  # 方案C 模板
├── patches/                     # 补丁清单
│   └── 2021-11-03-patches.md    # 方案A 必须补丁
├── data-ini/                    # data.ini 模板
│   └── data.ini.template        # 标准 data.ini
└── scripts/                     # 管理脚本
    ├── verify_client.py          # 客户端完整性校验
    └── switch_profile.py         # 方案切换辅助
```

## 方案A 实施步骤

### 问题背景

当前使用 `2021-11-03_Ragexe_patched.exe` + 新版 kRO `data.grf`，由于新版 GRF 中的地图文件使用了更高版本的 RSW 格式，旧客户端无法解析，导致频繁崩溃（`0xc0000005` access violation）。

### 解决方案

替换 `data.grf` 为与 2021-11-03 客户端 EXE 匹配的版本。

### 操作步骤

#### 1. 下载匹配版本的 kRO 完整客户端

从以下地址下载 2021 年 11 月版 kRO 完整客户端：

- NEMO 下载页: http://nemo.herc.ws/downloads
- 直接链接: http://rofull.gnjoy.com/RAG_SETUP_211105.exe

> 文件约 2GB，下载需要一定时间。

#### 2. 提取 GRF 文件

安装或解压下载的完整客户端，提取以下文件：
- `data.grf`
- `rdata.grf`

#### 3. 替换客户端目录中的 GRF

将提取的 `data.grf` 和 `rdata.grf` 复制到你的客户端目录，替换现有文件。

> **重要**: 替换前请备份现有的 GRF 文件！

#### 4. 配置 data.ini

将 `client/data-ini/data.ini.template` 复制到客户端目录，重命名为 `data.ini`：

```ini
[Data]
0 = custom.grf    ; 中文资源/自定义覆盖（优先级最高）
1 = rdata.grf
2 = data.grf       ; kRO 原始数据
```

#### 5. 确认补丁

确保 EXE 已打上所有必须补丁，详见 `patches/2021-11-03-patches.md`。

关键补丁：
- `#71 Ignore Resource Errors` (必须)
- `#72 Ignore Missing Palette Error` (必须)
- `#214 Restore Model Culling` (必须)
- `#234 Ignore Lua Errors` (必须)

#### 6. 验证

运行校验工具确认客户端完整性：

```bash
python client/scripts/verify_client.py "你的客户端目录路径"
```

#### 7. 测试

启动客户端，测试以下场景：
- 登录并创建角色
- 传送到之前崩溃的地图（如 payon、morocc）
- 在多个地图间切换

### 如果仍有个别地图崩溃

使用 RSW 降级方案：

1. 下载 [GRF Editor v1.8.9.7](https://rathena.org/board/files/file/2766-grf-editor/)
2. 从 data.grf 中提取崩溃地图的 `.rsw` / `.gat` / `.gnd`
3. 用 GRF Editor 降级 RSW 版本
4. 将降级后的文件打入 `custom.grf`
5. 利用 data.ini 优先级自动覆盖

## 方案切换

如果方案A仍不稳定，可以切换到其他方案。

### 查看可用方案

```bash
python client/scripts/switch_profile.py --list
```

### 查看当前方案

```bash
python client/scripts/switch_profile.py --current
```

### 查看切换指导

```bash
python client/scripts/switch_profile.py --switch 2018-06-20
```

### 激活新方案

```bash
python client/scripts/switch_profile.py --activate 2018-06-20
```

## 可用方案对比

| 方案 | 客户端 | PACKETVER | 服务端改动 | 中文兼容 | 稳定性 |
|------|--------|-----------|-----------|---------|--------|
| **A (推荐)** | 2021-11-03 Ragexe | 20211103 | 无 | 最佳 | Tier 1 |
| B | 2018-06-20e RagexeRE | 20180620 | 需重编译 | 良好 | Tier 1 |
| C | 2020-05-20b Ragexe | 20200520 | 需重编译 | 可行 | Tier 2 |

## 工具与资源

| 工具 | 用途 | 来源 |
|------|------|------|
| WARP | 客户端补丁工具 | [github.com/Neo-Mind/WARP](https://github.com/Neo-Mind/WARP) |
| NEMO | 客户端补丁工具（经典） | [gitlab.com/4144/Nemo](https://gitlab.com/4144/Nemo) |
| GRF Editor | GRF 编辑、RSW 降级 | [rathena.org](https://rathena.org/board/files/file/2766-grf-editor/) |
| ROClientFullCN | 中文客户端资源 | [github.com/rAthenaCN/ROClientFullCN](https://github.com/rAthenaCN/ROClientFullCN) |

## 注意事项

- `*.grf` 和 `*.exe` 文件不纳入 Git 版本控制（已在 .gitignore 中排除）
- 客户端 EXE 和 GRF 文件需要手动下载和管理
- 切换方案时请务必备份现有文件
- 中文资源应打包到 `custom.grf` 中，利用 data.ini 优先级覆盖
