# Telegram RSS Feed Bot

这是一个设计用于管理和分发RSS订阅给用户或频道的Telegram机器人。它支持多种功能，如订阅、取消订阅、设置更新间隔、内容过滤和切换消息样式等。

## 目录
- [功能](#功能)
- [设置](#设置)
- [使用方法](#使用方法)
- [命令](#命令)
- [数据库结构](#数据库结构)
- [配置](#配置)
- [运行机器人](#运行机器人)
- [贡献](#贡献)
- [许可证](#许可证)

## 功能
- **多语言支持**: 支持英语（en）和中文（zh）。
- **订阅管理**: 用户可以订阅或取消订阅RSS feeds。
- **设置间隔**: 允许用户为每个订阅设置自定义的检查更新间隔。
- **暂停/恢复**: 可以暂停或恢复特定订阅的更新检查。
- **内容过滤**: 基于关键词过滤RSS内容。
- **消息样式**: 可以选择不同的消息格式样式。
- **链接预览开关**: 可以开启或关闭消息中的链接预览。
- **反馈机制**: 用户可以通过机器人直接发送反馈。
- **最新更新**: 从已订阅的feeds中获取最新更新。

## 设置

### 先决条件
- Python 3.8 或更高版本
- 从BotFather获得的Telegram机器人token
- SQLite3（Python默认自带）
- 需要的库：`feedparser`、`aiohttp`、`python-telegram-bot`

### 安装
1. 克隆仓库：
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name/rss
   ```

2. 安装所需的库：
   ```bash
   pip install feedparser aiohttp python-telegram-bot
   ```

3. 设置环境变量或直接在脚本中配置机器人token：
   - 编辑`/rss/bot.py`中的`TOKEN`或使用环境变量。

4. 初始化数据库：
   - 运行脚本一次以初始化数据库（会创建`subscriptions.db`）。

## 使用方法
- 将机器人添加到您的Telegram账号或频道。
- 使用下面的命令与机器人互动。

## 命令
- `/start` - 启动机器人并显示帮助。
- `/subscribe` - 添加新的RSS订阅。机器人会提示您输入URL。
- `/unsubscribe` - 移除RSS订阅。您将看到一个列表供选择。
- `/list` - 列出所有订阅。
- `/set_interval URL 间隔` - 为订阅设置检查更新的间隔（以秒为单位）。
- `/pause URL` - 暂停来自某个订阅的更新。
- `/resume URL` - 恢复来自某个订阅的更新。
- `/set_filter URL 关键词` - 为订阅设置一个关键词来过滤内容。
- `/set_preview on|off` - 切换消息中的链接预览。
- `/set_style 1|2|3` - 设置订阅更新消息的样式。
- `/feedback 反馈` - 向机器人开发者发送反馈。
- `/get_latest [数量]` - 获取已订阅订阅的最新更新。可以指定更新的数量。
- `/help` - 显示帮助信息。

## 数据库结构
- **subscriptions**: 存储每个订阅的信息，包括chat_id、URL、间隔、暂停状态、最后检查时间和过滤关键词。
- **settings**: 存储用户设置，如链接预览偏好、消息样式和语言。
- **sent_posts**: 记录已发送的帖子，避免重复发送。

## 配置
- **TOKEN**: 您从BotFather获取的机器人token。请确保保密。
- **AUTHORIZED_USERS**: 允许与机器人互动的用户ID列表。添加您的Telegram用户ID。
- **HEADERS**: 用于请求RSS feeds的HTTP头。可以根据需要自定义。

## 运行机器人
运行机器人：
```bash
python /rss/bot.py
```

机器人将每20秒检查一次新帖子。如果需要，可以调整`check_latest_posts`任务的间隔。

## 贡献
欢迎贡献！请fork仓库并提交pull requests。问题和功能请求可以在GitHub的issues部分提出。

## 许可证
本项目在MIT许可证下开源。详见LICENSE文件。
```

**注意:** 将`https://github.com/your-username/your-repo-name.git`替换为您在GitHub上托管的实际仓库URL。根据您的项目设置调整任何其他具体细节。
