#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka 构建脚本
用于将 PyDatabaseBackup 项目编译为独立的可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 项目配置
PROJECT_NAME = "PyDatabaseBackup"
MAIN_SCRIPT = "main.py"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"

# Nuitka 编译选项
NUITKA_OPTIONS = [
    "--standalone",  # 独立模式，包含所有依赖
    "--windows-console-mode=attach",  # Windows 控制台模式
    "--enable-plugin=pyside6",  # 启用 PySide6 插件
    "--include-package=pymysql",  # 包含 pymysql 包
    "--include-package=yaml",  # 包含 yaml 包
    "--include-package=cryptography",  # 包含 cryptography 包
    "--include-data-file=config.yaml=config.yaml",  # 包含配置文件
    "--include-data-file=README.md=README.md",  # 包含 README
    f"--output-dir={OUTPUT_DIR}",  # 输出目录
    "--output-filename=DatabaseBackup.exe",  # 输出文件名
    "--assume-yes-for-downloads",  # 自动确认下载
    "--show-progress",  # 显示进度
    "--show-memory",  # 显示内存使用
    "--remove-output",  # 编译前删除旧的输出
]

# Windows 特定选项
if sys.platform == "win32":
    # 检查图标文件是否存在
    icon_path = "resource/icon.png"
    if os.path.exists(icon_path):
        NUITKA_OPTIONS.append(f"--windows-icon-from-ico={icon_path}")
    
    NUITKA_OPTIONS.extend([
        "--windows-company-name=PyDatabaseBackup",
        "--windows-product-name=Database Backup Tool",
        "--windows-file-version=1.0.0.0",
        "--windows-product-version=1.0.0.0",
        "--windows-file-description=数据库备份同步工具",
    ])

# 性能优化选项
OPTIMIZATION_OPTIONS = [
    "--lto=yes",  # 链接时优化
    "--jobs=8",  # 并行编译任务数（增加以加快编译）
]

# 快速编译选项
FAST_BUILD_OPTIONS = [
    "--nofollow-imports",  # 不跟踪所有导入（加快编译）
]

def print_separator(char="=", length=60):
    """打印分隔线"""
    print(char * length)

def print_step(step_name):
    """打印步骤信息"""
    print_separator()
    print(f">>> {step_name}")
    print_separator()

def check_nuitka_installed():
    """检查 Nuitka 是否已安装"""
    print_step("检查 Nuitka 安装")
    try:
        result = subprocess.run(
            ["python", "-m", "nuitka", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Nuitka 版本信息:")
            print(result.stdout.strip())
            return True
        else:
            print("错误: Nuitka 未安装")
            print("请运行: pip install nuitka")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"错误: Nuitka 未安装 - {e}")
        print("请运行: pip install nuitka")
        return False

def check_dependencies():
    """检查项目依赖"""
    print_step("检查项目依赖")
    
    if not os.path.exists("requirements.txt"):
        print("警告: requirements.txt 文件不存在")
        return True
    
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            requirements = f.read().strip().split("\n")
        
        print(f"发现 {len(requirements)} 个依赖:")
        for req in requirements:
            if req.strip():
                print(f"  - {req}")
        
        return True
    except Exception as e:
        print(f"读取 requirements.txt 失败: {e}")
        return False

def clean_build_dirs():
    """清理构建目录"""
    print_step("清理构建目录")
    
    dirs_to_clean = [BUILD_DIR, OUTPUT_DIR]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"删除目录: {dir_name}")
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ {dir_name} 已删除")
            except Exception as e:
                print(f"  ✗ 删除失败: {e}")
        else:
            print(f"  - {dir_name} 不存在，跳过")

def check_main_script():
    """检查主脚本是否存在"""
    print_step("检查主脚本")
    
    if not os.path.exists(MAIN_SCRIPT):
        print(f"错误: 主脚本 {MAIN_SCRIPT} 不存在")
        return False
    
    print(f"✓ 找到主脚本: {MAIN_SCRIPT}")
    return True

def build_with_nuitka(optimize=True, fast_mode=True):
    """使用 Nuitka 构建项目"""
    print_step("开始 Nuitka 编译")
    
    # 构建命令
    cmd = ["python", "-m", "nuitka"] + NUITKA_OPTIONS
    
    # 添加优化选项
    if optimize:
        cmd.extend(OPTIMIZATION_OPTIONS)
        print("已启用优化选项")
    
    # 添加快速编译选项
    if fast_mode:
        cmd.extend(FAST_BUILD_OPTIONS)
        print("已启用快速编译模式")
    
    # 添加主脚本
    cmd.append(MAIN_SCRIPT)
    
    # 打印完整命令
    print("\n编译命令:")
    print(" ".join(cmd))
    print()
    
    # 执行编译
    try:
        print("开始编译... (这可能需要几分钟)")
        print_separator("-")
        
        result = subprocess.run(cmd, check=True)
        
        print_separator("-")
        print("✓ 编译成功!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_separator("-")
        print(f"✗ 编译失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n编译被用户中断")
        return False

def show_build_results():
    """显示构建结果"""
    print_step("构建结果")
    
    if not os.path.exists(OUTPUT_DIR):
        print("输出目录不存在")
        return
    
    # 查找生成的可执行文件
    exe_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(('.exe', '.bin', '')):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                exe_files.append((file_path, file_size))
    
    if exe_files:
        print("生成的可执行文件:")
        for file_path, file_size in exe_files:
            size_mb = file_size / (1024 * 1024)
            print(f"  - {file_path}")
            print(f"    大小: {size_mb:.2f} MB")
    else:
        print("未找到可执行文件")
    
    # 显示输出目录内容
    print(f"\n输出目录 ({OUTPUT_DIR}) 内容:")
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path):
            print(f"  [DIR]  {item}")
        else:
            size = os.path.getsize(item_path)
            print(f"  [FILE] {item} ({size:,} bytes)")

def copy_additional_files():
    """复制额外的必要文件到输出目录"""
    print_step("复制额外文件")
    
    files_to_copy = ["config.yaml", "README.md"]
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            dest = os.path.join(OUTPUT_DIR, file_name)
            try:
                shutil.copy2(file_name, dest)
                print(f"  ✓ 复制: {file_name} -> {dest}")
            except Exception as e:
                print(f"  ✗ 复制失败 {file_name}: {e}")
        else:
            print(f"  - {file_name} 不存在，跳过")

def clean_build_artifacts():
    """清理构建产生的临时文件，只保留 dist 目录"""
    print_step("清理构建临时文件")
    
    # 需要清理的目录和文件
    items_to_clean = [
        BUILD_DIR,
        "main.build",
        "main.dist",
        "main.onefile-build",
    ]
    
    # 清理 .pyi 和其他 Nuitka 生成的文件
    for item in os.listdir("."):
        if item.endswith(".pyi") or item.startswith("main.") and item != "main.py":
            items_to_clean.append(item)
    
    cleaned_count = 0
    for item in items_to_clean:
        if os.path.exists(item):
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"  ✓ 删除目录: {item}")
                else:
                    os.remove(item)
                    print(f"  ✓ 删除文件: {item}")
                cleaned_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败 {item}: {e}")
    
    if cleaned_count == 0:
        print("  - 没有需要清理的文件")
    else:
        print(f"\n  已清理 {cleaned_count} 个项目")

def main():
    """主函数"""
    print_separator("=")
    print(f"  {PROJECT_NAME} - Nuitka 构建脚本")
    print_separator("=")
    print()
    
    # 检查 Nuitka
    if not check_nuitka_installed():
        return 1
    
    # 检查依赖
    if not check_dependencies():
        print("警告: 依赖检查失败，但继续构建")
    
    # 检查主脚本
    if not check_main_script():
        return 1
    
    # 自动清理旧的构建目录
    clean_build_dirs()
    
    # 开始构建（自动启用优化和快速编译）
    print()
    if not build_with_nuitka(optimize=True, fast_mode=True):
        print("\n构建失败!")
        return 1
    
    # 复制额外文件
    copy_additional_files()
    
    # 显示结果
    show_build_results()
    
    # 清理构建临时文件
    clean_build_artifacts()
    
    print()
    print_separator("=")
    print("  构建完成!")
    print_separator("=")
    print()
    print(f"可执行文件位于: {OUTPUT_DIR}/")
    print(f"所有临时文件已清理，只保留 {OUTPUT_DIR} 目录")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n构建过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
