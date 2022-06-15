import logging
from setuptools import Command
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, Defaults,
    InlineQueryHandler
)

# from urllib.parse import urlparse, urljoin
import re

from session import Session
from config import TOKEN

""" 个人处理、存储链接的 Telegram Bot
数据库: mongoDB.
    统一放在 `htmls` 数据库中. 根据不同的链接类型再分类保存在 `xiaoyuzhou_episode_info, arxiv_paper_info, github_repo_info` 等表中
指令说明: 见 HELP

https://github.com/python-telegram-bot/python-telegram-bot

APIs
Telegram: https://core.telegram.org/bots/api
GitHub: https://docs.github.com/en/rest
ArXiv: https://github.com/lukasschwab/arxiv.py

"""

RE_LINK = re.compile(r'(https?://[^\s]+)')
RE_INT = re.compile(r'(\d+)')

HELP = """ 
/help - show this help
/help_supported_links - show supported link types
/latest {n} - get the latest n links
"""

SUBBPORTED_LINKS = """
https://www.xiaoyuzhoufm.com/episode/62a3739bb32f552f54730f2a
https://arxiv.org/abs/2206.04673
https://github.com/Vincentqyw/cv-arxiv-daily
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Send a message when the command /start is issued. """
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm here! Give me the links")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=HELP)

async def help_supported_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=SUBBPORTED_LINKS)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # context.args
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def resolve_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ 主体处理函数的逻辑 """
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Resolving urls...")
    # extract all urls
    urls = re.findall(RE_LINK, update.message.text)
    for url in urls:
        
        code, info = session.resolve_url(url)
        if code < 0:
            text=f"Error: {url}... error info: {info}"
        else:
            text = f"{url} -> {info}"
        # 统一在 session 中的处理函数中记录 logging
        # logging.info(f"\t{text}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    # await context.bot.send_message(chat_id=update.effective_chat.id, text="Done!")

async def get_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    integers = re.findall(RE_INT, " ".join(context.args))
    num = max(integers[0], 20) if integers else 5
    code, info = session.get_latest(num)
    if code<0: text = f"Error: {info}"
    else: text = f"latest {num} links:\n{info}"
    # logging.info(f"\t{text}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    

if __name__ == '__main__':
    # proxy_url = "http://localhost:7890"
    # ApplicationBuilder().token(TOKEN).proxy_url(proxy_url)
    session = Session()
    defaults = Defaults(disable_web_page_preview=True)
    application = ApplicationBuilder().token(TOKEN).defaults(defaults).build()
    
    
    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    # caps_handler = CommandHandler('caps', caps)
    
    # 处理指令
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('help_supported_links', help_supported_links))
    application.add_handler(CommandHandler('latest', get_latest))
    # application.add_handler(echo_handler)
    # application.add_handler(caps_handler)
    # 注意：需要在最后被加入到 application 中, 否则会接管所有 Command
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    # 处理消息
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), resolve_url))
    
    application.run_polling()