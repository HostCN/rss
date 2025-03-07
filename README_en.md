
# Telegram RSS Bot

A powerful and customizable Telegram bot designed to fetch and deliver RSS feed updates to your Telegram chats or channels. Built with Python, this bot leverages the Telegram API, Playwright for robust web scraping, and SQLite for persistent storage. It supports multiple languages, advanced filtering, and flexible message styling.

## Features

- **Simple Subscription**: Easily subscribe to RSS feeds by providing a URL or associating it with a Telegram channel.
- **Private and Secure**: Runs with user authorization to ensure only permitted users can interact with the bot.
- **Multi-Device Sync**: Manage subscriptions and settings across multiple devices via Telegram.
- **Fast Updates**: Checks feeds at customizable intervals and delivers updates quickly.
- **Powerful Customization**:
  - Set update intervals per feed.
  - Filter feed content by keywords or tags.
  - Customize message styles (10 predefined options).
  - Toggle link previews on or off.
- **Open Architecture**: Uses an open-source framework with Playwright for fetching feeds and SQLite for data management.
- **Secure Delivery**: Ensures messages are sent reliably with error handling and logging.
- **Social Integration**: Supports large Telegram groups and channels (up to 200,000 members).
- **Expressive Formatting**: Delivers richly formatted messages with HTML support.

## Prerequisites

Before setting up the bot, ensure you have the following:

- **Python 3.8+**: The bot is written in Python.
- **Telegram Bot Token**: Obtain one from [BotFather](https://t.me/BotFather) on Telegram.
- **Authorized User IDs**: A list of Telegram user IDs allowed to use the bot.
- **Dependencies**: Install required Python packages (see [Installation](#installation)).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/telegram-rss-bot.git
cd telegram-rss-bot
```

*Replace `yourusername` with your GitHub username or the actual repository URL.*

### 2. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

Create a `requirements.txt` file with the following content:

```
feedparser==6.0.10
sqlite3
playwright==1.40.0
telegram==0.0.1
python-telegram-bot==20.7
certifi==2023.11.17
```

Then run:

```bash
playwright install
```

This installs the Playwright browser binaries (Chromium, Firefox, Webkit).

### 3. Configure the Bot

Edit the script to include your Telegram Bot Token and authorized user IDs:

```python
TOKEN = 'your_bot_token_here'  # Replace with your token from BotFather
AUTHORIZED_USERS = ['user_id_1', 'user_id_2']  # Replace with actual Telegram user IDs
```

To find your user ID, send a message to [@userinfobot](https://t.me/userinfobot).

### 4. Initialize the Database

The bot uses SQLite to store subscriptions and settings. Initialize it by running the script once:

```bash
python bot.py
```

This creates a `subscriptions.db` file in the working directory.

### 5. Run the Bot

Start the bot with:

```bash
python bot.py
```

The bot will begin polling Telegram for commands and checking RSS feeds every 30 seconds.

## Usage

Interact with the bot via Telegram commands. Below are the available commands and examples:

### Commands

| Command                            | Description                                      | Example                                      |
|------------------------------------|--------------------------------------------------|----------------------------------------------|
| `/start`                           | Start the bot and show help                      | `/start`                                     |
| `/subscribe`                       | Add a new RSS feed                               | `/subscribe https://example.com/feed`        |
| `/unsubscribe`                     | Remove an RSS feed (interactive)                 | `/unsubscribe`                               |
| `/list`                            | Show your subscriptions                          | `/list`                                      |
| `/set_interval [@ChannelName] URL interval` | Set check interval (seconds)            | `/set_interval https://example.com/feed 300` |
| `/pause URL`                       | Pause a feed                                     | `/pause https://example.com/feed`            |
| `/resume URL`                      | Resume a feed                                    | `/resume https://example.com/feed`           |
| `/set_filter [@ChannelName] URL keyword [--tag]` | Filter by keyword or tag          | `/set_filter https://example.com/feed news`  |
| `/set_tag URL @ChannelName tag`    | Set a custom tag for a feed in a channel         | `/set_tag https://example.com/feed @MyChannel News` |
| `/set_preview [@ChannelName] on\|off` | Toggle link preview                   | `/set_preview on`                            |
| `/set_style [@ChannelName] 1-10`   | Set message style (1-10)                        | `/set_style 3`                               |
| `/show_styles`                     | Show available message styles                    | `/show_styles`                               |
| `/feedback text`                   | Send feedback                                    | `/feedback Great bot!`                       |
| `/get_latest [@ChannelName] URL [number]` | Get latest updates                       | `/get_latest https://example.com/feed 5`     |
| `/help`                            | Show help message                                | `/help`                                      |

### Examples

1. **Subscribe to an RSS Feed**
   ```
   /subscribe https://rss.example.com/feed
   ```
   Response: "Subscribed to https://rss.example.com/feed"

2. **Subscribe to a Feed for a Channel**
   ```
   /subscribe @MyChannel https://rss.example.com/feed
   ```
   Response: "Subscribed to https://rss.example.com/feed for channel @MyChannel"

3. **Set Update Interval**
   ```
   /set_interval https://rss.example.com/feed 600
   ```
   Response: "Interval for https://rss.example.com/feed set to 600 seconds."

4. **List Subscriptions**
   ```
   /list
   ```
   Response: A list of all subscriptions with their status, intervals, filters, and tags.

5. **Filter Feed by Keyword**
   ```
   /set_filter https://rss.example.com/feed technology
   ```
   Response: "Filter for https://rss.example.com/feed set to technology"

## Configuration

### Database Schema

The bot uses SQLite with the following tables:

- **subscriptions**: Stores feed subscriptions.
  - `chat_id`: Telegram chat ID.
  - `is_channel`: Boolean indicating if the chat is a channel.
  - `url`: RSS feed URL.
  - `interval`: Check interval in seconds.
  - `paused`: Boolean indicating if the feed is paused.
  - `last_checked`: Timestamp of the last check.
  - `filter_keyword`: Keyword or tag filter.
  - `tag`: Custom tag for the feed.

- **settings**: Stores user/chat settings.
  - `chat_id`: Telegram chat ID.
  - `link_preview`: Boolean for enabling/disabling link previews.
  - `message_style`: Integer (1-10) for message style.
  - `language`: Language code (e.g., `en`, `zh`).

- **sent_posts**: Tracks sent posts to avoid duplicates.
  - `chat_id`: Telegram chat ID.
  - `post_link`: URL of the sent post.
  - `sent_time`: Timestamp of when the post was sent.

### Message Styles

The bot supports 10 message styles for formatting RSS updates. Use `/show_styles` to preview them. Examples:

- **Style 1**: `Title\nLink`
- **Style 2**: `\n<b>Title</b>\n\nLink`
- **Style 3**: `<b><a href='Link'>Title</a></b>`

### Language Support

The bot supports English (`en`) and Chinese (`zh`). Language is detected based on the user's Telegram settings, defaulting to Chinese if not specified.

## Logging

The bot logs events to the console with the following format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Log level is set to `INFO`. Errors are logged with stack traces for debugging.

## Troubleshooting

- **Bot Not Responding**: Check the token and ensure the bot is running.
- **Feed Not Updating**: Verify the RSS URL is valid and accessible. Check logs for errors.
- **Permission Denied**: Ensure your user ID is in `AUTHORIZED_USERS`.
- **Database Issues**: Delete `subscriptions.db` and restart the bot to reinitialize.

## Contributing

Contributions are welcome! Please:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).
- Uses [Playwright](https://playwright.dev/) for robust feed fetching.
- Inspired by the need for a flexible RSS solution on Telegram.
