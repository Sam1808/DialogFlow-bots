import argparse
import vk_api
import random
import logging
import os
import uuid
from google.cloud import dialogflow
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv


def fetch_answer_from_intent(project_id, session_id, text, language_code):
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
    if response.query_result.intent.is_fallback:
        logging.debug(f'Bot cant understand (is fallback). Text: {text}')
        return None
    return response.query_result.fulfillment_text


def send_chat_message(event, vk_api, project_id, session_id, language_code):
    reply = fetch_answer_from_intent(
        project_id,
        session_id,
        event.text,
        language_code
    )
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

    vk_session = vk_api.VkApi(token=vk_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            send_chat_message(
                event,
                vk_api,
                dialogflow_project_id,
                session_id,
                language
            )
