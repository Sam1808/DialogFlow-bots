import argparse
import json
import time
import logging
import os
from google.cloud import dialogflow
from dotenv import load_dotenv


def list_intents(project_id):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)
    intents = intents_client.list_intents(request={"parent": parent})
    return intents


def delete_intent(project_id, intent_id):
    intents_client = dialogflow.IntentsClient()
    intent_path = intents_client.intent_path(project_id, intent_id)
    intents_client.delete_intent(request={"name": intent_path})


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
    dialogflow_project_id = os.environ['DIALOG-PROJECT-ID']
    base_qa_filename = os.environ['BASE_QA_FILENAME']

    input('Renew DialogFlow base?\npress Enter to continue\npress Ctrl+C to Cancel\n')
    logging.debug('Renew DialogFlow base')

    if not os.path.exists(base_qa_filename):
        logging.debug(f'\nSomething wrong with {base_qa_filename} file.\n')
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