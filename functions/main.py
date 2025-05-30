import json
import boto3
import logging
import urllib3
import os
from getConfig import get_config

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
BUCKET_NAME: str = os.environ["BUCKET_NAME"]

# Setup Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Setup Bedrock
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.resource('s3')

bucket = s3.Bucket(BUCKET_NAME)

# Http 
http = urllib3.PoolManager()

system_prompt = "You are a helpful AI Assistant that will answer all questions and queries as accurately as possible. You can use only the following HTML tags to highligh the response text: <b>, <i>, <u>, <code>, <pre>, <a>; otherwise the answer must be a plain text without formatting."

def lambda_handler(event,context):
    ''' Main Logic '''

    # Pull input from event
    details = event['detail']
    print(details)
    print(type(details))
    chat_id = details['message']['chat']['id']
    username = details['message']['chat']['username']
    user_input = details['message']['text']

    logger.info(f"Chat ID: {chat_id}, Username: {username}, User Prompt: {user_input}")

    # Get config from s3
    config, model = get_config(chat_id)

    # Get message history from S3
    try:
        message_history = json.loads(bucket.Object(f"{chat_id}-history.json").get()['Body'].read().decode('utf-8'))
    except:
        message_history = []

    # Prepare Message
    message = message_prep(user_input)

    # Add message to message history
    message_history.append(message)

    # Send to Bedrock
    try:
        response = bedrock.converse_stream(
            modelId=model["modelId"],
            messages=message_history,
            inferenceConfig=config,
            system=[{"text":system_prompt}],
        )

        stream_response = response.get('stream')

        '''Concatenate every 10 events into 1 chunk. 1st chunk performs sendMessage to telegram, subsequent chunk edits the message'''
        current_text_chunk = []
        accumulated_text = []
        text_counter = 0
        message_id = None

        for event in stream_response:
            if 'contentBlockDelta' in event:
                text = event['contentBlockDelta']['delta']['text']
                current_text_chunk.append(text)
                text_counter += 1

                if text_counter % 20 == 0:
                    concatenated_text = ''.join(current_text_chunk)
                    accumulated_text.append(concatenated_text)
                    full_text = ''.join(accumulated_text)
                    print(full_text)

                    if message_id is None:
                        response = telegram_action(BOT_TOKEN, 'sendMessage', {'chat_id': chat_id, 'text': full_text, 'parse_mode': 'HTML'})
                        message_id = response['result']['message_id']
                    else:
                        telegram_action(BOT_TOKEN, 'editMessageText', {'chat_id': chat_id, 'message_id': message_id, 'text': full_text, 'parse_mode': 'HTML'})
                    
                    current_text_chunk = []
        
        # Concatenate remainder events and send or edit message to Telegram
        if current_text_chunk:
            final_chunk = ''.join(current_text_chunk)
            accumulated_text.append(final_chunk)
            full_text = ''.join(accumulated_text)
            print(full_text)

            if message_id is None:
                response = telegram_action(BOT_TOKEN, 'sendMessage', {'chat_id': chat_id, 'text': full_text, 'parse_mode': 'HTML'})
                message_id = response['result']['message_id']
            else:
                telegram_action(BOT_TOKEN, 'editMessageText', {'chat_id': chat_id, 'message_id': message_id, 'text': full_text, 'parse_mode': 'HTML'})

        message_history.append(
            {
                "role": "assistant", 
                "content": [{
                    "text":full_text
                    }
                ]
            }
        )

        # Saves the message history to S3
        try:
            bucket.put_object(Key=f"{chat_id}-history.json", Body=json.dumps(message_history))
        except:
            logger.info("Unable to save message history")
            logger.info(f"Message Hisotry: {message_history}")
    except:
        logger.info("Unable to send message to Bedrock")
        logger.info(f"Message: {message}")
        # log the error message
        logger.info(f"Error: {response}")
        telegram_action(BOT_TOKEN, 'sendMessage', {'chat_id': chat_id, 'text': "Sorry, I'm unable to process this message at this time"})

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    


def message_prep(prompt: str):
    ''' Prepare Message for Bedrock '''

    message = {
        "role": "user",
        "content": [
            {"text": prompt}
        ]
    }

    return message


def telegram_action(BOT_TOKEN, method:str , payload: dict):
    ''' Send or Edit Message to Telegram '''

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    payload_bytes = urllib3.request.urlencode(payload).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = http.request('POST', url, headers=headers, body=payload_bytes)
    response_data = response.data.decode("utf-8")
    return json.loads(response_data)