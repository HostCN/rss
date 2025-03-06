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
from telegram.error import BadRequest
from playwright.async_api import async_playwright
from asyncio import Semaphore
from collections import deque

# 限制同时运行的 Playwright 实例
MAX_CONCURRENT_BROWSERS = 2
semaphore = Semaphore(MAX_CONCURRENT_BROWSERS)

# 批量处理消息的队列
message_queue = deque()
BATCH_SIZE = 10  # 每批处理的消息数量
BATCH_INTERVAL = 5  # 每批处理间隔（秒）

TOKEN = 'bot'
AUTHORIZED_USERS = ['8111870448', '7554663120']

# 日志设置
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.google.com/',
}

# 多语言支持
lang_dict = {
    'en': {
        'welcome': 'Welcome to RSS Bot! Here are the available commands:',
        'subscribe_prompt': 'Send RSS URL (or @ChannelName URL for channel subscription):',
        'unsubscribe_prompt': 'Select a feed to unsubscribe:',
        'no_subscription': 'No subscriptions yet.',
        'subscribed': 'Subscribed to <a href="{0}">{0}</a>{1}',
        'unsubscribed': 'Unsubscribed from <a href="{0}">{0}</a>',
        'invalid_choice': 'Invalid choice.',
        'interval_set': 'Interval for <a href="{0}">{0}</a> set to <code>{1}</code> seconds.',
        'not_found': 'Feed not found.',
        'paused': 'Paused <a href="{0}">{0}</a>.',
        'resumed': 'Resumed <a href="{0}">{0}</a>.',
        'list_subscriptions': 'Your subscriptions:',
        'status': '{0}. <a href="{1}">{1}</a> - <i>{2}</i> - Interval: <code>{3}</code>s - Filter: <code>{4}</code> - Chat: {5}',
        'help': '<b>Available Commands:</b>\n'
                '<b>/start</b> - Start the bot and show help\n'
                '<b>/subscribe</b> - Add RSS feed (URL or @ChannelName URL)\n'
                '<b>/unsubscribe</b> - Remove an RSS feed\n'
                '<b>/list</b> - Show your subscriptions\n'
                '<b>/set_interval URL interval</b> - Set check interval (seconds)\n'
                '<b>/pause URL</b> - Pause a feed\n'
                '<b>/resume URL</b> - Resume a feed\n'
                '<b>/set_filter URL keyword</b> - Filter feed content\n'
                '<b>/set_preview on|off</b> - Toggle link preview\n'
                '<b>/set_style 1|2|3|4|5|6</b> - Set message style\n'
                '<b>/show_styles</b> - Show available message styles\n'
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
        'style_set': 'Message style set to Style {0}',
        'styles_preview': 'Available message styles:\n{0}'
    },
    'zh': {
        'welcome': '欢迎使用RSS机器人！以下是可用命令：',
        'subscribe_prompt': '发送RSS URL（或@ChannelName URL用于频道订阅）：',
        'unsubscribe_prompt': '选择要取消订阅的feed：',
        'no_subscription': '你还没有订阅任何feed。',
        'subscribed': '已订阅 <a href="{0}">{0}</a>{1}',
        'unsubscribed': '已取消订阅 <a href="{0}">{0}</a>',
        'invalid_choice': '无效选择。',
        'interval_set': '已将 <a href="{0}">{0}</a> 的间隔设置为 <code>{1}</code>秒。',
        'not_found': '未找到该feed。',
        'paused': '已暂停 <a href="{0}">{0}</a>。',
        'resumed': '已恢复 <a href="{0}">{0}</a>。',
        'list_subscriptions': '你的订阅列表：',
        'status': '{0}. <a href="{1}">{1}</a> - <i>{2}</i> - 间隔：<code>{3}</code>秒 - 过滤：<code>{4}</code> - 聊天：{5}',
        'help': '<b>可用命令：</b>\n'
                '<b>/start</b> - 启动机器人并显示帮助\n'
                '<b>/subscribe</b> - 添加RSS订阅（URL或@ChannelName URL）\n'
                '<b>/unsubscribe</b> - 取消RSS订阅\n'
                '<b>/list</b> - 查看订阅列表\n'
                '<b>/set_interval URL 间隔</b> - 设置检查间隔（秒）\n'
                '<b>/pause URL</b> - 暂停订阅\n'
                '<b>/resume URL</b> - 恢复订阅\n'
                '<b>/set_filter URL 关键词</b> - 过滤订阅内容\n'
                '<b>/set_preview on|off</b> - 开关链接预览\n'
                '<b>/set_style 1|2|3|4|5|6</b> - 设置消息样式\n'
                '<b>/show_styles</b> - 显示可用消息样式\n'
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
        'style_set': '消息样式设置为样式 {0}',
        'styles_preview': '可用消息样式：\n{0}'
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
        BotCommand("set_style", "Set message style (1-6)"),
        BotCommand("show_styles", "Show available message styles"),
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
        BotCommand("set_style", "设置消息样式（1-6）"),
        BotCommand("show_styles", "显示可用消息样式"),
        BotCommand("feedback", "发送反馈"),
        BotCommand("get_latest", "获取最新更新"),
        BotCommand("help", "显示此帮助")
    ]
    await bot.set_my_commands(commands=commands_en, language_code='en')
    await bot.set_my_commands(commands=commands_zh, language_code='zh')

# 数据库连接池，修复closed属性问题
class DatabasePool:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.is_closed = True  # 手动追踪连接状态
        self.lock = asyncio.Lock()

    async def get_conn(self):
        async with self.lock:
            if self.conn is None or self.is_closed:
                self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
                self.is_closed = False
            return self.conn

    async def close(self):
        async with self.lock:
            if self.conn and not self.is_closed:
                self.conn.close()
                self.is_closed = True
                self.conn = None

db_pool = DatabasePool('subscriptions.db')

# 初始化数据库
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
    # 添加索引以加快查询速度
    c.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_chat_id ON subscriptions(chat_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sent_posts_chat_id ON sent_posts(chat_id)')
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

async def batch_update_subscriptions(updates):
    conn = await db_pool.get_conn()
    try:
        with conn:
            c = conn.cursor()
            for update in updates:
                chat_id, is_channel, url, last_checked = update
                c.execute("UPDATE subscriptions SET last_checked=? WHERE chat_id=? AND is_channel=? AND url=?", 
                         (last_checked, chat_id, is_channel, url))
    except Exception as e:
        logger.error(f"批量更新订阅失败: {e}")
        raise

async def batch_save_sent_posts(posts):
    conn = await db_pool.get_conn()
    try:
        with conn:
            c = conn.cursor()
            c.executemany("INSERT OR IGNORE INTO sent_posts (chat_id, post_link, sent_time) VALUES (?, ?, ?)", posts)
    except Exception as e:
        logger.error(f"批量保存已发送帖子失败: {e}")
        raise

def add_subscription(chat_id, is_channel, url, interval=60, paused=False, filter_keyword=None):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT INTO subscriptions (chat_id, is_channel, url, interval, paused, last_checked, filter_keyword) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (chat_id, is_channel, url, interval, paused, 0, filter_keyword))
    except Exception as e:
        logger.error(f"添加订阅失败: {e}")
    finally:
        conn.close()

def remove_subscription(chat_id, is_channel, url):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("DELETE FROM subscriptions WHERE chat_id=? AND is_channel=? AND url=?", 
                     (chat_id, is_channel, url))
    except Exception as e:
        logger.error(f"移除订阅失败: {e}")
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
    except Exception as e:
        logger.error(f"获取订阅失败: {e}")
        return []
    finally:
        conn.close()

def get_all_subscriptions():
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT chat_id, is_channel, url, interval, paused, last_checked, filter_keyword FROM subscriptions")
            return c.fetchall()
    except Exception as e:
        logger.error(f"获取所有订阅失败: {e}")
        return []
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
    except Exception as e:
        logger.error(f"更新订阅失败: {e}")
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
    except Exception as e:
        logger.error(f"获取用户设置失败: {e}")
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
    except Exception as e:
        logger.error(f"更新用户设置失败: {e}")
    finally:
        conn.close()

def save_sent_post(chat_id, post_link, sent_time):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO sent_posts (chat_id, post_link, sent_time) VALUES (?, ?, ?)", (chat_id, post_link, sent_time))
    except Exception as e:
        logger.error(f"保存已发送帖子失败: {e}")
    finally:
        conn.close()

def is_post_sent(chat_id, post_link):
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    try:
        with conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM sent_posts WHERE chat_id=? AND post_link=?", (chat_id, post_link))
            return c.fetchone() is not None
    except Exception as e:
        logger.error(f"检查帖子是否已发送失败: {e}")
        return False
    finally:
        conn.close()

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = str(update.effective_user.id)
    logger.info(f"检查用户授权，user_id={user_id}")
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text(get_text(detect_language(update), 'error', '你未被授权'), parse_mode=ParseMode.HTML)
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
    logger.info(f"开始订阅流程，chat_id={update.effective_chat.id}")
    await update.message.reply_text(get_text(lang, 'subscribe_prompt'), parse_mode=ParseMode.HTML)
    context.user_data['chat_id'] = update.effective_chat.id
    return WAITING_URL

async def fetch_feed_with_playwright(url):
    retries = 2
    for attempt in range(retries):
        async with semaphore:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
                    context = await browser.new_context(user_agent=HEADERS['User-Agent'])
                    page = await context.new_page()
                    await page.goto(url, timeout=30000)
                    content = await page.content()
                    await browser.close()
                    if "<rss" not in content and "<feed" not in content:
                        logger.warning(f"链接 {url} 返回的内容不像是 RSS: {content[:200]}")
                        return None
                    return content
            except Exception as e:
                logger.error(f"Playwright 错误，链接 {url}: {e}")
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)
    return None

async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_language(update)
    text = update.message.text.strip().split()
    chat_id = context.user_data.get('chat_id', update.effective_chat.id)
    is_channel = False
    url = text[0]

    if len(text) > 1 and text[0].startswith('@'):
        try:
            channel = await context.bot.get_chat(text[0])
            chat_id = channel.id
            is_channel = True
            url = text[1]
        except Exception as e:
            await update.message.reply_text(get_text(lang, 'error', f"无效频道: {e}"), parse_mode=ParseMode.HTML)
            return ConversationHandler.END

    try:
        content = await fetch_feed_with_playwright(url)
        if content is None:
            await update.message.reply_text(get_text(lang, 'timeout', url), parse_mode=ParseMode.HTML)
            return ConversationHandler.END

        feed = feedparser.parse(content)
        if not feed.entries:
            logger.warning(f"链接 {url} 无条目。Feed 结构: {feed}")
            await update.message.reply_text(get_text(lang, 'empty_feed', url), parse_mode=ParseMode.HTML)
        else:
            logger.info(f"在 {url} 中找到 {len(feed.entries)} 个条目")
            add_subscription(chat_id, is_channel, url)
            channel_info = f" for channel {text[0]}" if is_channel else ""
            await update.message.reply_text(get_text(lang, 'subscribed', url, channel_info), parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(get_text(lang, 'error', str(e)), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    logger.info(f"用户触发取消订阅命令，user_id={update.effective_user.id}")
    subscriptions = get_all_subscriptions()
    if not subscriptions:
        logger.info("未找到订阅")
        await update.message.reply_text(get_text(lang, 'no_subscription'), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    keyboard = []
    for idx, (chat_id, is_channel, url, _, _, _, _) in enumerate(subscriptions):
        button_text = f"{chat_id} - {url[:30]}..." if len(url) > 30 else f"{chat_id} - {url}"
        callback_data = f"unsub_{idx}"
        logger.info(f"按钮 {idx}: text={button_text}, callback_data={callback_data}")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(get_text(lang, 'unsubscribe_prompt'), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        logger.info(f"发送取消订阅选项，包含 {len(keyboard)} 个按钮")
    except BadRequest as e:
        logger.error(f"无法发送取消订阅消息: {e}")
        await update.message.reply_text(get_text(lang, 'error', '无法生成取消订阅选项'), parse_mode=ParseMode.HTML)
    return WAITING_UNSUBSCRIBE

async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = detect_language(update)
    logger.info(f"处理取消订阅回调: {query.data}")
    
    try:
        parts = query.data.split('_')
        if len(parts) != 2 or parts[0] != 'unsub':
            raise ValueError("无效的回调数据格式")
        idx = int(parts[1])
        
        subscriptions = get_all_subscriptions()
        if idx < 0 or idx >= len(subscriptions):
            raise ValueError("无效的订阅索引")
        
        chat_id, is_channel, url, _, _, _, _ = subscriptions[idx]
        remove_subscription(chat_id, is_channel, url)
        logger.info(f"取消订阅: chat_id={chat_id}, is_channel={is_channel}, url={url}")
        await query.edit_message_text(get_text(lang, 'unsubscribed', url), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"handle_unsubscribe 中出错: {e}")
        await query.edit_message_text(get_text(lang, 'error', str(e)), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def list_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    subscriptions = get_all_subscriptions()
    if subscriptions:
        message = get_text(lang, 'list_subscriptions') + "\n"
        for i, (chat_id, is_channel, url, interval, paused, last_checked, filter_keyword) in enumerate(subscriptions, 1):
            status = "Paused" if paused else "Active" if lang == 'en' else "暂停" if paused else "活跃"
            filter_text = filter_keyword or "None"
            chat_type = "Channel" if is_channel else "Private" if lang == 'en' else "频道" if is_channel else "私人"
            message += get_text(lang, 'status', i, url, status, interval, filter_text, f"{chat_type} ({chat_id})") + "\n"
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(get_text(lang, 'no_subscription'), parse_mode=ParseMode.HTML)

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    if len(context.args) != 2 or not context.args[1].isdigit():
        await update.message.reply_text(get_text(lang, 'error', '用法: /set_interval URL interval'), parse_mode=ParseMode.HTML)
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
        await update.message.reply_text(get_text(lang, 'error', '用法: /pause URL'), parse_mode=ParseMode.HTML)
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
        await update.message.reply_text(get_text(lang, 'error', '用法: /resume URL'), parse_mode=ParseMode.HTML)
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
        await update.message.reply_text(get_text(lang, 'error', '用法: /set_filter URL keyword'), parse_mode=ParseMode.HTML)
        return
    url = context.args[0]
    keyword = ' '.join(context.args[1:])
    chat_id = update.effective_chat.id
    is_channel = update.effective_chat.type in ['channel', 'supergroup']
    subscriptions = get_subscriptions(chat_id, is_channel)
    for sub_url, _, _, _, _ in subscriptions:
        if sub_url == url:
            update_subscription(chat_id, is_channel, url, filter_keyword=keyword)
            await update.message.reply_text(f"过滤器为 <a href='{url}'>{url}</a> 设置为 <code>{keyword}</code>", parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text(get_text(lang, 'not_found'), parse_mode=ParseMode.HTML)

async def set_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    chat_id = update.effective_chat.id
    if len(context.args) != 1 or context.args[0].lower() not in ['on', 'off']:
        await update.message.reply_text(get_text(lang, 'error', '用法: /set_preview on|off'), parse_mode=ParseMode.HTML)
        return
    preview = context.args[0].lower() == 'on'
    update_user_settings(chat_id, link_preview=preview)
    await update.message.reply_text(get_text(lang, 'preview_set', 'on' if preview else 'off'), parse_mode=ParseMode.HTML)

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    chat_id = update.effective_chat.id
    if len(context.args) != 1 or not context.args[0].isdigit() or int(context.args[0]) not in [1, 2, 3, 4, 5, 6]:
        await update.message.reply_text(get_text(lang, 'error', '用法: /set_style 1|2|3|4|5|6'), parse_mode=ParseMode.HTML)
        return
    style = int(context.args[0])
    update_user_settings(chat_id, message_style=style)
    await update.message.reply_text(get_text(lang, 'style_set', style), parse_mode=ParseMode.HTML)

async def show_styles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return
    lang = detect_language(update)
    example_entry = {'title': '示例标题', 'link': 'https://example.com'}
    styles = [
        f"样式 1:\n{format_rss_update(example_entry, 1)[0]}",
        f"样式 2:\n{format_rss_update(example_entry, 2)[0]}",
        f"样式 3:\n{format_rss_update(example_entry, 3)[0]}",
        f"样式 4:\n{format_rss_update(example_entry, 4)[0]}",
        f"样式 5:\n{format_rss_update(example_entry, 5)[0]}",
        f"样式 6:\n{format_rss_update(example_entry, 6)[0]}"
    ]
    await update.message.reply_text(get_text(lang, 'styles_preview', '\n\n'.join(styles)), parse_mode=ParseMode.HTML)

def clean_html(text):
    allowed_tags = ['b', 'i', 'u', 's', 'a', 'code', 'pre']
    pattern = r'</?(?!(' + '|'.join(allowed_tags) + r')\b)[a-zA-Z][a-zA-Z0-9]*\b[^>]*>'
    cleaned = re.sub(pattern, '', text)
    for tag in allowed_tags:
        cleaned = re.sub(f"<{tag}([^>]*)>(.*?)(?<!</{tag}>)$", r"<\g<0>>\2</{tag}>", cleaned, flags=re.DOTALL)
    return cleaned

def format_rss_update(entry, style=1):
    title = clean_html(entry.get('title', '无标题'))
    link = entry.get('link', '#')
    if style == 1:
        return f"<b>{title}</b>\n<a href='{link}'>{link}</a>", link
    elif style == 2:
        return f"<b>{title}</b>\n🔗 <a href='{link}'>{link}</a>", link
    elif style == 3:
        return f"📌 <b>{title}</b> [<a href='{link}'>链接</a>]", link
    elif style == 4:
        return f"✨ <i>{title}</i>\n🌐 <a href='{link}'>{link}</a>", link
    elif style == 5:
        return f"<code>{title}</code>\n📎 <a href='{link}'>阅读更多</a>", link
    elif style == 6:
        return f"<a href='{link}'>{title}</a>", link
    return f"<b>{title}</b>\n<a href='{link}'>{link}</a>", link

async def process_message_queue(context: ContextTypes.DEFAULT_TYPE):
    while message_queue:
        batch = []
        for _ in range(min(BATCH_SIZE, len(message_queue))):
            batch.append(message_queue.popleft())
        
        # 按时间戳排序
        batch.sort(key=lambda x: x['timestamp'])
        
        sent_posts = []
        for item in batch:
            chat_id = item['chat_id']
            message = item['message']
            disable_preview = item['disable_preview']
            post_link = item['post_link']
            sent_time = item['timestamp']
            
            try:
                await context.bot.send_message(
                    chat_id,
                    message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=disable_preview
                )
                sent_posts.append((chat_id, post_link, sent_time))
            except Exception as e:
                logger.error(f"发送消息失败，chat_id={chat_id}: {e}")
        
        if sent_posts:
            await batch_save_sent_posts(sent_posts)

async def check_latest_posts(context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = await db_pool.get_conn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT chat_id, is_channel FROM subscriptions")
            chats = c.fetchall()
        
        updates_to_commit = []
        for chat_id, is_channel in chats:
            subscriptions = get_subscriptions(chat_id, is_channel)
            settings = get_user_settings(chat_id)
            lang = settings['language']
            
            for url, interval, paused, last_checked, filter_keyword in subscriptions:
                if paused:
                    logger.info(f"跳过暂停的链接: {url}")
                    continue
                current_time = int(time.time())
                if current_time - last_checked < interval:
                    logger.info(f"跳过 {url}，未到检查间隔")
                    continue
                
                logger.info(f"检查链接 {url}，chat_id={chat_id}")
                try:
                    content = await fetch_feed_with_playwright(url)
                    if content is None:
                        logger.error(f"无法获取链接 {url} 的内容")
                        await context.bot.send_message(
                            chat_id,
                            get_text(lang, 'feed_unhealthy', url),
                            parse_mode=ParseMode.HTML
                        )
                        continue

                    feed = feedparser.parse(content)
                    if not feed.entries:
                        logger.info(f"链接 {url} 无条目: {content[:200]}")
                        await context.bot.send_message(
                            chat_id,
                            get_text(lang, 'empty_feed', url),
                            parse_mode=ParseMode.HTML
                        )
                        continue
                    
                    entries = sorted(
                        [e for e in feed.entries if e.get('published_parsed') or e.get('updated_parsed')],
                        key=lambda x: time.mktime(x.get('published_parsed') or x.get('updated_parsed')),
                        reverse=True
                    )
                    if not entries:
                        logger.info(f"链接 {url} 无有效时间戳的条目")
                        continue
                    
                    for entry in entries[:10]:
                        post_link = entry.get('link', '#')
                        if not post_link:
                            logger.warning(f"链接 {url} 的条目无链接: {entry}")
                            continue
                        
                        if filter_keyword and filter_keyword.lower() not in (entry.get('title', '') + entry.get('summary', '')).lower():
                            logger.info(f"条目被过滤，关键字 '{filter_keyword}': {post_link}")
                            continue
                        
                        if not is_post_sent(chat_id, post_link):
                            formatted_entry, link = format_rss_update(entry, settings['message_style'])
                            timestamp = int(time.mktime(entry.get('published_parsed') or entry.get('updated_parsed') or time.gmtime()))
                            message_queue.append({
                                'chat_id': chat_id,
                                'message': formatted_entry,
                                'disable_preview': not settings['link_preview'],
                                'post_link': link,
                                'timestamp': timestamp
                            })
                    
                    updates_to_commit.append((chat_id, is_channel, url, current_time))
                
                except Exception as e:
                    logger.error(f"检查 {url} 时出错: {e}")
                    await context.bot.send_message(
                        chat_id,
                        get_text(lang, 'feed_unhealthy', url),
                        parse_mode=ParseMode.HTML
                    )
        
        if updates_to_commit:
            await batch_update_subscriptions(updates_to_commit)
        
        if message_queue:
            await process_message_queue(context)
    
    except Exception as e:
        logger.error(f"check_latest_posts 中发生意外错误: {e}")
        # Optionally, re-raise to let the job queue handle it
        # raise

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
        await update.message.reply_text(get_text(lang, 'error', '用法: /feedback text'), parse_mode=ParseMode.HTML)
        return
    feedback_text = ' '.join(context.args)
    logger.info(f"来自 {update.effective_user.id} 的反馈: {feedback_text}")
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
    for url, _, _, _, filter_keyword in subscriptions:
        try:
            content = await fetch_feed_with_playwright(url)
            if content is None:
                logger.error(f"无法获取链接 {url} 的内容")
                continue

            feed = feedparser.parse(content)
            if not feed.entries:
                logger.info(f"链接 {url} 无条目: {content[:200]}")
                continue
            logger.info(f"在 {url} 中找到 {len(feed.entries)} 个条目")
            for entry in feed.entries[:num_updates]:
                if filter_keyword and filter_keyword.lower() not in (entry.get('title', '') + entry.get('summary', '')).lower():
                    continue
                formatted_entry, _ = format_rss_update(entry, settings['message_style'])
                logger.info(f"发送条目，来自 {url}: {formatted_entry[:200]}")
                await update.message.reply_text(formatted_entry, parse_mode=ParseMode.HTML, disable_web_page_preview=not settings['link_preview'])
                updates_found = True
        except Exception as e:
            logger.error(f"获取最新条目失败，链接 {url}: {e}")
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
    application.add_handler(CommandHandler("show_styles", show_styles))
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
        raise RuntimeError("JobQueue 不可用。")
    
    application.job_queue.run_repeating(check_latest_posts, interval=30, first=0)

    application.run_polling()

if __name__ == '__main__':
    main()
