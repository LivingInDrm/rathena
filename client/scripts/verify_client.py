#!/usr/bin/env python3
"""
RO 客户端完整性校验工具

校验客户端目录是否包含必要文件，data.ini 配置是否正确，
GRF 文件大小是否在合理范围。

用法:
    python verify_client.py <客户端目录>
    python verify_client.py --help

示例:
    python verify_client.py "C:\\Games\\RO"
    python verify_client.py D:\\RO_Client
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.dirname(SCRIPT_DIR)
PROFILES_DIR = os.path.join(CLIENT_DIR, "profiles")

# GRF 文件大小合理范围 (bytes)
MIN_GRF_SIZE = 100 * 1024 * 1024       # 100 MB (最小合理 GRF)
MAX_GRF_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB (最大合理 GRF)

# data.ini 中 GRF 的推荐加载顺序
RECOMMENDED_GRF_ORDER = ["custom.grf", "rdata.grf", "data.grf"]


class VerifyResult:
    """校验结果收集器"""

    def __init__(self):
        self.passed = []
        self.warnings = []
        self.errors = []

    def ok(self, msg):
        self.passed.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    @property
    def success(self):
        return len(self.errors) == 0

    def print_report(self):
        print("\n" + "=" * 60)
        print("  RO 客户端完整性校验报告")
        print("=" * 60)

        if self.passed:
            print(f"\n[通过] ({len(self.passed)} 项)")
            for msg in self.passed:
                print(f"  + {msg}")

        if self.warnings:
            print(f"\n[警告] ({len(self.warnings)} 项)")
            for msg in self.warnings:
                print(f"  ! {msg}")

        if self.errors:
            print(f"\n[错误] ({len(self.errors)} 项)")
            for msg in self.errors:
                print(f"  X {msg}")

        print("\n" + "-" * 60)
        if self.success:
            print("  结果: 通过")
            if self.warnings:
                print(f"  (有 {len(self.warnings)} 个警告，建议检查)")
        else:
            print(f"  结果: 失败 ({len(self.errors)} 个错误)")
        print("-" * 60 + "\n")


def load_active_profile():
    """加载当前激活的客户端配置档案"""
    if not os.path.isdir(PROFILES_DIR):
        return None

    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json") and not filename.endswith(".example"):
            filepath = os.path.join(PROFILES_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                if profile.get("status") == "active":
                    return profile
            except (json.JSONDecodeError, IOError):
                continue
    return None


def check_directory(client_dir, result):
    """检查客户端目录是否存在"""
    if not os.path.isdir(client_dir):
        result.error(f"客户端目录不存在: {client_dir}")
        return False
    result.ok(f"客户端目录存在: {client_dir}")
    return True


def check_exe(client_dir, result, profile=None):
    """检查客户端 EXE 是否存在"""
    exe_files = [f for f in os.listdir(client_dir)
                 if f.lower().endswith(".exe") and "ragexe" in f.lower()]

    if not exe_files:
        # 也检查 patched 的 exe
        exe_files = [f for f in os.listdir(client_dir)
                     if f.lower().endswith(".exe") and "patched" in f.lower()]

    if not exe_files:
        result.error("未找到 Ragexe EXE 文件")
        return

    for exe in exe_files:
        exe_path = os.path.join(client_dir, exe)
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        result.ok(f"找到 EXE: {exe} ({size_mb:.1f} MB)")

    if profile:
        expected_exe = profile.get("client_exe", {}).get("filename", "")
        if expected_exe and not any(expected_exe.lower() in e.lower() for e in exe_files):
            result.warn(f"未找到配置档案指定的 EXE: {expected_exe}")


def check_grf_files(client_dir, result, profile=None):
    """检查 GRF 文件是否存在且大小合理"""
    required_grfs = ["data.grf", "rdata.grf"]
    if profile:
        required_grfs = profile.get("data_grf", {}).get("required_files", required_grfs)

    for grf_name in required_grfs:
        grf_path = os.path.join(client_dir, grf_name)
        if not os.path.isfile(grf_path):
            result.error(f"缺少必要 GRF 文件: {grf_name}")
            continue

        size = os.path.getsize(grf_path)
        size_mb = size / (1024 * 1024)
        size_gb = size / (1024 * 1024 * 1024)

        if size < MIN_GRF_SIZE:
            result.error(f"{grf_name} 文件过小 ({size_mb:.1f} MB)，可能已损坏")
        elif size > MAX_GRF_SIZE:
            result.warn(f"{grf_name} 文件异常大 ({size_gb:.2f} GB)")
        else:
            if size_gb >= 1:
                result.ok(f"{grf_name} 存在 ({size_gb:.2f} GB)")
            else:
                result.ok(f"{grf_name} 存在 ({size_mb:.0f} MB)")

    # 检查 custom.grf（可选）
    custom_grf = os.path.join(client_dir, "custom.grf")
    if os.path.isfile(custom_grf):
        size_mb = os.path.getsize(custom_grf) / (1024 * 1024)
        result.ok(f"custom.grf 存在 ({size_mb:.1f} MB)")
    else:
        result.warn("未找到 custom.grf（中文资源 GRF），中文显示可能不完整")


def check_data_ini(client_dir, result):
    """检查 data.ini 配置"""
    ini_path = os.path.join(client_dir, "data.ini")
    if not os.path.isfile(ini_path):
        result.error("缺少 data.ini 文件")
        result.warn("请参考 client/data-ini/data.ini.template 创建")
        return

    try:
        with open(ini_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(ini_path, "r", encoding="gbk", errors="replace") as f:
            content = f.read()

    result.ok("data.ini 存在")

    # 解析 GRF 加载顺序
    grf_entries = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(";") or line.startswith("//") or line.startswith("[") or not line:
            continue
        if "=" in line:
            parts = line.split("=", 1)
            try:
                idx = int(parts[0].strip())
                grf_name = parts[1].strip()
                grf_entries[idx] = grf_name
            except ValueError:
                continue

    if not grf_entries:
        result.error("data.ini 中未找到 GRF 配置条目")
        return

    # 检查 data.grf 是否在列表中
    grf_names = list(grf_entries.values())
    if not any("data.grf" in g for g in grf_names):
        result.error("data.ini 中未配置 data.grf")

    # 检查加载顺序：custom.grf 应在 data.grf 之前
    custom_idx = None
    data_idx = None
    for idx, name in grf_entries.items():
        if "custom" in name.lower():
            custom_idx = idx
        if name.strip().lower() == "data.grf":
            data_idx = idx

    if custom_idx is not None and data_idx is not None:
        if custom_idx < data_idx:
            result.ok("GRF 加载顺序正确 (custom.grf 优先于 data.grf)")
        else:
            result.warn("GRF 加载顺序可能有误: custom.grf 应排在 data.grf 之前")
    elif custom_idx is None:
        result.warn("data.ini 中未配置 custom.grf")

    # 显示当前配置
    for idx in sorted(grf_entries.keys()):
        result.ok(f"  data.ini [{idx}] = {grf_entries[idx]}")


def check_system_files(client_dir, result):
    """检查 System 目录和关键文件"""
    system_dir = os.path.join(client_dir, "System")
    if not os.path.isdir(system_dir):
        result.warn("未找到 System/ 目录")
        return

    result.ok("System/ 目录存在")

    # 检查关键 Lua 文件
    key_files = [
        "iteminfo.lub",
        "skillinfoz.lub",
        "msgstringtable.txt",
    ]
    for fname in key_files:
        fpath = os.path.join(system_dir, fname)
        if os.path.isfile(fpath):
            result.ok(f"  System/{fname} 存在")


def main():
    parser = argparse.ArgumentParser(
        description="RO 客户端完整性校验工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python verify_client.py "C:\\Games\\RO"
  python verify_client.py D:\\RO_Client
  python verify_client.py --profile 2021-11-03 "C:\\Games\\RO"
        """,
    )
    parser.add_argument("client_dir", nargs="?", help="客户端根目录路径")
    parser.add_argument(
        "--profile",
        help="指定配置档案名称 (默认使用激活的档案)",
    )
    args = parser.parse_args()

    if not args.client_dir:
        parser.print_help()
        print("\n错误: 请指定客户端目录路径")
        sys.exit(1)

    client_dir = os.path.abspath(args.client_dir)

    # 加载配置档案
    profile = None
    if args.profile:
        profile_path = os.path.join(PROFILES_DIR, f"{args.profile}.json")
        if os.path.isfile(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            print(f"使用配置档案: {profile.get('name', args.profile)}")
        else:
            print(f"警告: 未找到配置档案 {profile_path}，使用默认检查")
    else:
        profile = load_active_profile()
        if profile:
            print(f"使用激活的配置档案: {profile.get('name', 'unknown')}")

    result = VerifyResult()

    # 执行各项检查
    if not check_directory(client_dir, result):
        result.print_report()
        sys.exit(1)

    check_exe(client_dir, result, profile)
    check_grf_files(client_dir, result, profile)
    check_data_ini(client_dir, result)
    check_system_files(client_dir, result)

    result.print_report()
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
