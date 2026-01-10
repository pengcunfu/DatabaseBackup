"""
本地构建并发布脚本
功能：
1. 本地编译程序（快速）
2. 本地构建安装程序
3. 创建 Git 标签
4. 上传构建好的文件到 GitHub Releases

优势：
- 本地构建速度快，无需等待 CI
- 利用本地缓存，重复构建更快
- 节省 GitHub Actions 配额
"""
import os
import sys
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# 导入统一的版本信息
sys.path.insert(0, str(Path(__file__).parent.parent))
from version import VERSION, PRODUCT_NAME, COMPANY_NAME, REPO_URL, GITHUB_USER, GITHUB_REPO


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_step(step_num, total_steps, message):
    """打印步骤信息"""
    print(f"\n{Colors.OKBLUE}[{step_num}/{total_steps}]{Colors.ENDC} {Colors.BOLD}{message}{Colors.ENDC}")
    print("-" * 60)


def print_success(message):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """打印错误信息"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def run_command(cmd, check=True, shell=True):
    """运行命令并返回结果"""
    print(f"  执行: {cmd}")
    result = subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True
    )

    if check and result.returncode != 0:
        print_error(f"命令执行失败，返回码: {result.returncode}")
        if result.stderr:
            print(f"  错误: {result.stderr}")
        sys.exit(1)

    return result


def check_prerequisites():
    """检查前提条件"""
    print_step(1, 7, "检查前提条件")

    # 检查是否在 Git 仓库中
    result = run_command("git rev-parse --git-dir", check=False)
    if result.returncode != 0:
        print_error("当前不在 Git 仓库中")
        return False
    print_success("Git 仓库检查通过")

    # 检查工作目录状态
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print_warning("工作目录有未提交的更改:")
        print(result.stdout)
        response = input("  是否继续？(y/N): ")
        if response.lower() != 'y':
            print_error("用户取消操作")
            return False
    else:
        print_success("工作目录干净")

    # 检查版本号
    print(f"  当前版本: {VERSION}")
    print_success("版本信息读取成功")

    return True


def build_application():
    """编译应用程序"""
    print_step(2, 7, "编译应用程序")

    print("  正在编译，这可能需要几分钟...")
    result = run_command("python scripts/build.py", check=False)

    if result.returncode != 0:
        print_error("编译失败")
        return False

    # 检查输出文件
    exe_path = Path("dist/main.dist/DatabaseBackup.exe")
    if not exe_path.exists():
        print_error(f"找不到编译输出: {exe_path}")
        return False

    file_size = exe_path.stat().st_size / (1024 * 1024)
    print_success(f"编译成功: DatabaseBackup.exe ({file_size:.2f} MB)")
    return True


def build_installer():
    """构建安装程序"""
    print_step(3, 7, "构建安装程序")

    print("  正在构建安装程序...")
    result = run_command("python scripts/build_installer.py", check=False)

    if result.returncode != 0:
        print_error("安装程序构建失败")
        return False

    # 检查输出文件
    installer_path = Path(f"output/DatabaseBackup-Setup-{VERSION}.exe")
    if not installer_path.exists():
        print_error(f"找不到安装程序: {installer_path}")
        return False

    file_size = installer_path.stat().st_size / (1024 * 1024)
    print_success(f"安装程序构建成功: DatabaseBackup-Setup-{VERSION}.exe ({file_size:.2f} MB)")
    return True


def create_portable_package():
    """创建便携版压缩包"""
    print_step(4, 7, "创建便携版压缩包")

    import zipfile

    zip_path = Path(f"release/DatabaseBackup-Portable-{VERSION}.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  正在创建: {zip_path}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        dist_dir = Path("dist/main.dist")
        for file in dist_dir.rglob('*'):
            if file.is_file():
                arcname = file.relative_to(dist_dir)
                zipf.write(file, arcname)
                print(f"    添加: {arcname}")

    file_size = zip_path.stat().st_size / (1024 * 1024)
    print_success(f"便携版创建成功: DatabaseBackup-Portable-{VERSION}.zip ({file_size:.2f} MB)")


def prepare_release_files():
    """准备发布文件"""
    print_step(5, 7, "准备发布文件")

    release_dir = Path("release")
    release_dir.mkdir(parents=True, exist_ok=True)

    files_to_copy = [
        (f"output/DatabaseBackup-Setup-{VERSION}.exe", f"release/DatabaseBackup-Setup-{VERSION}.exe"),
        ("dist/main.dist/DatabaseBackup.exe", "release/DatabaseBackup.exe"),
    ]

    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = Path(dst)

        if src_path.exists():
            import shutil
            shutil.copy2(src_path, dst_path)
            file_size = dst_path.stat().st_size / (1024 * 1024)
            print_success(f"复制: {dst_path.name} ({file_size:.2f} MB)")
        else:
            print_error(f"文件不存在: {src_path}")
            return False

    return True


def create_git_tag():
    """创建 Git 标签"""
    print_step(6, 7, "创建 Git 标签")

    tag_name = f"v{VERSION}"

    # 检查标签是否已存在
    result = run_command(f"git tag -l {tag_name}", check=False)
    if result.stdout.strip():
        print_warning(f"标签 {tag_name} 已存在")
        response = input("  是否删除旧标签并重新创建？(y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {tag_name}")
            run_command(f"git push origin :refs/tags/{tag_name}")
            print_success(f"已删除旧标签")
        else:
            print_error("取消操作")
            return False

    # 创建标签
    run_command(f"git tag -a {tag_name} -m \"Release {VERSION}\"")
    print_success(f"标签创建成功: {tag_name}")

    # 推送标签
    print(f"  推送标签到远程仓库...")
    run_command(f"git push origin {tag_name}")
    print_success("标签推送成功")

    return True


def upload_to_github():
    """上传到 GitHub Releases"""
    print_step(7, 7, "上传到 GitHub Releases")

    # 获取 GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print_warning("未找到 GITHUB_TOKEN 环境变量")
        print("  请创建 GitHub Personal Access Token:")
        print("  1. 访问: https://github.com/settings/tokens")
        print("  2. 创建新令牌，勾选 'repo' 权限")
        print("  3. 设置环境变量: set GITHUB_TOKEN=your_token")
        print("\n  跳过上传，您需要手动上传文件到 GitHub Releases")
        return False

    # 创建 Release
    tag_name = f"v{VERSION}"
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 检查 Release 是否已存在
    print(f"  检查 Release 是否存在...")
    response = requests.get(f"{api_url}/tags/{tag_name}", headers=headers)

    if response.status_code == 200:
        print_warning(f"Release {tag_name} 已存在")
        response = input("  是否删除旧 Release 并重新创建？(y/N): ")
        if response.lower() == 'y':
            # 删除旧 Release
            release_data = response.json()
            delete_url = release_data['url']
            response = requests.delete(delete_url, headers=headers)
            if response.status_code == 204:
                print_success("已删除旧 Release")
            else:
                print_error(f"删除失败: {response.text}")
                return False
        else:
            print_error("取消操作")
            return False

    # 创建新 Release
    print(f"  创建 Release: {tag_name}")

    release_data = {
        "tag_name": tag_name,
        "name": f"Release {VERSION}",
        "body": f"Release {VERSION} - {datetime.now().strftime('%Y-%m-%d')}",
        "draft": False,
        "prerelease": False
    }

    response = requests.post(api_url, json=release_data, headers=headers)

    if response.status_code != 201:
        print_error(f"创建 Release 失败: {response.text}")
        return False

    release_info = response.json()
    upload_url = release_info['upload_url'].replace('{?name,label}', '')
    print_success(f"Release 创建成功: {release_info['html_url']}")

    # 上传文件
    files_to_upload = [
        f"release/DatabaseBackup-Setup-{VERSION}.exe",
        f"release/DatabaseBackup-Portable-{VERSION}.zip",
        "release/DatabaseBackup.exe"
    ]

    for file_path in files_to_upload:
        file_path = Path(file_path)
        if not file_path.exists():
            print_warning(f"文件不存在，跳过: {file_path}")
            continue

        print(f"  上传: {file_path.name}...")

        with open(file_path, 'rb') as f:
            file_content = f.read()

        upload_url_with_name = f"{upload_url}?name={file_path.name}"
        upload_headers = {
            **headers,
            "Content-Type": "application/octet-stream"
        }

        response = requests.post(
            upload_url_with_name,
            data=file_content,
            headers=upload_headers
        )

        if response.status_code == 201:
            file_size = file_path.stat().st_size / (1024 * 1024)
            print_success(f"上传成功: {file_path.name} ({file_size:.2f} MB)")
        else:
            print_error(f"上传失败: {file_path.name}")
            print(f"  错误: {response.text}")

    return True


def main():
    """主函数"""
    print(f"{Colors.BOLD}本地构建并发布工具{Colors.ENDC}")
    print(f"项目: {PRODUCT_NAME}")
    print(f"版本: {VERSION}")
    print(f"仓库: {REPO_URL}")
    print("=" * 60)

    try:
        # 检查前提条件
        if not check_prerequisites():
            sys.exit(1)

        # 编译应用程序
        if not build_application():
            sys.exit(1)

        # 构建安装程序
        if not build_installer():
            sys.exit(1)

        # 创建便携版压缩包
        create_portable_package()

        # 准备发布文件
        if not prepare_release_files():
            sys.exit(1)

        # 创建 Git 标签
        if not create_git_tag():
            sys.exit(1)

        # 上传到 GitHub
        upload_success = upload_to_github()

        # 显示总结
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}{Colors.OKGREEN}构建完成！{Colors.ENDC}")
        print("\n发布文件:")
        print(f"  • release/DatabaseBackup-Setup-{VERSION}.exe (安装程序)")
        print(f"  • release/DatabaseBackup-Portable-{VERSION}.zip (便携版)")
        print(f"  • release/DatabaseBackup.exe (独立可执行文件)")

        if upload_success:
            print(f"\n{Colors.OKGREEN}已上传到 GitHub Releases:{Colors.ENDC}")
            print(f"  {REPO_URL}/releases/tag/v{VERSION}")
        else:
            print(f"\n{Colors.WARNING}请手动上传文件到 GitHub Releases:{Colors.ENDC}")
            print(f"  {REPO_URL}/releases/new?tag=v{VERSION}")

        print(f"\n查看构建状态:")
        print(f"  {REPO_URL}/actions")

    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print_error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
