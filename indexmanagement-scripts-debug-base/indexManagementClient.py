
#!/bin/python

import os, sys
import json
import logging as log
from elasticsearch import Elasticsearch
from ssl import create_default_context

log.basicConfig(
  filename='/tmp/imdebug.log',
  format='%(asctime)s: [%(funcName)s] %(message)s',
  level=log.DEBUG
)

def getEsClient():
  log.debug("FUNC_INIT: {}".format(locals()))
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
  log.debug("FUNC_INIT: {}".format(locals()))
  try:
    es_client = getEsClient()
    ret = json.dumps(es_client.indices.get_alias(name=alias))
    log.debug("RETURN: {}".format(ret))
    return ret
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    return ""

def getIndicesAgeForAlias(alias):
  log.debug("FUNC_INIT: {}".format(locals()))
  try:
    es_client = getEsClient()
    ret = json.dumps(es_client.indices.get_settings(index=alias, name="index.creation_date"))
    log.debug("RETURN: {}".format(ret))
    return ret
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    return ""

def deleteIndices(index):
  log.debug("FUNC_INIT: {}".format(locals()))
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.delete(index=index)
    log.debug("RETURNING TRUE: response={}".format(response))
    return True
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False

def removeAsWriteIndexForAlias(index, alias):
  log.debug("FUNC_INIT: {}".format(locals()))
  es_client = getEsClient()
  response = es_client.indices.update_aliases({
    "actions": [
        {"add":{"index": f"{index}", "alias": f"{alias}", "is_write_index": False}}
    ]
  })
  log.debug("response={}".format(response))
  log.debug("RETURN: {}".format(response['acknowledged']))
  return response['acknowledged']

def catWriteAliases(policy):
  log.debug("FUNC_INIT: {}".format(locals()))
  try:
    es_client = getEsClient()
    alias_name = f"{policy}*-write"
    response = es_client.cat.aliases(name=alias_name, h="alias")
    log.debug("response={}".format(response))
    response_list = list(response.split("\n"))
    log.debug("response_list={}".format(response_list))
    ret = " ".join(sorted(set(response_list)))
    log.debug("RETURN: {}".format(ret))
    return ret
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    return ""

def rolloverForPolicy(alias, decoded):
  log.debug("FUNC_INIT: {}".format(locals()))
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.rollover(alias=alias, body=decoded)
    log.debug("response={}".format(response))
    sys.stdout = open('/tmp/response.txt', 'w')
    print(json.dumps(response))
    sys.stdout = original_stdout
    log.debug("RETURNING TRUE")
    return True
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    return False

def checkIndexExists(index):
  log.debug("FUNC_INIT: {}".format(locals()))
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    ret = es_client.indices.exists(index=index)
    log.debug("RETURN: {}".format(ret))
    return ret
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False

def updateWriteIndex(currentIndex, nextIndex, alias):
  log.debug("FUNC_INIT: {}".format(locals()))
  original_stdout = sys.stdout
  try:
    es_client = getEsClient()
    response = es_client.indices.update_aliases({
      "actions": [
          {"add":{"index": f"{currentIndex}", "alias": f"{alias}", "is_write_index": False}},
          {"add":{"index": f"{nextIndex}", "alias": f"{alias}", "is_write_index": True}}
      ]
    })
    log.debug("response={}".format(response))
    log.debug("RETURN: {}".format(response['acknowledged']))
    return response['acknowledged']
  except Exception as e:
    log.debug("EXCEPTION: {}".format(e))
    sys.stdout = open('/tmp/response.txt', 'w')
    print(e)
    sys.stdout = original_stdout
    return False
