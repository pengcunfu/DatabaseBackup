# 本地构建并发布指南

本指南说明如何使用本地构建脚本快速编译和发布程序，无需等待 GitHub CI。

## 为什么使用本地构建？

- ✅ **速度快**: 本地构建速度比 CI 快 3-5 倍
- ✅ **利用缓存**: 重复构建时，Nuitka 会使用本地缓存
- ✅ **节省资源**: 减少 GitHub Actions 配额使用
- ✅ **更灵活**: 可以在本地测试和调试

## 前置要求

1. **Python 3.9+**
2. **Visual Studio 2022** (用于编译)
3. **Inno Setup 6** (用于创建安装程序)
4. **Git**
5. **Python 依赖**: 运行 `pip install -r requirements.txt`

## 安装 Inno Setup

下载地址: https://jrsoftware.org/isdl.php

建议安装到: `D:\App\Code\Tools\Inno Setup 6\`

或使用默认路径: `C:\Program Files (x86)\Inno Setup 6\`

## 使用步骤

### 1. 配置 GitHub Token (可选但推荐)

如果希望脚本自动上传到 GitHub Releases:

```powershell
# 1. 访问 https://github.com/settings/tokens
# 2. 点击 "Generate new token" -> "Generate new token (classic)"
# 3. 勾选 "repo" 权限
# 4. 生成 token 并复制

# 5. 设置环境变量 (临时，仅在当前窗口有效)
$env:GITHUB_TOKEN="your_token_here"

# 或者设置为永久环境变量
setx GITHUB_TOKEN "your_token_here"
```

### 2. 运行构建脚本

```powershell
# 方式1: 构建并自动发布
python scripts/build_and_release.py

# 方式2: 仅构建，手动发布
python scripts/build.py
python scripts/build_installer.py

# 然后手动上传 release/ 目录下的文件到 GitHub Releases
```

### 3. 脚本执行流程

脚本会自动执行以下步骤:

1. ✓ 检查前提条件 (Git、工作目录状态)
2. ✓ 编译应用程序 (使用 Nuitka)
3. ✓ 构建安装程序 (使用 Inno Setup)
4. ✓ 创建便携版压缩包
5. ✓ 准备发布文件
6. ✓ 创建并推送 Git 标签
7. ✓ 上传文件到 GitHub Releases (如果配置了 token)

### 4. 验证发布

访问 GitHub Releases 页面:
```
https://github.com/pengcunfu/DatabaseBackup/releases
```

## 构建产物

构建完成后，在 `release/` 目录下会生成:

```
release/
├── DatabaseBackup-Setup-0.0.5.exe    # 安装程序 (推荐)
├── DatabaseBackup-Portable-0.0.5.zip  # 便携版
└── DatabaseBackup.exe                 # 独立可执行文件
```

## 常见问题

### Q1: 编译速度慢怎么办?

A: 首次编译会比较慢，后续编译会使用缓存，速度会快很多。

### Q2: 上传到 GitHub 失败?

A: 检查以下几点:
- GITHUB_TOKEN 是否正确设置
- Token 是否有 `repo` 权限
- 网络连接是否正常

如果自动上传失败，可以手动上传:
1. 访问 https://github.com/pengcunfu/DatabaseBackup/releases/new
2. 选择标签 (如 v0.0.5)
3. 上传 `release/` 目录下的文件

### Q3: 如何跳过某些步骤?

A: 编辑 `scripts/build_and_release.py`，注释掉不需要的步骤。

### Q4: 构建失败怎么办?

A: 查看错误信息，常见问题:
- 缺少 Visual Studio
- Inno Setup 未安装或路径不对
- Python 依赖未安装
- 工作目录有未提交的更改

## 版本管理

使用 `release.py` 脚本管理版本号:

```powershell
# 交互式发布
python scripts/release.py

# 快速发布补丁版本 (0.0.5 -> 0.0.6)
python scripts/release.py --patch

# 快速发布次版本 (0.0.5 -> 0.1.0)
python scripts/release.py --minor

# 快速发布主版本 (0.0.5 -> 1.0.0)
python scripts/release.py --major

# 自定义版本号
python scripts/release.py --version 1.2.3
```

## 工作流对比

### GitHub CI 工作流 (慢)
1. 修改代码并提交
2. 推送到 GitHub
3. 等待 CI 启动 (1-2 分钟)
4. 等待编译完成 (10-20 分钟)
5. 等待安装程序构建 (1-2 分钟)
6. 自动发布

**总耗时: 15-25 分钟**

### 本地构建工作流 (快)
1. 修改代码
2. 本地运行 `python scripts/build_and_release.py`
3. 等待编译完成 (3-5 分钟)
4. 自动发布

**总耗时: 3-5 分钟** 🚀

## 最佳实践

1. **开发阶段**: 使用本地构建，快速迭代
2. **测试版本**: 本地构建并手动上传测试
3. **正式版本**: 本地构建后自动发布到 GitHub
4. **备份**: 将 `release/` 目录的文件备份到云存储

## 许多人协作

如果是团队开发:
1. 每个人都可以本地构建
2. 指定一人负责正式发布
3. 使用 GitHub Actions 作为备份构建方案

## 脚本功能对比

| 脚本 | 功能 | 速度 | 适用场景 |
|------|------|------|----------|
| build.py | 仅编译 | ⭐⭐⭐ | 快速测试 |
| build_installer.py | 仅构建安装程序 | ⭐⭐⭐⭐ | 快速打包 |
| build_and_release.py | 完整流程 | ⭐⭐⭐⭐⭐ | 正式发布 |
| release.py | 版本管理 + 发布 | ⭐⭐ | 版本发布 |

## 总结

使用本地构建可以:
- 节省 80% 的等待时间
- 提高开发效率
- 减少 CI 资源消耗
- 更灵活地控制发布流程

推荐工作流: 本地开发 → 本地构建测试 → 推送代码 → 本地正式发布
