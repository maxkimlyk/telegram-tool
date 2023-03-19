import argparse
import asyncio
import logging
import os

import aiogram
import watchgod

from . import config
from . import utils

Bot = None
MessageId = None
ChatId = None

WatchedTextFilePath = None
WatchedButtonsFilePath = None


def parse_args():
    parse = argparse.ArgumentParser()
    parse.add_argument('-c', '--config', type=str,
                       default='config.yaml', help='Path to config file')
    parse.add_argument('-l', '--logfile', type=str,
                       default=None, help='Path to log file')
    args = parse.parse_args()
    return args


async def handle_start(message: aiogram.types.Message):
    global MessageId, ChatId

    sent_message = await message.bot.send_message(
        message.chat.id,
        'OK, this message will be changed when you change watched file')

    MessageId = sent_message.message_id
    ChatId = sent_message.chat.id

    logging.info(
        "Registered test message: message_id=%s, chat_id=%s",
        MessageId,
        ChatId)


async def handle_button(query: aiogram.types.CallbackQuery):
    logging.info("Button pressed: %s", query.data)
    await Bot.answer_callback_query(query.id)


def get_parse_mode(file_extension: str) -> str:
    default_parse_mode = ''
    parse_mode_by_extension = {
        'html': 'HTML',
        'md': 'MarkdownV2',
    }

    try:
        return parse_mode_by_extension[file_extension.lower()]
    except KeyError:
        return default_parse_mode


def load_text_from_file(path: str):
    with open(path) as f:
        text = f.read()

    extension = utils.get_file_extension(path)
    parse_mode = get_parse_mode(extension)

    return text, parse_mode


def trim_text(text: str, length: int) -> str:
    if len(text) < length:
        return text
    return text[:length]


def load_buttons_from_file(path: str):
    with open(path) as f:
        lines = f.readlines()

    lines = [l for l in lines if l != '']

    if not lines:
        return None

    markup = aiogram.types.InlineKeyboardMarkup()

    for line in lines:
        buttons = []
        for text in line.split('|'):
            text = text.strip()
            buttons.append(aiogram.types.InlineKeyboardButton(text, callback_data=trim_text(text, 32)))
        markup.row(*buttons)

    return markup


async def update_message_with_file_content():
    global Bot, MessageId, ChatId

    if MessageId is None or ChatId is None:
        logging.warning(
            'No registered message. '
            'Did you forget to send "/start" to your bot?'
        )
        return

    text, parse_mode = load_text_from_file(WatchedTextFilePath)
    reply_markup = load_buttons_from_file(WatchedButtonsFilePath)

    try:
        await Bot.edit_message_text(
            text, ChatId, MessageId, parse_mode=parse_mode
        )
        logging.info('Message updated succesfully %s',
                     '({})'.format(parse_mode) if parse_mode else '')
    except aiogram.utils.exceptions.MessageNotModified as exc:
        logging.debug('%s', exc)

    try:
        await Bot.edit_message_reply_markup(ChatId, MessageId, reply_markup=reply_markup)
    except aiogram.utils.exceptions.MessageNotModified as exc:
        logging.debug('%s', exc)


async def on_file_modified():
    global Bot, MessageId, ChatId

    try:
        await update_message_with_file_content()
    except BaseException as exc:
        logging.exception('Got exception')
        await Bot.edit_message_text(
            'Something went wrong: {}: {}'.format(repr(exc), str(exc)),
            ChatId,
            MessageId,
        )


async def watch_text_file_changes(watched_file: str):
    async for changes in watchgod.awatch(watched_file):
        for change, path in changes:
            if change == watchgod.Change.modified:
                await on_file_modified()


async def watch_buttons_file_changes(watched_file: str):
    async for changes in watchgod.awatch(watched_file):
        for change, path in changes:
            if change == watchgod.Change.modified:
                await on_file_modified()


def main():
    global Bot, WatchedTextFilePath, WatchedButtonsFilePath

    args = parse_args()

    logging.basicConfig(
        filename=args.logfile,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    cfg = config.load_config(args.config, os.environ)

    aio_loop = asyncio.get_event_loop()

    Bot = aiogram.Bot(token=cfg['bot_token'], loop=aio_loop)
    dispatcher = aiogram.Dispatcher(Bot)

    dispatcher.register_message_handler(handle_start, commands=['start'])
    dispatcher.register_callback_query_handler(handle_button)

    WatchedTextFilePath = cfg['watched_text_file']
    WatchedButtonsFilePath = cfg['watched_buttons_file']

    aio_loop.create_task(watch_text_file_changes(WatchedTextFilePath))
    aio_loop.create_task(watch_buttons_file_changes(WatchedButtonsFilePath))
    aiogram.executor.start_polling(dispatcher, skip_updates=True)
