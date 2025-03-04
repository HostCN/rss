import feedparser
import sqlite3
import logging
import time
import asyncio
import ssl
import certifi
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import filters
from telegram.constants import ParseMode
import aiohttp

TOKEN = 'bot'
AUTHORIZED_USERS = ['8111870448', '7554663120']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.google.com/',
}

lang_dict = {
    'en': {
        'welcome': 'Welcome to RSS Bot! Here are the available commands:',
        'subscribe_prompt': 'Please send the RSS feed URL:',
        'unsubscribe_prompt': 'Select a feed to unsubscribe:',
        'no_subscription': 'No subscriptions yet.',
        'subscribed': 'Subscribed to <a href="{0}">{0}</a>',
        'unsubscribed': 'Unsubscribed from <a href="{0}">{0}</a>',
        'invalid_choice': 'Invalid choice.',
        'interval_set': 'Interval for <a href="{0}">{0}</a> set to <code>{1}</code> seconds.',
        'not_found': 'Feed not found.',
        'paused': 'Paused <a href="{0}">{0}</a>.',
        'resumed': 'Resumed <a href="{0}">{0}</a>.',
        'list_subscriptions': 'Your subscriptions:',
        'status': '{0}. <a href="{1}">{1}</a> - <i>{2}</i> - Interval: <code>{3}</code>s - Filter: <code>{4}</code>',
        'help': '<b>Available Commands:</b>\n'
                '<b>/start</b> - Start the bot and show help\n'
                '<b>/subscribe</b> - Add a new RSS feed\n'
                '<b>/unsubscribe</b> - Remove an RSS feed\n'
                '<b>/list</b> - Show your subscriptions\n'
                '<b>/set_interval URL interval</b> - Set check interval (seconds)\n'
                '<b>/pause URL</b> - Pause a feed\n'
                '<b>/resume URL</b> - Resume a feed\n'
                '<b>/set_filter URL keyword</b> - Filter feed content\n'
                '<b>/set_preview on|off</b> - Toggle link preview\n'
                '<b>/set_style 1|2|3</b> - Set message style\n'
                '<b>/feedback text</b> - Send feedback\n'
                '<b>/get_latest [number]</b> - Get latest updates\n'
                '<b>/help</b> - Show this help',
        'feedback_thanks': 'Thanks for your feedback!',
        'error': 'Error: {0}',
        'get_latest_prompt': 'Specify number of updates: /get_latest [number] (default 1)',
        'latest_updates': 'Latest {0} update(s):',
        'no_updates': 'No new updates.',
        'feed_unhealthy': 'Warning: <a href="{0}">{0}</a> is unresponsive.',
        'timeout': 'Subscription to <a href="{0}">{0}</a> timed out.',
        'empty_feed': 'The feed <a href="{0}">{0}</a> appears empty or could not be parsed correctly.',
        'preview_set': 'Link preview set to {0}',
        'style_set': 'Message style set to Style {0}'
    },
    'zh': {
        'welcome': '欢迎使用RSS机器人！以下是可用命令：',
        'subscribe_prompt': '请发送RSS feed URL：',
        'unsubscribe_prompt': '选择要取消订阅的feed：',
        'no_subscription': '你还没有订阅任何feed。',
        'subscribed': '已订阅 <a href="{0}">{0}</a>',
        'unsubscribed': '已取消订阅 <a href="{0}">{0}</a>',
        'invalid_choice': '无效选择。',
        'interval_set': '已将 <a href="{0}">{0}</a> 的间隔设置为 <code>{1}</code>秒。',
        'not_found': '未找到该feed。',
        'paused': '已暂停 <a href="{0}">{0}</a>。',
        'resumed': '已恢复 <a href="{0}">{0}</a>。',
        'list_subscriptions': '你的订阅列表：',
        'status': '{0}. <a href="{1}">{1}</a> - <i>{2}</i> - 间隔：<code>{3}</code>秒 - 过滤：<code>{4}</code>',
        'help': '<b>可用命令：</b>\n'
                '<b>/start</b> - 启动机器人并显示帮助\n'
                '<b>/subscribe</b> - 添加RSS订阅\n'
                '<b>/unsubscribe</b> - 取消RSS订阅\n'
                '<b>/list</b> - 查看订阅列表\n'
                '<b>/set_interval URL 间隔</b> - 设置检查间隔（秒）\n'
                '<b>/pause URL</b> - 暂停订阅\n'
                '<b>/resume URL</b> - 恢复订阅\n'
                '<b>/set_filter URL 关键词</b> - 过滤订阅内容\n'
                '<b>/set_preview on|off</b> - 开关链接预览\n'
                '<b>/set_style 1|2|3</b> - 设置消息样式\n'
                '<b>/feedback 反馈</b> - 发送反馈\n'
                '<b>/get_latest [数量]</b> - 获取最新更新\n'
                '<b>/help</b> - 显示此帮助',
        'feedback_thanks': '感谢你的反馈！',
        'error': '错误：{0}',
        'get_latest_prompt': '请指定更新数量：/get_latest [数量]（默认1）',
        'latest_updates': '最新{0}条更新：',
        'no_updates': '没有新更新。',
        'feed_unhealthy': '警告：<a href="{0}">{0}</a> 无响应。',
        'timeout': '订阅 <a href="{0}">{0}</a> 超时。',
        'empty_feed': '该feed <a href="{0}">{0}</a> 看似为空或无法正确解析。',
        'preview_set': '链接预览设置为 {0}',
        'style_set': '消息样式设置为样式 {0}'
    }
}

def detect_language(update: Update):
    user_lang = update.effective_user.language_code or 'zh'
    return 'zh' if user_lang.startswith('zh') else 'en'

def get_text(lang, key, *args):
    return lang_dict.get(lang, lang_dict['zh'])[key].format(*args)

async def set_bot_commands(bot):
    commands_en = [
        BotCommand("start", "Start the bot and show help"),
        BotCommand("subscribe", "Add a new RSS feed"),
        BotCommand("unsubscribe", "Remove an RSS feed"),
        BotCommand("list", "Show your subscriptions"),
        BotCommand("set_interval", "Set check interval (seconds)"),
        BotCommand("pause", "Pause a feed"),
        BotCommand("resume", "Resume a feed"),
        BotCommand("set_filter", "Filter feed content"),
        BotCommand("set_preview", "Toggle link preview (on/off)"),
        BotCommand("set_style", "Set message style (1-3)"),
        BotCommand("feedback", "Send feedback"),
        BotCommand("get_latest", "Get latest updates"),
        BotCommand("help", "Show this help")
    ]
    commands_zh = [
        BotCommand("start", "启动机器人并显示帮助"),
        BotCommand("subscribe", "添加RSS订阅"),
        BotCommand("unsubscribe", "取消RSS订阅"),
        BotCommand("list", "查看订阅列表"),
        BotCommand("set_interval", "设置检查间隔（秒）"),
        BotCommand("pause", "暂停订阅"),
        BotCommand("resume", "恢复订阅"),
        BotCommand("set_filter", "过滤订阅内容"),
        BotCommand("set_preview", "开关链接预览（on/off）"),
        BotCommand("set_style", "设置消息样式（1-3）"),
        BotCommand("feedback", "发送反馈"),
        BotCommand("get_latest", "获取最新更新"),
        BotCommand("help", "显示此帮助")
    ]
    await bot.set_my_commands(commands=commands_en, language_code='en')
    await bot.set_my_commands(commands=commands_zh, language_code='zh')

def init_db():
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (chat_id INTEGER, is_channel BOOLEAN, url TEXT, interval INTEGER, 
                 paused BOOLEAN, last_checked INTEGER DEFAULT 0, filter_keyword TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (chat_id INTEGER PRIMARY KEY, link_preview BOOLEAN DEFAULT 1, message_style INTEGER DEFAULT 1, language TEXT DEFAULT 'en')''')
    c.execute('''CREATE TABLE IF NOT EXISTS sent_posts
                 (chat_id INTEGER, post_link TEXT, sent_time INTEGER, PRIMARY KEY (chat_id, post_link))''')
    try:
        c.execute("ALTER TABLE subscriptions ADD COLUMN last_checked INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE subscriptions ADD COLUMN filter_keyword TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE sent_posts ADD COLUMN sent_time INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE settings ADD COLUMN language TEXT DEFAULT 'en'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def add_subscription(chat_id, is_channel, url, interval=60, paused=False, filter_keyword=None):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT INTO subscriptions (chat_id, is_channel, url, interval, paused, last_checked, filter_keyword) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (chat_id, is_channel, url, interval, paused, 0, filter_keyword))
    finally:
        conn.close()

def remove_subscription(chat_id, is_channel, url):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("DELETE FROM subscriptions WHERE chat_id=? AND is_channel=? AND url=?", 
                     (chat_id, is_channel, url))
    finally:
        conn.close()

def get_subscriptions(chat_id, is_channel):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT url, interval, paused, last_checked, filter_keyword FROM subscriptions WHERE chat_id=? AND is_channel=?", 
                     (chat_id, is_channel))
            return c.fetchall()
    finally:
        conn.close()

def update_subscription(chat_id, is_channel, url, interval=None, paused=None, last_checked=None, filter_keyword=None):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            if interval is not None:
                c.execute("UPDATE subscriptions SET interval=? WHERE chat_id=? AND is_channel=? AND url=?", 
                         (interval, chat_id, is_channel, url))
            if paused is not None:
                c.execute("UPDATE subscriptions SET paused=? WHERE chat_id=? AND is_channel=? AND url=?", 
                         (paused, chat_id, is_channel, url))
            if last_checked is not None:
                c.execute("UPDATE subscriptions SET last_checked=? WHERE chat_id=? AND is_channel=? AND url=?", 
                         (last_checked, chat_id, is_channel, url))
            if filter_keyword is not None:
                c.execute("UPDATE subscriptions SET filter_keyword=? WHERE chat_id=? AND is_channel=? AND url=?", 
                         (filter_keyword, chat_id, is_channel, url))
    finally:
        conn.close()

def get_user_settings(chat_id):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT link_preview, message_style, language FROM settings WHERE chat_id=?", (chat_id,))
            result = c.fetchone()
            if result:
                return {'link_preview': bool(result[0]), 'message_style': result[1], 'language': result[2] or 'en'}
            else:
                c.execute("INSERT INTO settings (chat_id, link_preview, message_style, language) VALUES (?, 1, 1, 'en')", (chat_id,))
                conn.commit()
                return {'link_preview': True, 'message_style': 1, 'language': 'en'}
    finally:
        conn.close()

def update_user_settings(chat_id, link_preview=None, message_style=None, language=None):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO settings (chat_id, link_preview, message_style, language) VALUES (?, 1, 1, 'en')", (chat_id,))
            if link_preview is not None:
                c.execute("UPDATE settings SET link_preview=? WHERE chat_id=?", (int(link_preview), chat_id))
            if message_style is not None:
                c.execute("UPDATE settings SET message_style=? WHERE chat_id=?", (message_style, chat_id))
            if language is not None:
                c.execute("UPDATE settings SET language=? WHERE chat_id=?", (language, chat_id))
            conn.commit()
    finally:
        conn.close()

def save_sent_post(chat_id, post_link, sent_time):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO sent_posts (chat_id, post_link, sent_time) VALUES (?, ?, ?)", (chat_id, post_link, sent_time))
    finally:
        conn.close()

def is_post_sent(chat_id, post_link):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM sent_posts WHERE chat_id=? AND post_link=?", (chat_id, post_link))
            return c.fetchone() is not None
    finally:
        conn.close()

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text(get_text(detect_language(update), 'error', '你无权使用'), parse_mode=ParseMode.HTML)
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    welcome_msg = f"{get_text(lang, 'welcome')}\n\n{get_text(lang, 'help')}"
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML)
    await set_bot_commands(context.bot)

WAITING_URL, WAITING_UNSUBSCRIBE = range(2)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    await update.message.reply_text(get_text(lang, 'subscribe_prompt'), parse_mode=ParseMode.HTML)
    context.user_data['is_channel'] = update.effective_chat.type in ['channel', 'supergroup']
    return WAITING_URL

async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_channel = context.user_data.get('is_channel', False)
    lang = detect_language(update)
    url = update.message.text.strip()
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15), ssl=ssl_context) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                content = await response.text()
                logger.info(f"Response from {url}: {content[:1000]}")
        feed = feedparser.parse(content)
        if not feed.entries:
            logger.warning(f"No entries found in {url}. Feed structure: {feed}")
            await update.message.reply_text(get_text(lang, 'empty_feed', url), parse_mode=ParseMode.HTML)
        else:
            logger.info(f"Found {len(feed.entries)} entries in {url}")
            add_subscription(chat_id, is_channel, url)
            await update.message.reply_text(get_text(lang, 'subscribed', url), parse_mode=ParseMode.HTML)
    except asyncio.TimeoutError:
        await update.message.reply_text(get_text(lang, 'timeout', url), parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(get_text(lang, 'error', str(e)), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    lang = detect_language(update)
    subscriptions = get_subscriptions(chat_id, is_channel)
    if not subscriptions:
        await update.message.reply_text(get_text(lang, 'no_subscription'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(f"{i+1}. {url}", callback_data=f"unsub_{url}")] 
                for i, (url, _, _, _, _) in enumerate(subscriptions)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(lang, 'unsubscribe_prompt'), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return WAITING_UNSUBSCRIBE

async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    lang = detect_language(update)
    url = query.data.replace("unsub_", "")
    remove_subscription(chat_id, is_channel, url)
    await query.edit_message_text(get_text(lang, 'unsubscribed', url), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def list_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    lang = detect_language(update)
    subscriptions = get_subscriptions(chat_id, is_channel)
    if subscriptions:
        message = get_text(lang, 'list_subscriptions') + "\n"
        for i, (url, interval, paused, last_checked, filter_keyword) in enumerate(subscriptions, 1):
            status = "Paused" if paused else "Active" if lang == 'en' else "暂停" if paused else "活跃"
            filter_text = filter_keyword or "None"
            message += get_text(lang, 'status', i, url, status, interval, filter_text) + "\n"
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(get_text(lang, 'no_subscription'), parse_mode=ParseMode.HTML)

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if len(context.args) != 2 or not context.args[1].isdigit():
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /set_interval URL interval'), parse_mode=ParseMode.HTML)
        return
    url, interval = context.args
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    subscriptions = get_subscriptions(chat_id, is_channel)
    for sub_url, _, _, _, _ in subscriptions:
        if sub_url == url:
            update_subscription(chat_id, is_channel, url, interval=int(interval))
            await update.message.reply_text(get_text(lang, 'interval_set', url, interval), parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text(get_text(lang, 'not_found'), parse_mode=ParseMode.HTML)

async def pause_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if len(context.args) != 1:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /pause URL'), parse_mode=ParseMode.HTML)
        return
    url = context.args[0]
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    subscriptions = get_subscriptions(chat_id, is_channel)
    for sub_url, _, _, _, _ in subscriptions:
        if sub_url == url:
            update_subscription(chat_id, is_channel, url, paused=True)
            await update.message.reply_text(get_text(lang, 'paused', url), parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text(get_text(lang, 'not_found'), parse_mode=ParseMode.HTML)

async def resume_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if len(context.args) != 1:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /resume URL'), parse_mode=ParseMode.HTML)
        return
    url = context.args[0]
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    subscriptions = get_subscriptions(chat_id, is_channel)
    for sub_url, _, _, _, _ in subscriptions:
        if sub_url == url:
            update_subscription(chat_id, is_channel, url, paused=False)
            await update.message.reply_text(get_text(lang, 'resumed', url), parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text(get_text(lang, 'not_found'), parse_mode=ParseMode.HTML)

async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /set_filter URL keyword'), parse_mode=ParseMode.HTML)
        return
    url = context.args[0]
    keyword = ' '.join(context.args[1:])
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    subscriptions = get_subscriptions(chat_id, is_channel)
    for sub_url, _, _, _, _ in subscriptions:
        if sub_url == url:
            update_subscription(chat_id, is_channel, url, filter_keyword=keyword)
            await update.message.reply_text(f"Filter for <a href='{url}'>{url}</a> set to <code>{keyword}</code>", parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text(get_text(lang, 'not_found'), parse_mode=ParseMode.HTML)

async def set_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    chat_id = update.effective_chat.id
    if len(context.args) != 1 or context.args[0].lower() not in ['on', 'off']:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /set_preview on|off'), parse_mode=ParseMode.HTML)
        return
    preview = context.args[0].lower() == 'on'
    update_user_settings(chat_id, link_preview=preview)
    await update.message.reply_text(get_text(lang, 'preview_set', 'on' if preview else 'off'), parse_mode=ParseMode.HTML)

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    chat_id = update.effective_chat.id
    if len(context.args) != 1 or not context.args[0].isdigit() or int(context.args[0]) not in [1, 2, 3]:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /set_style 1|2|3'), parse_mode=ParseMode.HTML)
        return
    style = int(context.args[0])
    update_user_settings(chat_id, message_style=style)
    await update.message.reply_text(get_text(lang, 'style_set', style), parse_mode=ParseMode.HTML)

def clean_html(text):
    allowed_tags = ['b', 'i', 'u', 's', 'a', 'code', 'pre']
    pattern = r'</?(?!(' + '|'.join(allowed_tags) + r')\b)[a-zA-Z][a-zA-Z0-9]*\b[^>]*>'
    cleaned = re.sub(pattern, '', text)
    for tag in allowed_tags:
        cleaned = re.sub(f"<{tag}([^>]*)>(.*?)(?<!</{tag}>)$", r"<\g<0>>\2</{tag}>", cleaned, flags=re.DOTALL)
    return cleaned

def format_rss_update(entry, style=1):
    title = clean_html(entry.get('title', 'No title'))
    link = entry.get('link', '#')
    if style == 1:
        return f"<b>{title}</b>\n<a href='{link}'>{link}</a>"
    elif style == 2:
        return f"<b>{title}</b>\n🔗 <a href='{link}'>{link}</a>"
    elif style == 3:
        return f"📌 <b>{title}</b> [<a href='{link}'>Link</a>]"
    return f"<b>{title}</b>\n<a href='{link}'>{link}</a>"

async def check_latest_posts(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT chat_id, is_channel FROM subscriptions")
            chats = c.fetchall()
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession() as session:
            for chat_id, is_channel in chats:
                subscriptions = get_subscriptions(chat_id, is_channel)
                settings = get_user_settings(chat_id)
                lang = settings['language']
                for url, interval, paused, last_checked, filter_keyword in subscriptions:
                    if paused:
                        logger.info(f"Skipping paused feed: {url}")
                        continue
                    current_time = int(time.time())
                    if current_time - last_checked < interval:
                        logger.info(f"Skipping {url}, interval not reached")
                        continue
                    
                    logger.info(f"Checking feed {url}")
                    try:
                        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15), ssl=ssl_context) as response:
                            if response.status != 200:
                                logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                                await context.bot.send_message(chat_id, get_text(lang, 'feed_unhealthy', url), parse_mode=ParseMode.HTML)
                                continue
                            content = await response.text()
                            feed = feedparser.parse(content)
                        
                        if not feed.entries:
                            logger.info(f"No entries in feed from {url}: {content[:200]}")
                            await context.bot.send_message(chat_id, get_text(lang, 'empty_feed', url), parse_mode=ParseMode.HTML)
                            continue
                        
                        entries = sorted(
                            [e for e in feed.entries if e.get('published_parsed') or e.get('updated_parsed')],
                            key=lambda x: time.mktime(x.get('published_parsed') or x.get('updated_parsed')),
                            reverse=True
                        )
                        if not entries:
                            logger.info(f"No valid entries with timestamps in {url}")
                            continue
                        
                        for entry in entries[:1]:
                            post_link = entry.get('link', '#')
                            if not post_link:
                                logger.warning(f"Entry from {url} has no link: {entry}")
                                continue
                            
                            if filter_keyword and filter_keyword.lower() not in (entry.get('title', '') + entry.get('summary', '')).lower():
                                logger.info(f"Entry filtered out by '{filter_keyword}': {post_link}")
                                continue
                            
                            if not is_post_sent(chat_id, post_link):
                                formatted_entry = format_rss_update(entry, settings['message_style'])
                                logger.info(f"Sending entry from {url}: {formatted_entry[:200]}")
                                try:
                                    await context.bot.send_message(
                                        chat_id,
                                        formatted_entry,
                                        parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=not settings['link_preview']
                                    )
                                    save_sent_post(chat_id, post_link, current_time)
                                    logger.info(f"Marked as sent: {post_link}")
                                except Exception as e:
                                    logger.error(f"Failed to send {post_link}: {e}")
                            else:
                                logger.info(f"Post already sent: {post_link}")
                        
                        update_subscription(chat_id, is_channel, url, last_checked=current_time)
                    
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout fetching {url}")
                        await context.bot.send_message(chat_id, get_text(lang, 'timeout', url), parse_mode=ParseMode.HTML)
                    except Exception as e:
                        logger.error(f"Error checking {url}: {e}")
                        await context.bot.send_message(chat_id, get_text(lang, 'feed_unhealthy', url), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Unexpected error in check_latest_posts: {e}")
    finally:
        conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    await update.message.reply_text(get_text(lang, 'help'), parse_mode=ParseMode.HTML)

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, 'error', 'Usage: /feedback text'), parse_mode=ParseMode.HTML)
        return
    feedback_text = ' '.join(context.args)
    logger.info(f"Feedback from {update.effective_user.id}: {feedback_text}")
    await update.message.reply_text(get_text(lang, 'feedback_thanks'), parse_mode=ParseMode.HTML)

async def get_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    num_updates = 1 if not context.args else int(context.args[0]) if context.args and context.args[0].isdigit() else None
    if num_updates is None:
        await update.message.reply_text(get_text(lang, 'get_latest_prompt'), parse_mode=ParseMode.HTML)
        return
    subscriptions = get_subscriptions(chat_id, is_channel)
    if not subscriptions:
        await update.message.reply_text(get_text(lang, 'no_subscription'), parse_mode=ParseMode.HTML)
        return
    settings = get_user_settings(chat_id)
    await update.message.reply_text(get_text(lang, 'latest_updates', num_updates), parse_mode=ParseMode.HTML, disable_web_page_preview=not settings['link_preview'])
    updates_found = False
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession() as session:
        for url, _, _, _, filter_keyword in subscriptions:
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15), ssl=ssl_context) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                        continue
                    content = await response.text()
                    feed = feedparser.parse(content)
                    if not feed.entries:
                        logger.info(f"No entries in feed from {url}: {content[:200]}")
                        continue
                    logger.info(f"Found {len(feed.entries)} entries in {url}")
                    for entry in feed.entries[:num_updates]:
                        if filter_keyword and filter_keyword.lower() not in (entry.get('title', '') + entry.get('summary', '')).lower():
                            continue
                        formatted_entry = format_rss_update(entry, settings['message_style'])
                        logger.info(f"Sending entry from {url}: {formatted_entry[:200]}")
                        await update.message.reply_text(formatted_entry, parse_mode=ParseMode.HTML, disable_web_page_preview=not settings['link_preview'])
                        updates_found = True
            except Exception as e:
                logger.error(f"Get latest failed for {url}: {e}")
    if not updates_found:
        await update.message.reply_text(get_text(lang, 'no_updates'), parse_mode=ParseMode.HTML, disable_web_page_preview=not settings['link_preview'])

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_subscriptions))
    application.add_handler(CommandHandler("set_interval", set_interval))
    application.add_handler(CommandHandler("pause", pause_subscription))
    application.add_handler(CommandHandler("resume", resume_subscription))
    application.add_handler(CommandHandler("set_filter", set_filter))
    application.add_handler(CommandHandler("set_preview", set_preview))
    application.add_handler(CommandHandler("set_style", set_style))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("get_latest", get_latest))
    application.add_handler(CommandHandler("help", help_command))

    subscribe_handler = ConversationHandler(
        entry_points=[CommandHandler('subscribe', subscribe)],
        states={WAITING_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)]},
        fallbacks=[]
    )
    application.add_handler(subscribe_handler)

    unsubscribe_handler = ConversationHandler(
        entry_points=[CommandHandler('unsubscribe', unsubscribe)],
        states={WAITING_UNSUBSCRIBE: [CallbackQueryHandler(handle_unsubscribe)]},
        fallbacks=[]
    )
    application.add_handler(unsubscribe_handler)

    if application.job_queue is None:
        raise RuntimeError("JobQueue is not available.")
    
    application.job_queue.run_repeating(check_latest_posts, interval=20, first=0)

    application.run_polling()

if __name__ == '__main__':
    main()
