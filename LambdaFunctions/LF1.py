import json
import boto3
import datetime
import time
import dateutil.parser
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
  
    intent = event['sessionState']['intent']['name']

    if intent == 'GreetingIntent':
        return greetingResponse(event)
    elif intent == 'ThankYouIntent':
        return thanksResponse(event)
    elif intent == 'DiningSuggestionsIntent':
        return diningRecsResponse(event)
    elif intent == 'FallbackIntent':
        return fallbackResponse(event)
        
    raise Exception("Intent " + intent + " is not supported")
        
        
def greetingResponse(event):
    message = "Hello there! How can I help you?"
    return makeResponse(event, message)
    
    
def thanksResponse(event):
    message = "Of course! Always happy to help"
    return makeResponse(event, message)
    
    
def fallbackResponse(event):
    message = "Oops! I don't understand. Please try again"
    return makeResponse(event, message)
    
    
def diningRecsResponse(event):
    slots = event['sessionState']['intent']['slots']
    invoc_source = event['invocationSource']
    
    location = slots['location']
    cuisine = slots['cuisine']
    num_people = slots['num_people']
    dining_date = slots['dining_date']
    dining_time = slots['dining_time']
    phone_number = slots['phone_number']
    
    logger.debug(json.dumps(slots))
    
    if invoc_source == 'DialogCodeHook':

        validation = validate_dining_responses(cuisine, num_people, dining_date, dining_time)

        if not validation['isValid']:
            #logger.debug(json.dumps(slots))
            slots[validation['violatedSlot']] = None
            #logger.debug(json.dumps(slots))

            recall_slot = elicit_slot(event['sessionState']['sessionAttributes'], 
                                event['sessionState']['intent']['name'], 
                                slots, 
                                validation['violatedSlot'], 
                                validation['message']['content'])
            
            logger.debug(json.dumps(slots))
            return recall_slot

        return delegate(event, slots)
        
    # SQS queue
    push_user_info(slots)
    
    return close(event, event['sessionState']['sessionAttributes'])
                  
                  
def validate_dining_responses(cuisine, num_people, dining_date, dining_time):

    if cuisine is not None:
        possible_cuisines = ['japanese', 'mexican', 'italian', 'chinese', 'indian', 'thai', 'mediterranean']
        if cuisine['value']['originalValue'].lower() not in possible_cuisines:
            return make_validation_result(False, 'cuisine', 'Cuisine not recognized. Please try another')
            
    if num_people is not None:
        if int(num_people['value']['originalValue']) <= 0 or int(num_people['value']['originalValue']) > 20:
            return make_validation_result(False, 'num_people', 'Sorry, the maximum number of people is 20. Please try again')
            
    if dining_date is not None:
        if datetime.datetime.strptime(dining_date['value']['interpretedValue'], '%Y-%m-%d').date() < datetime.date.today():
            return make_validation_result(False, 'dining_date', 'You can only dine today or in the future. Please try again')
            
    if dining_time is not None:
        if datetime.datetime.strptime(dining_date['value']['interpretedValue'], '%Y-%m-%d').date() == datetime.date.today():
            if datetime.datetime.strptime(dining_time['value']['interpretedValue'], '%H:%M').time() <= datetime.datetime.now().time():
                return make_validation_result(False, 'dining_time', 'Please enter a valid time')
    
    return make_validation_result( True, None, None)
    
    
def make_validation_result(isValid, slot, message):
    if message is None:
        return {
            "isValid": isValid,
            "violatedSlot": slot
        }
        
    return {
        'isValid': isValid,
        'violatedSlot': slot,
        'message': {'contentType': 'PlainText', 'content': message}
    }
    
    
def elicit_slot(session_attr, intent_name, slots, slot_elicit, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_elicit,
            },
            'intent': {
                'name': intent_name,
                'slots': slots
            },
            'sessionAttributes': session_attr
        },
        'messages': [
        {
            'contentType': 'PlainText',
            'content': message
        }
        ]
    }
    

def delegate(event, slots):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Delegate'
            },
            "intent": {
                    "name": event['sessionState']['intent']['name'],
                    "state": "InProgress",
                    'slots': slots
                },
                "sessionAttributes": event['sessionState']['sessionAttributes']
        },
            "messages": []
    }
    

def push_user_info(slots):
    sqs = boto3.client('sqs')
                        
    Q1 = 'https://sqs.us-east-1.amazonaws.com/724955335464/Q1'

    user_info = {
        'location': {
            'DataType': 'String',
            'StringValue': slots["location"]['value']['interpretedValue']
        },
        'cuisine': {
            'DataType': 'String',
            'StringValue': slots["cuisine"]['value']['originalValue']
        },
        'num_people': {
            'DataType': 'String',
            'StringValue': slots["num_people"]['value']['originalValue']
        },
        'dining_date': {
            'DataType': 'String',
            'StringValue': slots["dining_date"]['value']['interpretedValue']
        },
        'dining_time': {
            'DataType': 'String',
            'StringValue': slots["dining_time"]['value']['interpretedValue']
        },
        'phone_number' : {
            'DataType': 'String',
            'StringValue': slots["phone_number"]['value']['interpretedValue']
        }
    }
    
    response = sqs.send_message(QueueUrl = Q1, MessageAttributes = user_info, MessageBody = json.dumps(user_info))


def makeResponse(event, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'state': 'Fulfilled'
            }
        },
        'messages': [
        {
            'contentType': 'PlainText',
            'content': message
        }
        ]
    }
    
    
def close(event, session_attr):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'state': 'Fulfilled'
            },
            'sessionAttributes': session_attr
        },
        'messages': [
        {
            'contentType': 'PlainText',
            'content': "You’re all set. Expect my suggestions shortly! Have a good day"
        }
        ]
    }
