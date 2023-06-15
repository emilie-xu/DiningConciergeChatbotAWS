# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 14:58:16 2023

@author: emili
"""

import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import requests
from decimal import Decimal
from time import sleep
import datetime
import collections
from urllib.parse import quote


# try:
#     # For Python 3.0 and later
#     #from urllib.error import HTTPError
    
#     #from urllib.parse import urlencode
# except ImportError:
#     # Fall back to Python 2's urllib2 and urllib
#     #from urllib2 import HTTPError
#     from urllib import quote
#     #from urllib import urlencode


def create_table():
    dynamodb = boto3.resource("dynamodb", region_name=region, aws_access_key_id = access_key, aws_secret_access_key = secret_key)
    params = {
        'TableName': 'yelp-restaurants',
        'KeySchema': [
            {'AttributeName': 'business_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'business_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        'ProvisionedThroughput': {
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    }
    dynamodb.create_table(**params)
    
create_table()


API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'


#Code from stackoverflow
def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    response = requests.request('GET', url, headers=headers, params=url_params)

    return response


def flatten(d, parent_key='', sep='_'):
    items = []
    for key, val in d.items():
        new_key = key
        if isinstance(val, collections.MutableMapping):
            items.extend(flatten(val, new_key, sep=sep).items())
        else:
            items.append((new_key, val))
    return dict(items)


dynamodb = boto3.resource('dynamodb', region_name=region, aws_access_key_id=access_key,  aws_secret_access_key = secret_key)
table = dynamodb.Table('yelp-restaurants')

#(Requirements: Business ID, Name, Address, Coordinates, Number of Reviews, Rating, Zip Code)
client = boto3.client('dynamodb', region_name=region, aws_access_key_id=access_key,  aws_secret_access_key = secret_key)
list_float=['rating', 'latitude', 'longitude', 'distance']

def convert_floats(item,list_float=list_float):
    for var in item:
        if var in list_float:
            item[var]=Decimal(str(item[var]))
    return item

# Creating the final list of dictionaries for the DynamoDB
cols = ['name', 'latitude', 'longitude', 'review_count', 'rating', 'zip_code']
final_list = []
cuisines = ['chinese', 'mexican', 'italian', 'indian', 'mediterranean', 'thai', 'japanese']
for s in cuisines:
  # add a pause
  sleep(0.5)
  for o in range(0, 1000, 50): #1000
    url_params = {
      'term': 'restaurants',
      'location': 'New York City',
      'offset': o,
      'categories': s,
      'limit': 50
    }
    print("cuisine:", s, "; offset:", o)
    response = request(API_HOST, SEARCH_PATH, API_KEY, url_params=url_params).json().get("businesses")
    #print(response)
    sleep(0.5)
    if(response==None):
        print("failed")
        continue
    for x in response:
      data = flatten(x)
      data = convert_floats(data)
      
      data2 = { your_key: data[str(your_key)] for your_key in cols }
      data2["business_id"] = data["id"]
      data2["cuisine"] = s
      data2["timestamp"] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S") + "}"
      data2["address"] = data["address1"]
      final_list.append(data2)


# Inserting the final dictionaries into the DynamoDB table
i = 0
table = dynamodb.Table('yelp-restaurants')
for entry in final_list:
    response = table.put_item(Item = entry)
    if ("UnprocessedItems" in response):
        print(response["UnprocessedItems"])
        break
    i+=1  
print('%i items inserted' %i)





# Creating OpenSearch client --copied from aws documentation
host = 'search-restaurantdomain-uuzfi2vpxvqmb4ex7jod2jo6dm.us-east-1.es.amazonaws.com'
service = "es"

from requests_aws4auth import AWS4Auth
awsauth = AWS4Auth(access_key, secret_key, region, service)#, session_token=credentials.token)

client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)


# Forming the elaticsearch dictionary to upload to our Domain
opensearch_list = []
for entry in final_list:
    name = entry.get("name")
    cuisine = entry.get("cuisine")
    #print(cuisine)
    business_id = entry.get("business_id")
    opensearch_dict = {"business_id":business_id, "cuisine": cuisine}
    opensearch_list.append(opensearch_dict)
    
action={
    "index": {
        "_index": 'restaurants'
    }
}

def payload_constructor(data,action):
    # "All my own work"

    action_string = json.dumps(action) + "\n"

    payload_string=""

    for datum in data:
        payload_string += action_string
        this_line = json.dumps(datum) + "\n"
        payload_string += this_line
    return payload_string

actions_body = payload_constructor(opensearch_list,action)

file = open("data.json", "w")
file.write(str(actions_body))
file.close()

#response=client.bulk(body=actions_body,index='restaurants')



#bulked = client.bulk(actions)

"""



# auth = AWSV4SignerAuth((access_key, secret_key, None), region, session_token = None)
# index_name = 'restaurants'


# client = OpenSearch(
#     hosts = [{'host': host, 'port': 443}],
#     http_auth = auth,
#     use_ssl = True,
#     verify_certs = True,
#     connection_class = RequestsHttpConnection
# )

# Creating index for bulk json data


my_index = 'restaurants'

try:
    response = client.indices.create(my_index)
    print('\nCreating index:')
    print(response)
except Exception as e:
    # If, for example, my_index already exists, do not much!
    print(e)
"""




"""


c = 'chinese'
query = {
  'match': {"cuisine": c}
}

response = client.search(
    body = query,
    index = index_name
)

print('\nSearch results:')
print(response)




# Inserting into ElasticSearch DB
# Using Royston Credentials as he is the Master User
access_key = "************************"
secret_key = "*************************************"

host = "search-test-es-55h2alnoth4r7l4hkldymkn7m4.us-west-2.es.amazonaws.com"
region = 'us-west-2'
service = "es"
#credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(access_key, secret_key, region, service)

es = Elasticsearch(hosts = [{'host': host, 'port': 443}],
                   http_auth = awsauth, use_ssl = True,
                   verify_certs = True, connection_class = RequestsHttpConnection
                   )

for restaurant in es_list:
  response = es.index(index = "restaurants", body = restaurant)

# ElasticSearch Index populated.
# Now Querying the index for restaurant ID.

import random

res = es.search(index="restaurants", body={"query": {"match": {"cuisine": "american"}}})
candidates = []
for entry in res['hits']['hits']:
  candidates.append(entry["_source"])

ids = []
for i in candidates:
  ids.append(i.get("id"))

restaurant_suggestion = random.choice(ids)
"""
