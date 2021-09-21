import argparse
import logging
import os
import uuid
from dotenv import load_dotenv
from bot_tools import fetch_answer_from_intent
from bot_tools import init_telegram_log_bot
from functools import partial
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


logger = logging.getLogger('Logger')


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")


def _error(_, context):
    logger.info('Bot catch some exception. Need your attention.')
    print('^' * 20)
    logging.exception(context.error)


def send_chat_message(
        update,
        context,
        project_id: str,
        session_id: str,
        language: str
):
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
    session_id = str(uuid.uuid4())

    init_telegram_log_bot(telegram_log_token, telegram_log_id, bot_name='Telegram bot')

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    partial_send_chat_message = partial(
        send_chat_message,
        project_id=dialogflow_project_id,
        session_id=session_id,
        language=language
    )

    send_chat_message_handler = MessageHandler(
        Filters.text & (~Filters.command),
        partial_send_chat_message
    )
    dispatcher.add_handler(send_chat_message_handler)
    dispatcher.add_error_handler(_error)

    updater.start_polling()
