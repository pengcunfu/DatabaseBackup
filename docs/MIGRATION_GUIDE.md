# 数据库迁移工具使用指南

## 简介

这是一个功能强大的数据库迁移和备份工具,支持多种数据库之间的数据迁移,包括:
- **MySQL** (5.x 和 8.x)
- **SQLite** (3.x)
- **PostgreSQL** (9.x+)

## 主要功能

### 1. 数据库迁移
支持在不同类型的数据库之间进行数据迁移,自动处理数据类型转换:
- MySQL ↔ SQLite
- MySQL ↔ PostgreSQL
- SQLite ↔ PostgreSQL
- MySQL 5 ↔ MySQL 8

### 2. 数据库备份
- 导出数据库为 SQL 文件
- 支持选择性导出特定表
- 支持只导出结构或包含数据

### 3. 数据导入
- 从 SQL 文件导入数据
- 自动处理语法转换
- 批量执行 SQL 语句

### 4. 定时任务
- 支持配置定时备份/迁移任务
- 灵活的调度策略(间隔、Cron 表达式)
- 任务执行日志和状态跟踪

## 安装

### 依赖要求

```bash
pip install -r requirements.txt
```

主要依赖:
- PySide6 (GUI 框架)
- PyMySQL (MySQL 驱动)
- psycopg2-binary (PostgreSQL 驱动)
- PyYAML (配置文件)
- APScheduler (定时任务)

### 运行程序

```bash
python main.py
```

## 配置说明

### 数据库配置

在程序中点击 "文件" → "配置数据库" 可以配置源数据库和目标数据库。

#### MySQL 配置示例
```
数据库类型: MySQL
主机地址: localhost
端口: 3306
用户名: root
密码: your_password
数据库名: my_database
```

#### SQLite 配置示例
```
数据库类型: SQLite
数据库文件: /path/to/database.db
```

#### PostgreSQL 配置示例
```
数据库类型: PostgreSQL
主机地址: localhost
端口: 5432
用户名: postgres
密码: your_password
数据库名: my_database
```

## 使用方法

### 数据库迁移

1. 在 "操作模式" 下拉框中选择 "数据库迁移"
2. 点击 "配置数据库" 设置本地(源)和远程(目标)数据库
3. 点击 "开始执行" 开始迁移

**迁移特性:**
- 自动转换数据类型
- 自动处理表结构差异
- 批量插入数据,提高效率
- 事务保护,失败可回滚

### 导出 SQL

1. 在 "操作模式" 下拉框中选择 "导出SQL"
2. 配置要导出的数据库
3. 点击 "开始执行"
4. SQL 文件将保存在程序目录下

### 导入 SQL

1. 在 "操作模式" 下拉框中选择 "导入SQL"
2. 配置目标数据库
3. 点击 "浏览" 选择要导入的 SQL 文件
4. 点击 "开始执行"

### 传统同步模式

程序保留了原有的同步功能,支持:
- 远程到本地同步
- 本地到远程同步
- 执行 SQL 文件

## 数据类型映射

工具会自动在不同数据库之间转换数据类型:

### MySQL → SQLite
| MySQL 类型 | SQLite 类型 |
|-----------|-------------|
| INT, BIGINT | INTEGER |
| VARCHAR, TEXT | TEXT |
| BLOB | BLOB |
| DATETIME | TEXT |
| DECIMAL | REAL |

### MySQL → PostgreSQL
| MySQL 类型 | PostgreSQL 类型 |
|-----------|-----------------|
| TINYINT | SMALLINT |
| INT | INTEGER |
| BIGINT | BIGINT |
| VARCHAR | VARCHAR |
| TEXT | TEXT |
| BLOB | BYTEA |
| DATETIME | TIMESTAMP |
| DECIMAL | NUMERIC |

### SQLite → MySQL
| SQLite 类型 | MySQL 类型 |
|-------------|------------|
| INTEGER | INT |
| REAL | DOUBLE |
| TEXT | TEXT |
| BLOB | BLOB |

## 注意事项

1. **数据库连接**: 确保目标数据库有足够的权限(创建表、插入数据)
2. **数据类型**: 某些特殊类型可能有精度损失(如 DECIMAL → REAL)
3. **外键约束**: 迁移时会禁用外键检查,迁移完成后需要手动恢复
4. **大数据库**: 对于大型数据库,建议分批次迁移或使用排除表功能
5. **字符编码**: 确保源和目标数据库使用相同的字符集(推荐 UTF-8)

## 常见问题

### Q: 迁移失败怎么办?
A: 查看日志输出,通常是由于数据类型不兼容或表结构差异导致。可以尝试:
- 检查目标数据库是否有足够权限
- 使用排除表功能跳过有问题的表
- 手动调整表结构后再迁移数据

### Q: 如何只迁移部分表?
A: 程序支持配置 `include_tables` 和 `exclude_tables` 选项来过滤要迁移的表。

### Q: SQLite 的性能如何?
A: SQLite 适合中小型数据库,对于大量数据建议使用 MySQL 或 PostgreSQL。

## 更新日志

### v2.0.0 (2025-01-XX)
- 新增多数据库支持(MySQL, SQLite, PostgreSQL)
- 新增数据库迁移功能
- 新增数据类型自动转换
- 改进配置界面,支持数据库类型选择
- 改进日志显示和进度跟踪

### v0.0.5
- 初始版本,仅支持 MySQL
- 基本的备份和同步功能

## 技术支持

如有问题或建议,请访问: https://github.com/pengcunfu/DatabaseBackup

## 许可证

Copyright © 2025 pengcunfu
