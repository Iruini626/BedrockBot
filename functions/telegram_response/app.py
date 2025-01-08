import urllib3
import json

# Http
http = urllib3.PoolManager()

def send_telegram(message:str, chat_id: int):
    url = f"https://api.telegram.org/bot8073759396:AAFZQOzXGsyc6VZ90ZKUp5gzohj8TYqG0MU/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }
    payload_bytes = urllib3.request.urlencode(payload).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = http.request('POST', url, headers=headers, body=payload_bytes)
    response_data = response.data.decode("utf-8")
    return json.loads(response_data)['result']['message_id']

def edit_telegram(message: str, chat_id: int, message_id: int):
    url = f"https://api.telegram.org/bot8073759396:AAFZQOzXGsyc6VZ90ZKUp5gzohj8TYqG0MU/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": message
    }
    payload_bytes = urllib3.request.urlencode(payload).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = http.request('POST', url, headers=headers, body=payload_bytes)
    response_data = response.data.decode("utf-8")
    return json.loads(response_data)['result']


def lambda_handler(event,context):
    messages = []
    for i, item in enumerate(event):
        if i == 0:
            message_id = send_telegram(item, 46307554)
            messages.append(item)
        else:
            messages.append(item)
            print(messages)
            full_message = ''.join(messages)
            result = edit_telegram(full_message, 46307554, message_id)
    