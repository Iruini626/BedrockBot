

import boto3
import urllib3
import json
import logging
import typing

# HTTP Manager
http = urllib3.PoolManager()

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event,context):
    logger.info(event)
    print(event)
    # Extract text from events in one line
    texts = [item['contentBlockDelta']['delta']['text'] 
            for item in event 
            if 'contentBlockDelta' in item]
    print(texts)
    
    # If less than 20 items, return single joined string
    if len(texts) < 20:
        print(''.join(texts))
        return ''.join(texts)
    
    # Otherwise, return chunks of 20 items
    print([''.join(texts[i:i+20]) 
            for i in range(0, len(texts), 20)])
    return [''.join(texts[i:i+20]) 
            for i in range(0, len(texts), 20)]


