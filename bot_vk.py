import argparse
import vk_api
import random
import logging
import os
import time
import uuid
from bot_tools import fetch_answer_from_intent
from vk_api.longpoll import VkLongPoll, VkEventType
from requests.exceptions import ReadTimeout
from dotenv import load_dotenv

from bot_tg import init_telegram_log_bot

logger = logging.getLogger('Logger')


def send_chat_message(event, vk_api, project_id, session_id, language_code):
    reply = fetch_answer_from_intent(
        project_id,
        session_id,
        event.text,
        language_code,
        silent=True
    )
    logging.debug(f'Reply: {reply}')
    if reply:
        vk_api.messages.send(
            user_id=event.user_id,
            message=reply,
            random_id=random.randint(1, 1000)
        )


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
    vk_token = os.environ['VK-TOKEN']
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    language = os.environ['LANGUAGE']
    session_id = str(uuid.uuid4())

    init_telegram_log_bot(bot_name='VK.com bot')

    vk_session = vk_api.VkApi(token=vk_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    send_chat_message(
                        event,
                        vk_api,
                        dialogflow_project_id,
                        session_id,
                        language
                    )
        except ReadTimeout:
            logging.debug(f'''
            ReadTimeout or Connection error.
            Re-request after 60 sec.
            ''')
            time.sleep(60)

        except Exception as error:
            print('^' * 20)
            logger.info('Bot catch some exception. Need your attention.')
            logging.exception(error)
