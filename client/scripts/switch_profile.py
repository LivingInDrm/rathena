#!/usr/bin/env python3
"""
RO 客户端方案切换辅助工具

列出可用的客户端方案，显示当前激活方案，
并在切换方案时提供详细的操作指导。

用法:
    python switch_profile.py --list
    python switch_profile.py --current
    python switch_profile.py --switch <方案名>
    python switch_profile.py --help

示例:
    python switch_profile.py --list
    python switch_profile.py --switch 2018-06-20
"""

import argparse
import json
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.dirname(SCRIPT_DIR)
PROFILES_DIR = os.path.join(CLIENT_DIR, "profiles")
DATA_INI_DIR = os.path.join(CLIENT_DIR, "data-ini")


def load_profiles():
    """加载所有配置档案"""
    profiles = {}
    if not os.path.isdir(PROFILES_DIR):
        return profiles

    for filename in os.listdir(PROFILES_DIR):
        if not filename.endswith(".json") and not filename.endswith(".json.example"):
            continue

        filepath = os.path.join(PROFILES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                profile = json.load(f)
            # 提取方案名（去掉 .json 或 .json.example 后缀）
            name = filename
            if name.endswith(".json.example"):
                name = name[: -len(".json.example")]
            elif name.endswith(".json"):
                name = name[: -len(".json")]
            profiles[name] = {
                "data": profile,
                "filename": filename,
                "filepath": filepath,
                "is_example": filename.endswith(".example"),
            }
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 无法加载 {filename}: {e}")
    return profiles


def list_profiles():
    """列出所有可用方案"""
    profiles = load_profiles()
    if not profiles:
        print("未找到任何配置档案")
        print(f"请检查目录: {PROFILES_DIR}")
        return

    print("\n可用的客户端方案:")
    print("=" * 70)

    for name, info in sorted(profiles.items()):
        data = info["data"]
        status = data.get("status", "unknown")
        display_name = data.get("name", name)
        description = data.get("description", "")

        if status == "active":
            marker = " [当前激活]"
        elif info["is_example"]:
            marker = " [模板]"
        else:
            marker = ""

        print(f"\n  {name}{marker}")
        print(f"    名称: {display_name}")
        print(f"    说明: {description}")

        packetver = data.get("packetver", {})
        if isinstance(packetver, dict):
            print(f"    PACKETVER: {packetver.get('value', 'N/A')}")
        else:
            print(f"    PACKETVER: {packetver}")

        server_changes = data.get("server_changes", "unknown")
        print(f"    服务端改动: {server_changes}")

    print("\n" + "=" * 70)
    print(f"共 {len(profiles)} 个方案")
    print()


def show_current():
    """显示当前激活的方案"""
    profiles = load_profiles()
    active = None
    for name, info in profiles.items():
        if info["data"].get("status") == "active":
            active = (name, info)
            break

    if not active:
        print("当前没有激活的方案")
        print("请使用 --switch <方案名> 激活一个方案")
        return

    name, info = active
    data = info["data"]
    print(f"\n当前激活方案: {data.get('name', name)}")
    print(f"  PACKETVER: {data.get('packetver', {}).get('value', 'N/A')}")
    print(f"  客户端 EXE: {data.get('client_exe', {}).get('filename', 'N/A')}")
    print(f"  服务端改动: {data.get('server_changes', 'N/A')}")

    # 显示 GRF 信息
    grf_info = data.get("data_grf", {})
    if grf_info:
        print(f"  GRF 来源: {grf_info.get('source', 'N/A')}")
        urls = grf_info.get("download_urls", [])
        if urls:
            print("  下载地址:")
            for url in urls:
                print(f"    - {url}")
    print()


def switch_profile(target_name):
    """切换到指定方案（只生成指导，不执行破坏性操作）"""
    profiles = load_profiles()

    if target_name not in profiles:
        print(f"错误: 未找到方案 '{target_name}'")
        print("可用方案:")
        for name in sorted(profiles.keys()):
            print(f"  - {name}")
        return False

    target = profiles[target_name]
    target_data = target["data"]

    # 找到当前激活的方案
    current_name = None
    current_info = None
    for name, info in profiles.items():
        if info["data"].get("status") == "active":
            current_name = name
            current_info = info
            break

    if current_name == target_name:
        print(f"方案 '{target_name}' 已经是当前激活方案")
        return True

    print("\n" + "=" * 70)
    print(f"  方案切换指导")
    print(f"  从: {current_name or '(无)'} -> 到: {target_name}")
    print("=" * 70)

    # 步骤 1: 下载客户端
    print("\n--- 步骤 1: 准备客户端文件 ---")
    grf_info = target_data.get("data_grf", {})
    print(f"  需要下载: {grf_info.get('source', 'N/A')}")
    urls = grf_info.get("download_urls", [])
    if urls:
        print("  下载地址:")
        for url in urls:
            print(f"    {url}")
    required_files = grf_info.get("required_files", [])
    if required_files:
        print(f"  必需文件: {', '.join(required_files)}")

    # 步骤 2: 客户端 EXE
    print("\n--- 步骤 2: 客户端 EXE ---")
    exe_info = target_data.get("client_exe", {})
    print(f"  需要 EXE: {exe_info.get('filename', 'N/A')}")
    print(f"  补丁工具: {exe_info.get('patch_tool', 'NEMO 或 WARP')}")

    # 步骤 3: 补丁
    print("\n--- 步骤 3: 打补丁 ---")
    patches = target_data.get("required_patches", {})
    if isinstance(patches, dict):
        critical = patches.get("critical", [])
        recommended = patches.get("recommended", [])
        if critical:
            print("  必须补丁:")
            for p in critical:
                print(f"    #{p['id']} {p['name']} - {p['reason']}")
        if recommended:
            print("  推荐补丁:")
            for p in recommended:
                print(f"    #{p['id']} {p['name']} - {p['reason']}")
    else:
        print("  请参考 client/patches/ 目录下的补丁清单")

    # 步骤 4: 服务端配置
    print("\n--- 步骤 4: 服务端配置 ---")
    server_changes = target_data.get("server_changes", "none")
    if server_changes == "none":
        print("  无需修改服务端配置")
    else:
        print(f"  {server_changes}")
        packetver = target_data.get("packetver", {})
        if isinstance(packetver, dict):
            override_file = packetver.get("override_file", "")
            override_content = packetver.get("override_content", "")
            if override_file and override_content:
                print(f"  修改文件: {override_file}")
                print(f"  添加内容: {override_content}")
                print("  然后重新编译服务端 (MSBuild / make)")

    # 步骤 5: data.ini
    print("\n--- 步骤 5: 配置 data.ini ---")
    print("  将 client/data-ini/data.ini.template 复制到客户端目录")
    print("  重命名为 data.ini")

    # 步骤 6: 更新 profile 状态
    print("\n--- 步骤 6: 更新配置档案 ---")
    print("  完成上述步骤后，运行以下命令激活方案:")
    print(f"  python switch_profile.py --activate {target_name}")

    print("\n" + "=" * 70)
    print("  注意: 以上步骤需要手动执行，本工具不会自动修改任何文件")
    print("=" * 70 + "\n")
    return True


def activate_profile(target_name):
    """激活指定方案（更新 JSON 文件中的 status 字段）"""
    profiles = load_profiles()

    if target_name not in profiles:
        print(f"错误: 未找到方案 '{target_name}'")
        return False

    target = profiles[target_name]

    # 如果是 .example 文件，需要先复制为 .json
    if target["is_example"]:
        new_filename = f"{target_name}.json"
        new_filepath = os.path.join(PROFILES_DIR, new_filename)
        shutil.copy2(target["filepath"], new_filepath)
        print(f"已从模板创建配置文件: {new_filename}")
        target["filepath"] = new_filepath
        target["filename"] = new_filename

    # 将所有其他方案设为 inactive
    for name, info in profiles.items():
        if name == target_name:
            continue
        if info["data"].get("status") == "active":
            info["data"]["status"] = "inactive"
            filepath = info["filepath"]
            # 只更新非 example 文件
            if not info["is_example"]:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(info["data"], f, ensure_ascii=False, indent=2)
                print(f"已将 {name} 设为 inactive")

    # 激活目标方案
    target["data"]["status"] = "active"
    with open(target["filepath"], "w", encoding="utf-8") as f:
        json.dump(target["data"], f, ensure_ascii=False, indent=2)
    print(f"已激活方案: {target['data'].get('name', target_name)}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="RO 客户端方案切换辅助工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python switch_profile.py --list              # 列出所有方案
  python switch_profile.py --current           # 显示当前方案
  python switch_profile.py --switch 2018-06-20 # 查看切换指导
  python switch_profile.py --activate 2018-06-20 # 激活方案
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="列出所有可用方案")
    group.add_argument("--current", action="store_true", help="显示当前激活方案")
    group.add_argument("--switch", metavar="NAME", help="显示切换到指定方案的操作指导")
    group.add_argument("--activate", metavar="NAME", help="激活指定方案 (更新配置文件)")

    args = parser.parse_args()

    if args.list:
        list_profiles()
    elif args.current:
        show_current()
    elif args.switch:
        switch_profile(args.switch)
    elif args.activate:
        activate_profile(args.activate)


if __name__ == "__main__":
    main()
