import boto3
import logging
import json
import typing

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a boto3 client for Amazon Bedrock
bedrock = boto3.client('bedrock-runtime')

# Main Logic
def lambda_handler(event, context):
    '''Sends the message to bedrock model'''

    # Converse with Bedrock
    response = bedrock.converse_stream(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[
            {
                "role": "user",
                "content": [
                    {"text":"create a story in 200 words"}
                ]
            }
        ]
    )

    logger.info(response)
    stream = response.get('stream')
    logger.info(stream)
    
    response_stream = []
    current_chunck = []

    # Parse the response
    for event in stream:
        logger.info(event)
        logger.info(type(event))
        if 'contentBlockDelta' in event:
            text = event['contentBlockDelta']['delta']['text']
            current_chunck.append(text)

            if len(current_chunck) == 20:
                concatenated_text = ''.join(current_chunck)
                response_stream.append(concatenated_text)
                current_chunck = []

    if current_chunck:
        concatenated_text = ''.join(current_chunck)
        response_stream.append(concatenated_text)

    return response_stream