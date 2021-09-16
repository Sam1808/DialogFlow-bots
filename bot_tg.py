import argparse
import logging
import os
import telegram
import uuid
from google.cloud import dialogflow
from dotenv import load_dotenv
from functools import partial
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


logger = logging.getLogger('Logger')


class TelegramLogsHandler(logging.Handler):

    def __init__(self, log_bot, chat_id, bot_name):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = log_bot
        self.name = bot_name
        self.tg_bot.send_message(chat_id=self.chat_id, text=f'{bot_name} LOG: started')

    def emit(self, record):
        log_entry = f"{self.name} LOG: {self.format(record)}"
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")


def _error(update, context):
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
        project_id, session_id, [update.message.text], language
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply)


def fetch_answer_from_intent(project_id, session_id, texts, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    logging.info("Session path: {}\n".format(session))
    for text in texts:
        text_input = dialogflow.TextInput(
            text=text, language_code=language_code
        )
        query_input = dialogflow.QueryInput(text=text_input)
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        logging.info("=" * 20)
        logging.info(
            "Input: {}".format(response.query_result.query_text)
        )
        logging.info(
            "Output: {}".format(response.query_result.fulfillment_text)
        )
        return response.query_result.fulfillment_text


def init_telegram_log_bot(bot_name='Telegram bot'):
    logger.setLevel(logging.INFO)
    telegram_log_token = os.environ['TELEGRAM-LOG-TOKEN']
    telegram_log_id = os.environ['TELEGRAM-LOG-ID']
    bot = telegram.Bot(token=telegram_log_token)
    logger.addHandler(TelegramLogsHandler(
        bot,
        telegram_log_id,
        bot_name))


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
    base_qa_filename = os.environ['BASE_QA_FILENAME']
    language = os.environ['LANGUAGE']
    session_id = str(uuid.uuid4())

    init_telegram_log_bot()

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
