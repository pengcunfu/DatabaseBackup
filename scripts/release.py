"""
自动化版本发布脚本
功能：
1. 检查工作目录状态
2. 更新版本号
3. 创建Git标签
4. 推送到GitHub（触发GitHub Actions自动构建和发布）
"""
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime


# ==================== 配置区域 ====================
# 项目信息
PROJECT_NAME = "Database Backup Tool"
COMPANY_NAME = "PyDatabaseBackup"
REPO_URL = "https://github.com/pengcunfu/DatabaseBackup"

# 版本文件路径
VERSION_FILES = [
    "scripts/build.py",
    "scripts/build_installer.py",
    "scripts/install.iss",
]

# Git配置
GIT_REMOTE = "origin"
GIT_BRANCH = "main"
# =================================================


class Version:
    """版本号管理类"""

    def __init__(self, major=1, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self):
        return f"Version({self.major}, {self.minor}, {self.patch})"

    @classmethod
    def from_string(cls, version_str):
        """从字符串解析版本号"""
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
        if match:
            major, minor, patch = match.groups()
            return cls(int(major), int(minor), int(patch))
        raise ValueError(f"Invalid version format: {version_str}")

    def bump_major(self):
        """增加主版本号"""
        return Version(self.major + 1, 0, 0)

    def bump_minor(self):
        """增加次版本号"""
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self):
        """增加补丁版本号"""
        return Version(self.major, self.minor, self.patch + 1)


def run_command(cmd, check=True, capture_output=True):
    """运行命令并返回结果"""
    print(f"执行: {cmd}")

    if capture_output:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if check and result.returncode != 0:
            print(f"错误: 命令执行失败")
            print(f"返回码: {result.returncode}")
            print(f"输出: {result.stdout}")
            print(f"错误: {result.stderr}")
            sys.exit(1)
        return result
    else:
        exit_code = os.system(cmd)
        if check and exit_code != 0:
            print(f"错误: 命令执行失败，返回码: {exit_code}")
            sys.exit(1)
        return None


def get_current_version():
    """从build.py获取当前版本号"""
    build_py = Path("scripts/build.py")
    if not build_py.exists():
        print(f"错误: 找不到 {build_py}")
        sys.exit(1)

    content = build_py.read_text(encoding='utf-8')
    match = re.search(r'VERSION\s*=\s*["\']([\d.]+)["\']', content)
    if match:
        return Version.from_string(match.group(1))

    print("错误: 无法从build.py中解析版本号")
    sys.exit(1)


def update_version_files(new_version):
    """更新所有文件中的版本号"""
    old_version = get_current_version()
    version_str = str(new_version)

    print(f"\n更新版本号: {old_version} -> {new_version}")

    for file_path in VERSION_FILES:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"警告: 文件不存在，跳过: {file_path}")
            continue

        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 更新版本号（支持多种格式）
        patterns = [
            (r'VERSION\s*=\s*["\'][\d.]+["\']', f'VERSION = "{version_str}"'),
            (r'PRODUCT_VERSION\s*=\s*["\'][\d.]+["\']', f'PRODUCT_VERSION = "{version_str}"'),
            (r'#define\s+PRODUCT_VERSION\s+"[\d.]+"', f'#define PRODUCT_VERSION "{version_str}"'),
            (r'AppVersion=[\d.]+', f'AppVersion={version_str}'),
            (r'VersionInfoVersion=[\d.]+', f'VersionInfoVersion={version_str}'),
            (r'VersionInfoProductVersion=[\d.]+', f'VersionInfoProductVersion={version_str}'),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"✓ 已更新: {file_path}")


def check_git_status():
    """检查Git工作目录状态"""
    print("\n检查Git状态...")

    # 检查是否有未提交的更改
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("警告: 工作目录有未提交的更改:")
        print(result.stdout)
        response = input("\n是否继续？(y/N): ")
        if response.lower() != 'y':
            print("取消操作")
            sys.exit(1)

    # 检查当前分支
    result = run_command(f"git rev-parse --abbrev-ref HEAD")
    current_branch = result.stdout.strip()
    print(f"当前分支: {current_branch}")

    if current_branch != GIT_BRANCH:
        print(f"警告: 当前不在 {GIT_BRANCH} 分支")
        response = input(f"是否切换到 {GIT_BRANCH} 分支？(y/N): ")
        if response.lower() == 'y':
            run_command(f"git checkout {GIT_BRANCH}")
        else:
            print("取消操作")
            sys.exit(1)

    # 检查是否有未推送的提交
    result = run_command(f"git log {GIT_REMOTE}/{GIT_BRANCH}..HEAD")
    if result.stdout.strip():
        print("警告: 有未推送的提交:")
        print(result.stdout)
        response = input("\n是否继续？(y/N): ")
        if response.lower() != 'y':
            print("取消操作")
            sys.exit(1)

    print("✓ Git状态检查通过")


def create_git_tag(version, message):
    """创建Git标签"""
    tag_name = f"v{version}"
    print(f"\n创建Git标签: {tag_name}")

    # 检查标签是否已存在
    result = run_command(f"git tag -l {tag_name}")
    if result.stdout.strip():
        print(f"警告: 标签 {tag_name} 已存在")
        response = input("是否删除旧标签并重新创建？(y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {tag_name}")
            run_command(f"git push {GIT_REMOTE} :refs/tags/{tag_name}")
        else:
            print("取消操作")
            sys.exit(1)

    # 创建标签
    run_command(f"git tag -a {tag_name} -m \"{message}\"")
    print(f"✓ 标签已创建: {tag_name}")


def push_to_remote(version):
    """推送到远程仓库"""
    print(f"\n推送到远程仓库")

    # 推送提交
    print("推送代码...")
    run_command(f"git push {GIT_REMOTE} {GIT_BRANCH}")

    # 推送标签（触发GitHub Actions）
    tag_name = f"v{version}"
    print(f"推送标签 {tag_name}...")
    run_command(f"git push {GIT_REMOTE} {tag_name}")

    print("✓ 推送完成")


def generate_release_notes(version):
    """生成Release说明"""
    date = datetime.now().strftime("%Y-%m-%d")

    notes = f"""## Release {version} - {date}

### 🚀 Features
- New features and improvements

### 🐛 Bug Fixes
- Bug fixes and optimizations

### 📦 Installation
Download the installer from the [Releases](../../releases) page.

### 🔧 Usage
See the [README](../../#readme) for usage instructions.

---

**Full Changelog**: https://github.com/pengcunfu/DatabaseBackup/compare/v{version}...HEAD
"""
    return notes


def interactive_release():
    """交互式发布流程"""
    print(f"{PROJECT_NAME} - 自动化版本发布工具")

    # 获取当前版本
    current_version = get_current_version()
    print(f"\n当前版本: {current_version}")

    # 选择版本更新类型
    print("\n选择版本更新类型:")
    print("1. 主版本 (major) - {0}.x.x -> {1}.0.0".format(
        current_version.major, current_version.major + 1))
    print("2. 次版本 (minor) - x.{0}.x -> x.{1}.0".format(
        current_version.minor, current_version.minor + 1))
    print("3. 补丁 (patch) - x.x.{0} -> x.x.{1}".format(
        current_version.patch, current_version.patch + 1))
    print("4. 自定义版本号")

    choice = input("\n请选择 (1-4): ").strip()

    if choice == "1":
        new_version = current_version.bump_major()
    elif choice == "2":
        new_version = current_version.bump_minor()
    elif choice == "3":
        new_version = current_version.bump_patch()
    elif choice == "4":
        version_str = input("请输入新版本号 (格式: x.y.z): ").strip()
        try:
            new_version = Version.from_string(version_str)
        except ValueError:
            print("错误: 无效的版本号格式")
            sys.exit(1)
    else:
        print("无效选择")
        sys.exit(1)

    print(f"\n新版本号: {new_version}")

    # 输入Release说明
    print("\n请输入Release说明（留空使用默认模板）:")
    release_message = input().strip()
    if not release_message:
        release_message = f"Release {new_version}"

    # 确认
    print("\n")
    print("发布信息预览:")
    print(f"  版本号: {current_version} -> {new_version}")
    print(f"  说明: {release_message}")

    response = input("\n确认发布？(y/N): ")
    if response.lower() != 'y':
        print("取消操作")
        sys.exit(0)

    # 检查Git状态
    check_git_status()

    # 更新版本号文件
    update_version_files(new_version)

    # 提交版本号更改
    print("\n提交版本号更改...")
    run_command(f"git add scripts/")
    run_command(f'git commit -m "Bump version to {new_version}"')

    # 创建Git标签
    create_git_tag(new_version, release_message)

    # 推送到远程
    push_to_remote(new_version)

    # 显示成功信息
    print("\n")
    print("✓ 版本发布成功！")
    print(f"版本号: {new_version}")
    print(f"标签: v{new_version}")
    print(f"\nGitHub Actions正在构建和发布...")
    print(f"查看构建状态: {REPO_URL}/actions")
    print(f"查看Release: {REPO_URL}/releases/tag/v{new_version}")


def quick_release(version_type="patch"):
    """快速发布（无需交互）"""
    current_version = get_current_version()
    print(f"当前版本: {current_version}")

    # 自动递增版本
    if version_type == "major":
        new_version = current_version.bump_major()
    elif version_type == "minor":
        new_version = current_version.bump_minor()
    else:
        new_version = current_version.bump_patch()

    print(f"新版本: {new_version}")

    # 检查Git状态
    check_git_status()

    # 更新版本号
    update_version_files(new_version)

    # 提交
    run_command(f"git add scripts/")
    run_command(f'git commit -m "Bump version to {new_version}"')

    # 创建标签
    create_git_tag(new_version, f"Release {new_version}")

    # 推送
    push_to_remote(new_version)

    print(f"\n✓ 版本 {new_version} 发布成功！")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="自动化版本发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式发布
  python scripts/release.py

  # 快速发布补丁版本
  python scripts/release.py --patch

  # 快速发布次版本
  python scripts/release.py --minor

  # 快速发布主版本
  python scripts/release.py --major

  # 自定义版本号
  python scripts/release.py --version 2.0.0
        """
    )

    parser.add_argument(
        "--patch", "-p",
        action="store_true",
        help="快速发布补丁版本 (x.x.X -> x.x.(X+1))"
    )

    parser.add_argument(
        "--minor", "-m",
        action="store_true",
        help="快速发布次版本 (x.X.x -> x.(X+1).0)"
    )

    parser.add_argument(
        "--major", "-M",
        action="store_true",
        help="快速发布主版本 (X.x.x -> (X+1).0.0)"
    )

    parser.add_argument(
        "--version", "-v",
        type=str,
        metavar="X.Y.Z",
        help="指定版本号"
    )

    args = parser.parse_args()

    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        if args.version:
            # 自定义版本号
            version = Version.from_string(args.version)
            current_version = get_current_version()
            print(f"当前版本: {current_version}")
            print(f"新版本: {version}")

            check_git_status()
            update_version_files(version)
            run_command(f"git add scripts/")
            run_command(f'git commit -m "Bump version to {version}"')
            create_git_tag(version, f"Release {version}")
            push_to_remote(version)
            print(f"\n✓ 版本 {version} 发布成功！")

        elif args.major:
            quick_release("major")
        elif args.minor:
            quick_release("minor")
        elif args.patch:
            quick_release("patch")
        else:
            # 交互式发布
            interactive_release()

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
