# 数据库备份同步工具

<div align="center">

**版本 1.0.0** | **基于 PySide6** | **MIT 许可**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)](https://pyside6.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

功能强大的 MySQL 数据库备份、同步和管理工具

[在线文档](docs/) | [更新日志](CHANGELOG.md) | [问题反馈](https://github.com/pengcunfu/DatabaseBackup/issues)

</div>

---

## 📋 目录

- [项目概述](#项目概述)
- [主要功能](#主要功能)
- [项目结构](#项目结构)
- [安装指南](#安装指南)
- [使用方法](#使用方法)
- [配置说明](#配置说明)
- [构建打包](#构建打包)
- [版本更新](#版本更新)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## 项目概述

本项目是一个功能强大的 MySQL 数据库管理工具，支持数据库备份、同步、SQL 导入导出以及定时任务调度。使用 PySide6 Widgets 构建现代化图形界面，提供直观易用的操作体验。

### ✨ 特性亮点

- 🚀 **高性能**: 基于 PySide6 原生控件，响应迅速
- 🔒 **安全可靠**: 密码加密存储，详细日志记录
- ⏰ **定时任务**: 支持 Cron 表达式的定时调度
- 🔄 **双向同步**: 本地 ⇄ 远程数据库双向同步
- 📦 **自动更新**: 内置自动更新检查和下载
- 🎨 **现代化界面**: 简洁直观的用户界面

---

## 主要功能

### 核心功能

- ✅ **数据库同步**
  - 远程数据库 → 本地数据库
  - 本地数据库 → 远程数据库
  - 支持表结构复制和数据同步

- ✅ **SQL 文件管理**
  - 导出数据库为 SQL 文件
  - 从 SQL 文件导入数据
  - 执行自定义 SQL 脚本

- ✅ **定时任务调度**
  - 基于 APScheduler 的任务调度
  - 支持 Cron 表达式
  - 任务启用/禁用管理
  - 实时任务状态监控

- ✅ **多数据库配置**
  - 支持配置多个数据库连接
  - 配置加密存储
  - 快速切换数据库

### 新增功能

- ✨ **自动更新** (v1.0.0+)
  - 启动时自动检查更新
  - 一键下载和安装新版本
  - 显示更新说明和版本对比

- 📦 **Windows 安装程序**
  - 使用 Inno Setup 6 生成
  - 专业的安装向导
  - 完整的卸载支持

---

## 项目结构

```
DatabaseBackup/
├── app/                              # 应用程序核心模块
│   ├── __init__.py                   # 包初始化
│   ├── main_window.py                # 主窗口界面
│   ├── config_dialog.py              # 数据库配置对话框
│   ├── config_manager.py             # 配置管理器
│   ├── db_config.py                  # 数据库配置类
│   ├── db_sync.py                    # 数据库同步核心
│   ├── task_scheduler.py             # 定时任务调度器
│   ├── task_dialog.py                # 任务对话框
│   ├── scheduler_config.py           # 任务配置
│   ├── update_manager.py             # 更新管理器
│   └── update_config.py              # 更新配置
│
├── resources/                        # 资源文件
│   ├── config.yaml                   # 默认配置
│   ├── icon.png                      # 应用图标
│   └── icon.ico                      # Windows 图标
│
├── scripts/                          # 构建和发布脚本
│   ├── build.py                      # Nuitka 编译脚本
│   ├── build_installer.py            # Inno Setup 构建脚本
│   ├── install.iss                   # Inno Setup 配置
│   └── release.py                    # 版本发布脚本
│
├── docs/                             # 文档
│   └── UPDATE_FEATURE.md             # 更新功能文档
│
├── .github/                          # GitHub 配置
│   └── workflows/
│       └── python-app-release.yml    # CI/CD 工作流
│
├── logs/                             # 日志目录（运行时创建）
├── dist/                             # 编译输出目录
├── output/                           # 安装程序输出目录
│
├── main.py                           # 程序入口
├── requirements.txt                  # Python 依赖
├── config.yaml                       # 配置文件（可选）
├── db_config.json                    # 旧版配置（兼容）
├── CHANGELOG.md                      # 更新日志
└── README.md                         # 本文件
```

---

## 安装指南

### 环境要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11, Linux, macOS
- **数据库**: MySQL 5.7+ 或 MariaDB 10.3+

### 安装步骤

#### 方式1：使用安装程序（推荐）

1. 从 [Releases](https://github.com/pengcunfu/DatabaseBackup/releases) 下载最新安装程序
2. 运行 `DatabaseBackup-Setup-1.0.0.exe`
3. 按照安装向导完成安装
4. 启动程序：开始菜单 → Database Backup Tool

#### 方式2：从源码安装

```bash
# 1. 克隆仓库
git clone https://github.com/pengcunfu/DatabaseBackup.git
cd DatabaseBackup

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

### 依赖包

```txt
PySide6>=6.0.0
PyMySQL>=1.0.0
cryptography>=41.0.0
APScheduler>=3.10.0
PyYAML>=6.0
```

---

## 使用方法

### 图形界面模式

```bash
python main.py
```

### 主要界面说明

#### 1. 手动同步 Tab
- 选择同步模式（远程到本地 / 本地到远程 / 导出SQL / 导入SQL / 执行SQL）
- 选择数据库配置
- 点击"开始同步"按钮
- 查看日志输出和进度

#### 2. 定时任务 Tab
- 查看所有定时任务
- 添加新任务（设置 Cron 表达式）
- 启用/禁用任务
- 查看任务执行日志

#### 3. 菜单栏

**文件菜单**
- 配置数据库：管理数据库连接
- 退出：关闭程序

**工具菜单**
- 清空日志：清空日志输出

**帮助菜单**
- 检查更新：手动检查新版本
- 关于：查看程序信息

---

## 配置说明

### 配置文件位置

- **Windows**: `%USERPROFILE%\.databasebackup\config.yaml`
- **Linux/macOS**: `~/.databasebackup/config.yaml`

### 配置文件格式 (config.yaml)

```yaml
databases:
  local:
    host: localhost
    port: 3306
    username: root
    password: encrypted_base64_password
    database: robot_management_local

  remote:
    host: 192.168.1.100
    port: 3306
    username: root
    password: encrypted_base64_password
    database: robot_management

sync_options:
  exclude_tables:
    - user_sessions
    - login_attempts
  drop_target_tables: true

scheduled_tasks:
  - name: "每日备份"
    enabled: true
    cron: "0 2 * * *"  # 每天凌晨2点
    source: "remote"
    target: "local"
    sync_type: "远程到本地"
```

### 密码加密

密码使用 Base64 编码加密存储：
```python
import base64
password = "mypassword"
encrypted = base64.b64encode(password.encode()).decode()
```

---

## 构建打包

### 编译为 Windows 可执行文件

```bash
# 1. 使用 Nuitka 编译
python scripts/build.py

# 2. 生成安装程序
python scripts/build_installer.py
```

**输出文件**：
- `dist/main.dist/` - 编译后的程序
- `output/DatabaseBackup-Setup-1.0.0.exe` - 安装程序

### 构建要求

- **Windows 10/11**
- **Python 3.9+**
- **Visual Studio Build Tools**（用于 Nuitka）
- **Inno Setup 6**（用于生成安装程序）

### Nuitka 参数说明

```bash
--standalone              # 独立可执行文件
--windows-console-mode=disable  # 禁用控制台
--plugin-enable=pyside6  # 启用 PySide6 插件
--assume-yes-for-downloads  # 自动确认下载依赖
--include-package=apscheduler  # 包含 APScheduler
--output-dir=dist        # 输出目录
```

---

## 版本更新

### 自动更新

程序内置自动更新功能：

1. **自动检查**：程序启动时自动检查更新（每7天）
2. **手动检查**：菜单 → 帮助 → 检查更新
3. **更新提示**：发现新版本时显示更新说明
4. **一键安装**：下载完成后可直接安装

### 更新配置

配置文件：`~/.databasebackup/update_config.json`

```json
{
  "auto_check": true,        // 是否自动检查
  "check_interval": 7,       // 检查间隔（天）
  "last_check": "",          // 上次检查时间
  "skipped_version": "",     // 跳过的版本
  "beta_updates": false      // 是否接收测试版
}
```

详细说明：[更新功能文档](docs/UPDATE_FEATURE.md)

---

## 开发指南

### 项目架构

```
main.py (入口)
    ↓
MainWindow (主窗口)
    ├── ConfigManager (配置管理)
    ├── DatabaseSynchronizer (数据库同步)
    ├── TaskScheduler (任务调度)
    └── UpdateManager (更新管理)
```

### 代码规范

- 使用 PEP 8 代码风格
- 添加类型提示（Type Hints）
- 编写文档字符串（Docstrings）
- 使用 logging 模块记录日志

### 添加新功能

1. 在 `app/` 目录创建新模块
2. 在 `main_window.py` 中集成
3. 更新 `requirements.txt`（如有新依赖）
4. 编写测试和文档

---

## 常见问题

### Q: 编译时提示缺少 Visual Studio？
**A**: 需要安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Q: 如何修改默认配置？
**A**: 编辑 `resources/config.yaml` 或通过界面修改

### Q: 定时任务不执行？
**A**: 检查 Cron 表达式格式，确保程序保持运行

### Q: 如何禁用自动更新？
**A**: 修改 `~/.databasebackup/update_config.json` 中的 `auto_check` 为 `false`

### Q: 程序无法连接数据库？
**A**:
1. 检查数据库服务是否运行
2. 验证主机地址和端口
3. 确认用户名和密码
4. 检查防火墙设置

---

## 更新日志

### v1.0.0 (2025-01-10)

**新功能**
- ✨ 添加自动更新功能
- ✨ 添加定时任务调度功能
- ✨ 添加 Inno Setup 安装程序
- ✨ 添加 GitHub Actions CI/CD

**改进**
- 🎨 优化用户界面
- 📝 改进日志输出
- 🔒 增强配置安全性

**文档**
- 📚 添加详细使用文档
- 📚 添加构建指南
- 📚 添加更新功能说明

完整更新日志：[CHANGELOG.md](CHANGELOG.md)

---

## 技术栈

- **GUI 框架**: [PySide6](https://pyside6.org/) (Qt for Python)
- **数据库**: [PyMySQL](https://pymysql.readthedocs.io/)
- **加密**: [cryptography](https://cryptography.io/)
- **任务调度**: [APScheduler](https://github.com/agronholm/apscheduler)
- **配置管理**: [PyYAML](https://pyyaml.org/)
- **编译工具**: [Nuitka](https://nuitka.net/)
- **安装程序**: [Inno Setup](https://jrsoftware.org/isinfo.php)

---

## 安全性

- 🔐 密码使用 Base64 加密存储
- 📝 所有操作记录详细日志
- ⚠️ 异常情况妥善处理
- 🚫 不收集任何用户数据

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)

```
Copyright (c) 2025 Database Backup Tool

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 贡献

欢迎贡献代码！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 贡献指南

- 遵循现有代码风格
- 添加适当的测试
- 更新相关文档
- 提交前测试所有功能

---

## 联系方式

- **项目主页**: [https://github.com/pengcunfu/DatabaseBackup](https://github.com/pengcunfu/DatabaseBackup)
- **问题反馈**: [GitHub Issues](https://github.com/pengcunfu/DatabaseBackup/issues)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

---

## 致谢

感谢以下开源项目：

- [PySide6](https://pyside6.org/) - Qt for Python
- [Nuitka](https://nuitka.net/) - Python 编译器
- [Inno Setup](https://jrsoftware.org/isinfo.php) - 安装程序制作工具
- [APScheduler](https://github.com/agronholm/apscheduler) - 任务调度器

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐ Star！**

Made with ❤️ by [pengcunfu](https://github.com/pengcunfu)

</div>
