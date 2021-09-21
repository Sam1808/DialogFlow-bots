import argparse
import vk_api
import random
import logging
import os
from bot_tools import fetch_answer_from_intent
from bot_tools import init_telegram_log_bot
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType


logger = logging.getLogger('Logger')


def send_fetched_answer_to_chat(
        event,
        vk_api,
        project_id,
        language_code
):
    session_id = f'vk-{event.user_id}'
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
    telegram_log_token = os.environ['TELEGRAM-LOG-TOKEN']
    telegram_log_id = os.environ['TELEGRAM-LOG-ID']

    init_telegram_log_bot(
        telegram_log_token,
        telegram_log_id,
        bot_name='VK.com bot'
    )

    vk_session = vk_api.VkApi(token=vk_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    send_fetched_answer_to_chat(
                        event,
                        vk_api,
                        dialogflow_project_id,
                        language
                    )

        except Exception as error:
            logger.info('Bot catch some exception. Need your attention.')
            logging.exception(error)
