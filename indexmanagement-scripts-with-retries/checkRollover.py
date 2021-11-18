
#!/bin/python

import json,sys

try:
  fileToRead = sys.argv[1]
  currentIndex = sys.argv[2]
except IndexError:
  raise SystemExit(f"Usage: {sys.argv[0]} <file_to_read> <current_index>")

try:
  with open(fileToRead) as f:
    data = json.load(f)
except ValueError:
  raise SystemExit(f"Invalid JSON: {f}")

try:
  if not data['acknowledged']:
    if not data['rolled_over']:
      for condition in data['conditions']:
        if data['conditions'][condition]:
          print(f"Index was not rolled over despite meeting conditions to do so: {data['conditions']}")
          sys.exit(1)

      print(data['old_index'])
      sys.exit(0)

  if data['old_index'] != currentIndex:
    print(f"old index {data['old_index']} does not match expected index {currentIndex}")
    sys.exit(1)

  print(data['new_index'])
except KeyError as e:
  raise SystemExit(f"Unable to check rollover for {data}: missing key {e}")
