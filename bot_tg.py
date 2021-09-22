import argparse
import logging
import os
from dotenv import load_dotenv
from bot_tools import fetch_answer_from_intent
from bot_tools import setup_logger
from functools import partial
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


logger = logging.getLogger('Logger')


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")


def _error(_, context):
    logger.info('Bot catch some exception. Need your attention.')
    logging.exception(context.error)


def send_answer(
        update,
        context,
        project_id: str,
        language: str
):
    session_id = f"tg-{update.message.from_user['id']}"
    reply = fetch_answer_from_intent(
        project_id, session_id, update.message.text, language
    )
    if reply:
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug',
        type=bool,
        default=False,
        help='Turn DEBUG mode on'
    )
    arguments = parser.parse_args()

    level = logging.DEBUG if arguments.debug else logging.INFO
    logging.basicConfig(level=level)

    load_dotenv()
    telegram_token = os.environ['TELEGRAM-TOKEN']
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    language = os.environ['LANGUAGE']
    telegram_log_token = os.environ['TELEGRAM-LOG-TOKEN']
    telegram_log_id = os.environ['TELEGRAM-LOG-ID']

    setup_logger(
        telegram_log_token,
        telegram_log_id,
        bot_name='Telegram bot'
    )

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    partial_send_answer = partial(
        send_answer,
        project_id=dialogflow_project_id,
        language=language
    )

    send_chat_message_handler = MessageHandler(
        Filters.text & (~Filters.command),
        partial_send_answer
    )
    dispatcher.add_handler(send_chat_message_handler)
    dispatcher.add_error_handler(_error)

    updater.start_polling()
