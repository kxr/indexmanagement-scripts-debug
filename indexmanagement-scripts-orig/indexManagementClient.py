
#!/bin/python

import os, sys
import json
from elasticsearch import Elasticsearch
from ssl import create_default_context

def getEsClient():
  esService = os.environ['ES_SERVICE']
  connectTimeout = os.getenv('CONNECT_TIMEOUT', 30)

  tokenFile = open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r')
  bearer_token = tokenFile.read()

  context = create_default_context(cafile='/etc/indexmanagement/keys/admin-ca')
  es_client = Elasticsearch([esService],
    timeout=connectTimeout,
    max_retries=5,
    retry_on_timeout=True,
    headers={"authorization": f"Bearer {bearer_token}"},
    ssl_context=context)
  return es_client

def getAlias(alias):
  try:
    es_client = getEsClient()
    return json.dumps(es_client.indices.get_alias(name=alias))
  except:
    return ""

def getIndicesAgeForAlias(alias):
  try:
    es_client = getEsClient()
    return json.dumps(es_client.indices.get_settings(index=alias, name="index.creation_date"))
  except:
    return ""

def deleteIndices(index):
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.delete(index=index)
    return True
  except Exception as e:
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False

def removeAsWriteIndexForAlias(index, alias):
  es_client = getEsClient()
  response = es_client.indices.update_aliases({
    "actions": [
        {"add":{"index": f"{index}", "alias": f"{alias}", "is_write_index": False}}
    ]
  })
  return response['acknowledged']

def catWriteAliases(policy):
  try:
    es_client = getEsClient()
    alias_name = f"{policy}*-write"
    response = es_client.cat.aliases(name=alias_name, h="alias")
    response_list = list(response.split("\n"))
    return " ".join(sorted(set(response_list)))
  except:
    return ""

def rolloverForPolicy(alias, decoded):
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.rollover(alias=alias, body=decoded)
    sys.stdout = open('/tmp/response.txt', 'w')
    print(json.dumps(response))
    sys.stdout = original_stdout
    return True
  except:
    return False

def checkIndexExists(index):
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    return es_client.indices.exists(index=index)
  except Exception as e:
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False

def updateWriteIndex(currentIndex, nextIndex, alias):
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.update_aliases({
      "actions": [
          {"add":{"index": f"{currentIndex}", "alias": f"{alias}", "is_write_index": False}},
          {"add":{"index": f"{nextIndex}", "alias": f"{alias}", "is_write_index": True}}
      ]
    })
    return response['acknowledged']
  except Exception as e:
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False
