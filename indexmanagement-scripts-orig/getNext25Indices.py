
#!/bin/python

from __future__ import print_function
import json,sys

try:
  minAgeFromEpoc = sys.argv[1]
  writeIndex = sys.argv[2]
  output = sys.argv[3]
except IndexError:
  raise SystemExit(f"Usage: {sys.argv[0]} <minAgeFromEpoc> <writeIndex> <json_response>")

try:
  response = json.loads(output)
except ValueError:
  raise SystemExit(f"Invalid JSON: {output}")

lastIndex = len(response) - 1

if 'error' in response[lastIndex]:
  print(f"Error while attemping to determine index creation dates: {response[lastIndex]}")
  sys.exit(1)

r = response[lastIndex]

indices = []
for index in r:
  try:
    if 'settings' in r[index]:
      settings = r[index]['settings']
      if 'index' in settings:
        meta = settings['index']
        if 'creation_date' in meta:
          creation_date = meta['creation_date']
          if int(creation_date) < int(minAgeFromEpoc):
            indices.append(index)
        else:
          sys.stderr.write("'creation_date' missing from index settings: %r" % (meta))
      else:
        sys.stderr.write("'index' missing from setting: %r" % (settings))
    else:
      sys.stderr.write("'settings' missing for %r" % (index))
  except:
    e = sys.exc_info()[0]
    sys.stderr.write("Error trying to evaluate index from '%r': %r" % (r,e))
if writeIndex in indices:
  indices.remove(writeIndex)
for i in range(0, len(indices), 25):
  print(','.join(indices[i:i+25]))
