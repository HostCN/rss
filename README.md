# RSS Telegram Bot

这是一个功能丰富的 Telegram 机器人，用于订阅和管理 RSS 源。它支持多语言、频道订阅、消息样式定制、链接预览、内容过滤等功能。通过 Playwright 抓取 RSS 内容，确保能够处理复杂的网页结构。

---

## 功能列表

- **订阅 RSS 源**：支持普通聊天和频道订阅。
- **多语言支持**：目前支持中文和英文。
- **消息样式定制**：提供 6 种不同的消息样式。
- **链接预览**：可开启或关闭链接预览。
- **内容过滤**：根据关键词过滤订阅内容。
- **定时检查**：定期检查 RSS 源并推送新内容。
- **批量处理**：批量处理消息，提高效率。
- **反馈功能**：用户可以通过机器人发送反馈。
- **授权管理**：仅允许授权用户使用机器人。

---

## 安装与配置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/rss-telegram-bot.git
cd rss-telegram-bot
```

### 2. 安装依赖

确保你已经安装了 Python 3.8 或更高版本。

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录下创建一个 `.env` 文件，并添加以下内容：

```env
TOKEN=your_telegram_bot_token
AUTHORIZED_USERS=user_id1,user_id2
```

- `TOKEN`：你的 Telegram 机器人 token。
- `AUTHORIZED_USERS`：授权用户的 ID，多个用户用逗号分隔。

### 4. 初始化数据库

运行以下命令初始化数据库：

```bash
python3 -c "from your_script_name import init_db; init_db()"
```

### 5. 运行机器人

```bash
python3 your_script_name.py
```

---

## 使用说明

### 1. 启动机器人

发送 `/start` 命令启动机器人并查看帮助信息。

### 2. 订阅 RSS 源

发送 `/subscribe` 命令，然后输入 RSS 源的 URL。如果是频道订阅，格式为 `@ChannelName URL`。

### 3. 取消订阅

发送 `/unsubscribe` 命令，然后选择要取消订阅的 RSS 源。

### 4. 查看订阅列表

发送 `/list` 命令查看当前订阅的 RSS 源。

### 5. 设置检查间隔

发送 `/set_interval URL interval` 命令设置 RSS 源的检查间隔（秒）。

### 6. 暂停/恢复订阅

发送 `/pause URL` 或 `/resume URL` 命令暂停或恢复订阅。

### 7. 设置内容过滤

发送 `/set_filter URL keyword` 命令设置内容过滤关键词。

### 8. 设置链接预览

发送 `/set_preview on|off` 命令开启或关闭链接预览。

### 9. 设置消息样式

发送 `/set_style 1|2|3|4|5|6` 命令设置消息样式。

### 10. 查看消息样式

发送 `/show_styles` 命令查看所有可用的消息样式。

### 11. 发送反馈

发送 `/feedback text` 命令发送反馈。

### 12. 获取最新更新

发送 `/get_latest [number]` 命令获取指定数量的最新更新。

---

## 数据库结构

### `subscriptions` 表

| 字段名        | 类型      | 描述                     |
|---------------|-----------|--------------------------|
| chat_id       | INTEGER   | 聊天 ID                  |
| is_channel    | BOOLEAN   | 是否为频道               |
| url           | TEXT      | RSS 源 URL               |
| interval      | INTEGER   | 检查间隔（秒）           |
| paused        | BOOLEAN   | 是否暂停                 |
| last_checked  | INTEGER   | 上次检查时间（时间戳）   |
| filter_keyword| TEXT      | 内容过滤关键词           |

### `settings` 表

| 字段名        | 类型      | 描述                     |
|---------------|-----------|--------------------------|
| chat_id       | INTEGER   | 聊天 ID                  |
| link_preview  | BOOLEAN   | 是否开启链接预览         |
| message_style | INTEGER   | 消息样式                 |
| language      | TEXT      | 用户语言                 |

### `sent_posts` 表

| 字段名        | 类型      | 描述                     |
|---------------|-----------|--------------------------|
| chat_id       | INTEGER   | 聊天 ID                  |
| post_link     | TEXT      | 帖子链接                 |
| sent_time     | INTEGER   | 发送时间（时间戳）       |

---

## 依赖列表

### 1. **核心依赖**
这些是运行机器人所需的核心库。

| 依赖名称               | 版本要求 | 描述                                                                 |
|------------------------|----------|----------------------------------------------------------------------|
| `python-telegram-bot`  | `>=20.0` | Telegram Bot API 的 Python 封装库，用于与 Telegram 服务器通信。       |
| `feedparser`           | `>=6.0`  | 用于解析 RSS 和 Atom 源的工具。                                      |
| `playwright`           | `>=1.40` | 用于抓取动态网页内容的无头浏览器库。                                 |
| `certifi`              | `>=2023` | 提供 CA 证书，用于 HTTPS 请求的 SSL 验证。                           |
| `sqlite3`              | 内置     | SQLite 数据库，用于存储订阅信息和用户设置。                          |
| `asyncio`              | 内置     | Python 的异步 I/O 框架，用于处理并发任务。                           |
| `logging`              | 内置     | Python 的日志模块，用于记录运行日志。                                |

### 2. **可选依赖**
这些依赖项用于增强功能或开发调试。

| 依赖名称               | 版本要求 | 描述                                                                 |
|------------------------|----------|----------------------------------------------------------------------|
| `pytest`               | `>=7.0`  | 用于运行单元测试的测试框架。                                         |
| `black`                | `>=23.0` | 代码格式化工具，确保代码风格一致。                                   |
| `flake8`               | `>=6.0`  | 代码静态检查工具，用于检查代码风格和潜在问题。                       |
| `python-dotenv`        | `>=1.0`  | 用于加载 `.env` 文件中的环境变量。                                   |

---

## 开发与贡献

欢迎提交 Issue 和 Pull Request。请在提交之前确保代码通过所有测试。

### 运行测试

```bash
python3 -m pytest
```

### 代码风格

请遵循 PEP 8 代码风格指南。

---

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

## 致谢

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [feedparser](https://github.com/kurtmckee/feedparser)
- [playwright](https://github.com/microsoft/playwright-python)

---

感谢使用 RSS Telegram Bot！如有任何问题或建议，请随时联系。
