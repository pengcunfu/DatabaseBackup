# MySQL 数据库同步工具

数据库备份工具

先完成MySQL的功能，后续接入更多数据库。



## 功能特性
- 支持多数据库配置管理
- 数据库同步（本地到远程，远程到本地）
- SQL文件导出和执行
- 图形化用户界面
- 安全的配置文件管理

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 图形界面模式
```bash
python main.py  # 默认启动GUI
```

### 命令行模式

#### 数据库同步
```bash
# 从本地同步到远程数据库
python main.py --mode sync --source local --target remote

# 从远程同步到本地数据库
python main.py --mode sync --source remote --target local
```

#### SQL文件导出
```bash
# 导出本地数据库（包含数据）
python main.py --mode export --database local --output local_db.sql --include-data

# 仅导出数据库结构
python main.py --mode export --database local --output local_db_structure.sql
```

#### 执行SQL文件
```bash
python main.py --mode execute --database local --sql-file path/to/script.sql
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