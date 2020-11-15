import argparse
import logging
import os

import aiogram

from . import config

Bot = None


def parse_args():
    parse = argparse.ArgumentParser()
    parse.add_argument('-c', '--config', type=str,
                       default='config.yaml', help='Path to config file')
    parse.add_argument('-l', '--logfile', type=str,
                       default=None, help='Path to log file')
    args = parse.parse_args()
    return args


async def handle_start(message: aiogram.types.Message):
    await message.bot.send_message(
        message.chat.id,
        'OK, this message will be changed when you change watched file')


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

    Bot = aiogram.Bot(token=cfg['bot_token'])
    dispatcher = aiogram.Dispatcher(Bot)

    dispatcher.register_message_handler(handle_start, commands=['start'])

    aiogram.executor.start_polling(dispatcher, skip_updates=True)
