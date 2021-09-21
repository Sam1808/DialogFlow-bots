import logging
from google.cloud import dialogflow


def fetch_answer_from_intent(project_id, session_id, text, language_code, silent=False):
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
