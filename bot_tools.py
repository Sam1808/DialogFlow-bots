import logging
import telegram
from google.cloud import dialogflow

logger = logging.getLogger('Logger')


class TelegramLogsHandler(logging.Handler):

    def __init__(self, log_bot, chat_id, bot_name):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = log_bot
        self.name = bot_name
        self.tg_bot.send_message(
            chat_id=self.chat_id,
            text=f'{bot_name} LOG: started'
        )

    def emit(self, record):
        log_entry = f"{self.name} LOG: {self.format(record)}"
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def fetch_answer_from_intent(
        project_id,
        session_id,
        text,
        language_code,
        silent=False
):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    logging.info("Session path: {}\n".format(session))

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
    if response.query_result.intent.is_fallback and silent:
        logging.debug(f'Bot cant understand (is fallback). Text: {text}')
        return None
    return response.query_result.fulfillment_text


def init_telegram_log_bot(telegram_log_token, telegram_log_id, bot_name):
    logger.setLevel(logging.INFO)
    bot = telegram.Bot(token=telegram_log_token)
    logger.addHandler(TelegramLogsHandler(
        bot,
        telegram_log_id,
        bot_name))
