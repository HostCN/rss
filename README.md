
# Telegram RSS 机器人

一个功能强大且可定制的 Telegram 机器人，旨在为您将 RSS 源更新获取并发送到 Telegram 聊天或频道。该机器人使用 Python 开发，利用 Telegram API、Playwright 进行可靠的网页抓取，以及 SQLite 进行持久化存储。它支持多语言、高级过滤和灵活的消息样式。

## 功能

- **简单订阅**: 通过提供 URL 或关联 Telegram 频道轻松订阅 RSS 源。
- **私密安全**: 通过用户授权运行，确保只有允许的用户可以与机器人交互。
- **多设备同步**: 通过 Telegram 在多个设备上管理订阅和设置。
- **快速更新**: 以可自定义的间隔检查源并快速传递更新。
- **强大的自定义功能**:
  - 为每个源设置更新间隔。
  - 通过关键词或标签过滤源内容。
  - 自定义消息样式（提供 10 种预定义选项）。
  - 开关链接预览。
- **开放架构**: 使用开源框架，结合 Playwright 获取源和 SQLite 管理数据。
- **安全传递**: 确保消息可靠发送，包含错误处理和日志记录。
- **社交集成**: 支持大型 Telegram 群组和频道（最多 200,000 名成员）。
- **丰富的表达**: 支持 HTML 格式，提供丰富格式的消息。

## 前提条件

在设置机器人之前，请确保具备以下条件：

- **Python 3.8+**: 机器人使用 Python 编写。
- **Telegram Bot Token**: 从 Telegram 的 [BotFather](https://t.me/BotFather) 获取。
- **授权用户 ID**: 允许使用机器人的 Telegram 用户 ID 列表。
- **依赖项**: 安装所需的 Python 包（见 [安装](#安装)）。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/telegram-rss-bot.git
cd telegram-rss-bot
```

*将 `yourusername` 替换为您的 GitHub 用户名或实际仓库 URL。*

### 2. 安装依赖

使用 `pip` 安装所需的 Python 包：

```bash
pip install -r requirements.txt
```

创建一个 `requirements.txt` 文件，内容如下：

```
feedparser==6.0.10
sqlite3
playwright==1.40.0
telegram==0.0.1
python-telegram-bot==20.7
certifi==2023.11.17
```

然后运行：

```bash
playwright install
```

这将安装 Playwright 的浏览器二进制文件（Chromium、Firefox、Webkit）。

### 3. 配置机器人

编辑脚本以包含您的 Telegram Bot Token 和授权用户 ID：

```python
TOKEN = 'your_bot_token_here'  # 替换为从 BotFather 获取的 token
AUTHORIZED_USERS = ['user_id_1', 'user_id_2']  # 替换为实际的 Telegram 用户 ID
```

要查找您的用户 ID，可向 [@userinfobot](https://t.me/userinfobot) 发送消息。

### 4. 初始化数据库

机器人使用 SQLite 存储订阅和设置。首次运行脚本以初始化：

```bash
python bot.py
```

这将在工作目录中创建 `subscriptions.db` 文件。

### 5. 运行机器人

启动机器人：

```bash
python bot.py
```

机器人将开始轮询 Telegram 以接收命令，并每 30 秒检查一次 RSS 源。

## 使用方法

通过 Telegram 命令与机器人交互。以下是可用命令和示例：

### 命令列表

| 命令                                | 描述                                      | 示例                                           |
|-------------------------------------|-------------------------------------------|------------------------------------------------|
| `/start`                            | 启动机器人并显示帮助                      | `/start`                                       |
| `/subscribe`                        | 添加新的 RSS 源                           | `/subscribe https://example.com/feed`          |
| `/unsubscribe`                      | 删除 RSS 源（交互式）                     | `/unsubscribe`                                 |
| `/list`                             | 显示您的订阅                              | `/list`                                        |
| `/set_interval [@ChannelName] URL 间隔` | 设置检查间隔（秒）                   | `/set_interval https://example.com/feed 300`   |
| `/pause URL`                        | 暂停一个源                                | `/pause https://example.com/feed`              |
| `/resume URL`                       | 恢复一个源                                | `/resume https://example.com/feed`             |
| `/set_filter [@ChannelName] URL 关键词 [--tag]` | 按关键词或标签过滤           | `/set_filter https://example.com/feed news`    |
| `/set_tag URL @ChannelName 标签`    | 为频道中的源设置自定义标签                | `/set_tag https://example.com/feed @MyChannel 新闻` |
| `/set_preview [@ChannelName] on\|off` | 开关链接预览                         | `/set_preview on`                              |
| `/set_style [@ChannelName] 1-10`    | 设置消息样式（1-10）                      | `/set_style 3`                                 |
| `/show_styles`                      | 显示可用消息样式                          | `/show_styles`                                 |
| `/feedback 文本`                    | 发送反馈                                  | `/feedback 很棒的机器人！`                     |
| `/get_latest [@ChannelName] URL [数量]` | 获取最新更新                          | `/get_latest https://example.com/feed 5`       |
| `/help`                             | 显示帮助信息                              | `/help`                                        |

### 示例

1. **订阅 RSS 源**
   ```
   /subscribe https://rss.example.com/feed
   ```
   回复: "已订阅 https://rss.example.com/feed"

2. **为频道订阅 RSS 源**
   ```
   /subscribe @MyChannel https://rss.example.com/feed
   ```
   回复: "已为频道 @MyChannel 订阅 https://rss.example.com/feed"

3. **设置更新间隔**
   ```
   /set_interval https://rss.example.com/feed 600
   ```
   回复: "已将 https://rss.example.com/feed 的间隔设置为 600 秒。"

4. **列出订阅**
   ```
   /list
   ```
   回复: 所有订阅的列表，包括状态、间隔、过滤器和标签。

5. **按关键词过滤源**
   ```
   /set_filter https://rss.example.com/feed 技术
   ```
   回复: "已为 https://rss.example.com/feed 设置过滤器为 技术"

## 配置

### 数据库架构

机器人使用 SQLite，包含以下表：

- **subscriptions**: 存储订阅信息。
  - `chat_id`: Telegram 聊天 ID。
  - `is_channel`: 布尔值，表示聊天是否为频道。
  - `url`: RSS 源 URL。
  - `interval`: 检查间隔（秒）。
  - `paused`: 布尔值，表示源是否暂停。
  - `last_checked`: 上次检查的时间戳。
  - `filter_keyword`: 关键词或标签过滤器。
  - `tag`: 源的自定义标签。

- **settings**: 存储用户/聊天设置。
  - `chat_id`: Telegram 聊天 ID。
  - `link_preview`: 布尔值，启用/禁用链接预览。
  - `message_style`: 整数（1-10），表示消息样式。
  - `language`: 语言代码（例如 `en`、`zh`）。

- **sent_posts**: 跟踪已发送的帖子以避免重复。
  - `chat_id`: Telegram 聊天 ID。
  - `post_link`: 已发送帖子的 URL。
  - `sent_time`: 发送时间的时间戳。

### 消息样式

机器人支持 10 种消息样式来格式化 RSS 更新。使用 `/show_styles` 查看预览。示例：

- **样式 1**: `标题\n链接`
- **样式 2**: `\n<b>标题</b>\n\n链接`
- **样式 3**: `<b><a href='链接'>标题</a></b>`

### 语言支持

机器人支持英语（`en`）和中文（`zh`）。语言根据用户的 Telegram 设置自动检测，默认为中文。

## 日志

机器人将事件记录到控制台，格式如下：

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

日志级别设为 `INFO`。错误会记录堆栈跟踪以便调试。

## 故障排除

- **机器人无响应**: 检查 token 是否正确，确保机器人正在运行。
- **源未更新**: 验证 RSS URL 是否有效且可访问，检查日志中的错误。
- **权限拒绝**: 确保您的用户 ID 在 `AUTHORIZED_USERS` 中。
- **数据库问题**: 删除 `subscriptions.db` 并重启机器人以重新初始化。

## 贡献

欢迎贡献！请按照以下步骤操作：

1. Fork 仓库。
2. 创建功能分支（`git checkout -b feature/new-feature`）。
3. 提交更改（`git commit -m "添加新功能"`）。
4. 推送分支（`git push origin feature/new-feature`）。
5. 提交拉取请求。

## 许可证

本项目采用 MIT 许可证。详情见 [LICENSE](LICENSE) 文件。

## 鸣谢

- 使用 [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 构建。
- 使用 [Playwright](https://playwright.dev/) 实现可靠的源获取。
- 灵感来源于在 Telegram 上实现灵活 RSS 解决方案的需求。

---

此 `README.md` 提供了 Telegram RSS 机器人的全面指南，便于用户理解、安装和有效使用机器人。请根据您的项目调整仓库 URL、许可证和其他具体细节！
