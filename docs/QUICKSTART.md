# 快速开始指南

## 安装

### 1. 克隆或下载项目

```bash
cd DatabaseBackup
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

这将安装以下依赖:
- PySide6 - GUI 框架
- PyMySQL - MySQL 数据库驱动
- psycopg2-binary - PostgreSQL 数据库驱动
- PyYAML - 配置文件处理
- APScheduler - 定时任务

### 3. 运行程序

```bash
python main.py
```

## 基本使用

### 场景 1: MySQL 到 SQLite 迁移

1. **配置源数据库(MySQL)**
   - 点击 "文件" → "配置数据库"
   - 在 "本地数据库" 标签页:
     - 数据库类型: 选择 **MySQL**
     - 主机地址: `localhost`
     - 端口: `3306`
     - 用户名: `root`
     - 密码: (你的密码)
     - 数据库名: `my_mysql_db`

2. **配置目标数据库(SQLite)**
   - 切换到 "远程数据库" 标签页:
     - 数据库类型: 选择 **SQLite**
     - 数据库文件: `data/my_sqlite.db`

3. **执行迁移**
   - 在主界面 "操作模式" 选择: **数据库迁移**
   - 点击 "开始执行"
   - 等待迁移完成

### 场景 2: MySQL 5 到 MySQL 8 升级

1. **配置源数据库(MySQL 5)**
   - 本地数据库配置指向 MySQL 5 服务器

2. **配置目标数据库(MySQL 8)**
   - 远程数据库配置指向 MySQL 8 服务器

3. **执行迁移**
   - 操作模式: **数据库迁移**
   - 点击 "开始执行"

### 场景 3: 导出数据库为 SQL 文件

1. **配置要导出的数据库**
   - 在 "本地数据库" 中配置

2. **执行导出**
   - 操作模式: **导出SQL**
   - 点击 "开始执行"
   - SQL 文件会保存在程序目录

### 场景 4: 从 SQL 文件导入

1. **配置目标数据库**
   - 在 "本地数据库" 中配置

2. **选择 SQL 文件**
   - 点击 "浏览" 选择 SQL 文件

3. **执行导入**
   - 操作模式: **导入SQL**
   - 点击 "开始执行"

## 配置示例

### MySQL 配置
```json
{
    "db_type": "mysql",
    "host": "localhost",
    "port": 3306,
    "username": "root",
    "password": "your_password",
    "database": "your_database"
}
```

### SQLite 配置
```json
{
    "db_type": "sqlite",
    "database": "path/to/database.db"
}
```

### PostgreSQL 配置
```json
{
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "postgres",
    "password": "your_password",
    "database": "your_database"
}
```

## 测试连接

配置完成后,建议先测试连接:

1. 在配置对话框中点击 "测试连接"
2. 查看连接结果
3. 确认无误后保存配置

## 常见问题

### Q: 提示 "数据库驱动未安装"
**A:** 安装对应的数据库驱动:
```bash
# MySQL
pip install pymysql

# PostgreSQL
pip install psycopg2-binary
```

### Q: SQLite 连接失败
**A:** 确保:
- 数据库文件路径正确
- 程序有该目录的读写权限
- 目录存在(如果指定了子目录)

### Q: 迁移过程中出错
**A:**
1. 检查日志输出查看具体错误
2. 确认目标数据库有足够权限
3. 尝试只迁移部分表进行测试

### Q: 数据类型不兼容
**A:** 工具会自动转换大部分数据类型,某些特殊类型可能需要手动调整。

## 下一步

- 阅读详细文档: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- 查看更新日志: [CHANGELOG.md](CHANGELOG.md)
- 运行测试脚本: `python test_migration.py`

## 技术支持

如有问题,请访问: https://github.com/pengcunfu/DatabaseBackup
