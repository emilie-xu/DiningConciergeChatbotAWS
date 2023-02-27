import boto3
import json

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    
    msg_from_user = event['messages'][0]['unstructured']['text']
    
    print(f"Message from frontend: {msg_from_user}")
    
    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='***', 
            botAliasId='***',
            localeId='en_US',
            text=msg_from_user,
            sessionId='testuser'
            )
    
    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)
        
        resp = {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Headers" : "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "text": msg_from_lex[0]['content']
                }
            },
            ]
        }
        
        return resp
