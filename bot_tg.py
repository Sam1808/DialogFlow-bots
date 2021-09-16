import argparse
import json
import time
import logging
import os
import uuid
from google.cloud import dialogflow
from dotenv import load_dotenv
from functools import partial
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


load_dotenv()
GOOGLE_APPLICATION_CREDENTIALS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello!")


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


def create_intent(
        project_id, display_name, training_phrases_parts, message_texts
):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(
            text=training_phrases_part
        )
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)
    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message]
    )
    response = intents_client.create_intent(
        request={"parent": parent, "intent": intent}
    )
    print("Intent created: {}".format(response))


def list_intents(project_id):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)
    intents = intents_client.list_intents(request={"parent": parent})
    return intents


def delete_intent(project_id, intent_id):
    intents_client = dialogflow.IntentsClient()
    intent_path = intents_client.intent_path(project_id, intent_id)
    intents_client.delete_intent(request={"name": intent_path})


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--renew',
        type=bool,
        default=False,
        help='Overwrite DialogFlow base'
    )
    parser.add_argument(
        '--debug',
        type=bool,
        default=False,
        help='Turn DEBUG mode on'
    )
    arguments = parser.parse_args()

    level = logging.DEBUG if arguments.debug else logging.INFO
    logging.basicConfig(level=level)

    renew = arguments.renew
    logging.debug(f'Renew DialogFlow base status:{renew}')

    telegram_token = os.environ['TELEGRAM-TOKEN']
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    base_qa_filename = os.environ['BASE_QA_FILENAME']
    language = os.environ['LANGUAGE']
    session_id = str(uuid.uuid4())

    if renew:
        if not os.path.exists(base_qa_filename):
            logging.info(f'\nSomething wrong with {base_qa_filename} file.\n')
            raise FileExistsError

        for intent in list_intents(dialogflow_project_id):
            if 'Default' in intent.display_name:
                continue
            delete_intent(dialogflow_project_id, intent.name.split('/')[-1])
            time.sleep(3)  # limit 'All other requests per minute' of service 'dialogflow.googleapis.com'

        with open(base_qa_filename, 'r') as file:
            questions = json.load(file)

        for phrase_part in questions:
            create_intent(
                dialogflow_project_id,
                phrase_part,
                questions[phrase_part]['questions'],
                questions[phrase_part]['answer']
            )
            time.sleep(3)  # limit 'All other requests per minute' of service 'dialogflow.googleapis.com'

        logging.debug(f'DialogFlow base update complete.')

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

    echo_handler = MessageHandler(
        Filters.text & (~Filters.command),
        partial_send_chat_message
    )
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
