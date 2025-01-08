import boto3
import logging
import urllib3
import json
import asyncio

BOT_TOKEN: str = "8073759396:AAFZQOzXGsyc6VZ90ZKUp5gzohj8TYqG0MU"
CHAT_ID: int = 46307554

http = urllib3.PoolManager()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client('bedrock-runtime')

def telegram_action(BOT_TOKEN, method:str , payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    payload_bytes = urllib3.request.urlencode(payload).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = http.request('POST', url, headers=headers, body=payload_bytes)
    response_data = response.data.decode("utf-8")
    return json.loads(response_data)

def lambda_handler(event, context):
    event_body = json.loads(event['body'])
    print(event_body)

    user_prompt = event_body['message']['text']
    print(user_prompt)

    response = bedrock.converse_stream(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=[
            {
                "role": "user",
                "content": [
                    {"text":user_prompt}
                ]
            }
        ]
    )

    stream_response = response.get('stream')
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
                    response = telegram_action(BOT_TOKEN, 'sendMessage', {'chat_id': CHAT_ID, 'text': full_text})
                    message_id = response['result']['message_id']
                else:
                    telegram_action(BOT_TOKEN, 'editMessageText', {'chat_id': CHAT_ID, 'message_id': message_id, 'text': full_text})
                
                current_text_chunk = []
    
    if current_text_chunk:
        final_chunk = ''.join(current_text_chunk)
        accumulated_text.append(final_chunk)
        full_text = ''.join(accumulated_text)
        print(full_text)

        if message_id is None:
            response = telegram_action(BOT_TOKEN, 'sendMessage', {'chat_id': CHAT_ID, 'text': full_text})
            message_id = response['result']['message_id']
        else:
            telegram_action(BOT_TOKEN, 'editMessageText', {'chat_id': CHAT_ID, 'message_id': message_id, 'text': full_text})

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

