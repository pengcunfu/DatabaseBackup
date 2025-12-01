# 数据库备份同步工具 - PySide6 Widgets 版本

## 项目概述

本项目已经从 QML 界面重构为传统的 PySide6 Widgets 界面，移除了所有 QML 相关代码，使用 PySide6 的默认样式。

## 项目结构

```
DatabaseBackup/
├── app/                          # 应用程序模块
│   ├── __init__.py               # 包初始化文件
│   ├── config_dialog.py          # 数据库配置对话框
│   ├── config_manager.py         # 配置管理器
│   ├── db_config.py              # 数据库配置类
│   ├── db_sync.py                # 数据库同步核心逻辑
│   └── main_window.py            # 主窗口界面
├── resources/                    # 资源文件夹
│   └── icon.png                  # 应用图标
├── logs/                         # 日志文件夹（运行时创建）
├── main.py                       # 主程序入口
├── build.py                      # Nuitka 构建脚本
├── requirements.txt              # Python 依赖
├── db_config.json               # 数据库配置（旧版兼容）
├── config.yaml                  # 配置文件（新版本）
└── README.md                    # 本文件
```

## 主要变更

### 1. 界面框架迁移
- **之前**: 使用 QML (Qt Quick) 界面
- **现在**: 使用传统 PySide6 Widgets 界面

### 2. 移除的文件
- `qml/` 文件夹及其所有内容
- `app/qml_backend.py` QML后端桥接文件

### 3. 新增的文件
- `app/main_window.py` - 主窗口实现
- `app/config_dialog.py` - 配置对话框实现

### 4. 构建配置更新
- 更新了 `build.py` 中的依赖文件列表
- 移除了对 QML 文件夹的依赖

### 5. 应用包更新
- 更新了 `app/__init__.py` 移除 QML 相关导入

## 功能特性
- 支持多数据库配置管理
- 数据库同步（本地到远程，远程到本地）
- SQL文件导出和执行
- 传统图形化用户界面（PySide6 Widgets）
- 安全的配置文件管理
- 实时日志显示和进度指示

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 图形界面模式
```bash
python main.py  # 启动PySide6 Widgets界面
```

### 构建 Windows 可执行文件
```bash
python build.py
```

## 配置文件 (config.yaml)
```yaml
databases:
  local:
    host: localhost
    port: 3306
    username: root
    password: encrypted_password
    database: robot_management_local

  remote:
    host: 192.168.1.100
    port: 3306
    username: root
    password: encrypted_password
    database: robot_management

sync_options:
  exclude_tables:
    - user_sessions
    - login_attempts
  drop_target_tables: true
```

## 安全性
- 密码使用Base64加密
- 详细的操作日志记录
- 异常情况处理

## 许可
MIT 开源许可

## 贡献
欢迎提交 Issues 和 Pull Requests！