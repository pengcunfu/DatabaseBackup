"""
Inno Setup安装程序构建脚本
用于生成DatabaseBackup工具的Windows安装包
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 配置区域
VERSION = "0.0.1"
YEAR = "2025"
AUTHOR = "pengcunfu"

# 项目信息
PRODUCT_NAME = "Database Backup Tool"
COMPANY_NAME = "PyDatabaseBackup"
DESCRIPTION = "MySQL Database Backup and Synchronization Tool"

# 目录配置
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
MAIN_DIST_DIR = DIST_DIR / "main.dist"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Inno Setup配置
ISS_FILE = SCRIPTS_DIR / "install.iss"
INSTALLER_NAME = f"DatabaseBackup-Setup-{VERSION}.exe"
EXPECTED_INSTALLER = OUTPUT_DIR / INSTALLER_NAME

# Inno Setup可执行文件路径（ISCC.exe）
# 常见安装位置
INNO_SETUP_PATHS = [
    r"D:\App\Code\Tools\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Inno Setup 6\ISCC.exe",
]


def find_inno_setup():
    """查找Inno Setup安装路径"""
    # 首先检查PATH环境变量
    for path in os.environ.get("PATH", "").split(os.pathsep):
        iscc_path = Path(path) / "ISCC.exe"
        if iscc_path.exists():
            return iscc_path

    # 检查常见安装位置
    for iscc_path in INNO_SETUP_PATHS:
        if Path(iscc_path).exists():
            return Path(iscc_path)

    return None


def check_prerequisites():
    """检查前提条件"""
    print("检查前提条件...")

    # 检查编译后的程序是否存在
    if not MAIN_DIST_DIR.exists():
        print(f"✗ 错误: 找不到编译后的程序目录")
        print(f"  期望路径: {MAIN_DIST_DIR}")
        print(f"  请先运行 scripts/build.py 进行编译")
        return False

    print(f"✓ 找到编译后的程序: {MAIN_DIST_DIR}")

    # 检查main.exe是否存在
    main_exe = MAIN_DIST_DIR / "main.exe"
    if not main_exe.exists():
        print(f"✗ 错误: 找不到 main.exe")
        print(f"  期望路径: {main_exe}")
        return False

    print(f"✓ 找到可执行文件: {main_exe}")

    # 检查Inno Setup脚本是否存在
    if not ISS_FILE.exists():
        print(f"✗ 错误: 找不到Inno Setup脚本文件")
        print(f"  期望路径: {ISS_FILE}")
        return False

    print(f"✓ 找到Inno Setup脚本: {ISS_FILE}")

    # 检查Inno Setup是否安装
    iscc_path = find_inno_setup()
    if not iscc_path:
        print(f"✗ 错误: 未找到Inno Setup 6")
        print(f"  请从以下地址下载并安装Inno Setup:")
        print(f"  https://jrsoftware.org/isdl.php")
        print(f"  当前检查的路径:")
        for path in INNO_SETUP_PATHS:
            print(f"    - {path}")
        return False

    print(f"✓ 找到Inno Setup: {iscc_path}")

    return True


def build_installer():
    """构建安装程序"""
    print("\n开始构建安装程序...")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ 输出目录: {OUTPUT_DIR}")

    # 如果旧的安装程序存在，先删除
    if EXPECTED_INSTALLER.exists():
        print(f"✓ 删除旧的安装程序...")
        EXPECTED_INSTALLER.unlink()

    # 查找Inno Setup编译器
    iscc_path = find_inno_setup()

    # 构建Inno Setup命令
    # Inno Setup使用/D参数传递宏定义
    cmd = [
        str(iscc_path),
        f"/dPRODUCT_VERSION={VERSION}",
        f"/dYEAR={YEAR}",
        f"/dAUTHOR={AUTHOR}",
        f"/dCOMPANY_NAME={COMPANY_NAME}",
        f"/dPRODUCT_NAME={PRODUCT_NAME}",
        f"/dDESCRIPTION={DESCRIPTION}",
        str(ISS_FILE)
    ]

    print(f"\n执行命令:")
    print(f"  {' '.join(cmd)}")
    print()

    try:
        # 执行Inno Setup编译
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='gbk',  # Inno Setup使用GBK编码
            errors='ignore'
        )

        # 显示输出
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # 检查结果
        if result.returncode == 0 and EXPECTED_INSTALLER.exists():
            file_size = EXPECTED_INSTALLER.stat().st_size / (1024 * 1024)  # MB
            print("\n")
            print("✓ 安装程序构建成功！")
            print(f"文件路径: {EXPECTED_INSTALLER}")
            print(f"文件大小: {file_size:.2f} MB")
            print(f"\n您现在可以:")
            print(f"1. 分发此安装程序给其他用户")
            print(f"2. 双击运行进行安装测试")
            return True
        else:
            print("\n")
            print("✗ 安装程序构建失败")
            print(f"返回码: {result.returncode}")
            if EXPECTED_INSTALLER.exists():
                print(f"警告: 虽然返回码非0，但安装程序文件已生成")
                return True
            return False

    except Exception as e:
        print(f"\n✗ 构建过程中发生错误: {e}")
        return False


def main():
    """主函数"""
    print(f"Inno Setup安装程序构建工具")
    print(f"产品: {PRODUCT_NAME}")
    print(f"版本: {VERSION}")

    # 检查前提条件
    if not check_prerequisites():
        print("\n✗ 前提条件检查失败，退出")
        sys.exit(1)

    # 构建安装程序
    if build_installer():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
