import argparse
import asyncio
import logging
import os

import aiogram
import watchgod

from . import config

Bot = None
MessageId = None
ChatId = None


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


async def on_file_modified(path: str):
    global Bot, MessageId, ChatId

    if MessageId is None or ChatId is None:
        logging.warning('No message to write to')
        return

    with open(path) as f:
        content = f.read()

    await Bot.edit_message_text(content, ChatId, MessageId)
    logging.info('Message updated succesfully')


async def watch_file_changes(watched_file: str):
    async for changes in watchgod.awatch(watched_file):
        for change, path in changes:
            if change == watchgod.Change.modified:
                await on_file_modified(path)


def main():
    global Bot

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

    aio_loop.create_task(watch_file_changes(cfg['watched_file']))
    aiogram.executor.start_polling(dispatcher, skip_updates=True)
