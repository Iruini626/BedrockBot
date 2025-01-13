import boto3
import json
import os
import urllib3
import getConfig

http = urllib3.PoolManager()

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ["BUCKET_NAME"])

model_selection = ["/claude","/nova","/llama"]
model_map = {
    "/claude": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "/nova": "amazon.nova-pro-v1:0",
    "/llama": "us.meta.llama3-3-70b-instruct-v1:0"
}
config_choices = ["/temperature","/maxtokens","/topp","/reset","/newchat"]

def send_telegram(config, chat_id):
    url = f"https://api.telegram.org/bot{os.environ["BOT_TOKEN"]}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"Config Updated\n{json.dumps(config, indent=2)}"
    }
    payload_bytes = urllib3.request.urlencode(payload).encode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    http.request('POST', url, headers=headers, body=payload_bytes)

    
def lambda_handler(event, context):
    """ Write input config to s3 based on chat id"""

    chat_id = event['detail']['message']['chat']['id']
    command = event['detail']['message']['text']

    full_config = getConfig.get_config(chat_id)
    print(full_config)
    config = full_config[0]

    if command in model_selection:
        bucket.put_object(Key=f"{chat_id}-model.json", Body=json.dumps({"modelId":model_map[command]}))
        send_telegram({"modelId":model_map[command]}, chat_id)

    if any(command.startswith(choice) for choice in config_choices):
        # Update config based on command
        parts = command.split()
        command_type = parts[0]

        if command_type == "/temperature":
            config["temperature"] = float(parts[1])
        elif command_type == "/maxtokens":
            config["maxTokens"] = int(parts[1])
        elif command_type == "/topp":
            config["topP"] = float(parts[1])
        elif command_type == "/reset":
            config = {"temperature":float(0.9), "maxTokens":2048, "topP":float(0.9)}
        elif command_type == "/newchat":
            bucket.put_object(Key=f"{chat_id}-history.json", Body=json.dumps([]))
            send_telegram("Message History Cleared", chat_id)

        # Save updated config to S3
        bucket.put_object(Key=f"{chat_id}-config.json", Body=json.dumps(config))
        send_telegram(config, chat_id)
        