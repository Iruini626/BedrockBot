import boto3
import os
import json
from typing import List

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ["BUCKET_NAME"])

def get_config(chat_id):
    '''Gets config and model from s3 by chat_id'''

    try:
        config = bucket.Object(f"{chat_id}-config.json").get()['Body'].read().decode('utf-8')
        config = json.loads(config)
        model = bucket.Object(f"{chat_id}-model.json").get()['Body'].read().decode('utf-8')
        model = json.loads(model)
    except:
        config = {"temperature":float(0.9), "maxTokens":2048, "topP":float(0.9)}
        model = {"modelId":"anthropic.claude-3-sonnet-20240229-v1:0"}
        bucket.put_object(Key=f"{chat_id}-config.json", Body=json.dumps(config))
        bucket.put_object(Key=f"{chat_id}-model.json", Body=json.dumps(model))

    print(f"Config: {config}")
    print(f"Model: {model}")
    return config, model