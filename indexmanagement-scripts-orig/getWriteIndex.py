
#!/bin/python

import json,sys

try:
  alias = sys.argv[1]
  output = sys.argv[2]
except IndexError:
  raise SystemExit(f"Usage: {sys.argv[0]} <write_alias> <json_response>")

try:
  response = json.loads(output)
except ValueError:
  raise SystemExit(f"Invalid JSON: {output}")

lastIndex = len(response) - 1

if 'error' in response[lastIndex]:
  print(f"Error while attemping to determine the active write alias: {response[lastIndex]}")
  sys.exit(1)

data = response[lastIndex]

try:
  writeIndex = [index for index in data if data[index]['aliases'][alias].get('is_write_index')]
  if len(writeIndex) > 0:
    writeIndex.sort(reverse=True)
    print(" ".join(writeIndex))
except:
  e = sys.exc_info()[0]
  raise SystemExit(f"Error trying to determine the 'write' index from {data}: {e}")
