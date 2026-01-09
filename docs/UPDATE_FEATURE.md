# 版本更新功能说明

## 功能概述

DatabaseBackup工具现在支持自动检查和安装更新，确保您始终使用最新版本。

## 主要功能

### 1. 自动更新检查
- 程序启动3秒后自动检查更新
- 每7天自动检查一次（可配置）
- 后台静默检查，不打扰用户

### 2. 手动检查更新
- 菜单栏: `帮助` → `检查更新`
- 实时查看最新版本信息

### 3. 智能更新提示
- 显示当前版本和最新版本
- 展示更新内容和文件大小
- 提供下载、稍后、跳过等选项

### 4. 一键下载安装
- 自动下载更新安装包
- 下载完成后可直接安装
- 支持断点续传（计划中）

## 使用方法

### 检查更新

1. **自动检查**
   - 程序启动时自动检查
   - 根据配置的时间间隔定期检查

2. **手动检查**
   ```
   菜单栏 → 帮助 → 检查更新
   ```

### 安装更新

1. 当检测到新版本时，会弹出更新提示对话框
2. 点击"下载更新"按钮
3. 等待下载完成（会显示下载进度）
4. 下载完成后可选择：
   - **立即安装**: 自动启动安装程序并退出当前版本
   - **稍后安装**: 安装包保存在下载文件夹，可稍后手动安装

### 跳过版本

- 如果不想更新某个版本，可以点击"跳过此版本"
- 该版本将不再提示更新

## 配置选项

更新配置保存在: `~/.databasebackup/update_config.json`

### 配置项

```json
{
  "auto_check": true,          // 是否自动检查更新
  "check_interval": 7,         // 检查间隔（天）
  "last_check": "",            // 上次检查时间
  "skipped_version": "",       // 跳过的版本
  "beta_updates": false        // 是否接收测试版更新
}
```

### 修改配置

您可以通过配置文件或界面（计划中）修改：
- `auto_check`: 启用/禁用自动检查
- `check_interval`: 设置检查间隔（天）
- `beta_updates`: 是否接收测试版更新

## 技术实现

### 核心组件

1. **UpdateChecker (QThread)**
   - 异步检查更新
   - 下载安装包
   - 避免阻塞主界面

2. **UpdateManager (QObject)**
   - 管理更新流程
   - 处理用户交互
   - 协调各个组件

3. **UpdateConfig**
   - 保存更新配置
   - 记录检查历史
   - 管理跳过的版本

### API接口

- 使用GitHub Releases API获取最新版本
- 自动查找Windows安装程序
- 支持自定义更新源

## 版本号规则

遵循语义化版本 (Semantic Versioning):

- **主版本**: 1.0.0 → 2.0.0 (重大更新，不兼容)
- **次版本**: 1.0.0 → 1.1.0 (新功能，向下兼容)
- **补丁**: 1.0.0 → 1.0.1 (Bug修复)

## 开发相关

### 发布新版本

1. 更新版本号:
   ```bash
   python scripts/release.py --patch  # 补丁版本
   python scripts/release.py --minor  # 次版本
   python scripts/release.py --major  # 主版本
   ```

2. 推送到GitHub后自动触发:
   - 构建Windows安装程序
   - 创建GitHub Release
   - 用户即可收到更新通知

### 测试更新功能

```python
from app.update_manager import check_update

# 在主窗口中调用
manager = check_update(parent)
```

## 常见问题

### Q: 如何禁用自动检查更新？
A: 修改配置文件中的 `auto_check` 为 `false`

### Q: 下载的安装包保存在哪里？
A: 默认保存在 `~/Downloads/` 文件夹

### Q: 更新失败怎么办？
A: 可以手动访问项目主页下载:
   https://github.com/pengcunfu/DatabaseBackup/releases

### Q: 如何回退到旧版本？
A: 在GitHub Releases页面下载历史版本

## 未来计划

- [ ] 支持增量更新（仅下载变更部分）
- [ ] 后台静默更新
- [ ] 自动更新配置界面
- [ ] 支持Rollback（回滚功能）
- [ ] 多线程下载加速
- [ ] 断点续传
