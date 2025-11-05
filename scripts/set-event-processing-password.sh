#!/bin/bash

# Path to JSON file
FILE="components/instances/ibm-event-processing/ep-user.json"

# Check if file exists
if [ ! -f "$FILE" ]; then
  echo "Error: File not found: $FILE"
  exit 1
fi

# Extract username and password using jq
USERNAME=$(jq -r '.users[0].username' "$FILE")
PASSWORD=$(jq -r '.users[0].password' "$FILE")

# Base64 encode depending on OS
if base64 --help 2>&1 | grep -q "\-w"; then
  # Linux
  B64=$(base64 -w 0 "$FILE")
else
  # macOS (no -w option)
  B64=$(base64 < "$FILE" | tr -d '\n')
fi

# Patch the secret
oc patch secret eventprocessing-instance-ibm-ep-user-credentials \
  --type='json' \
  -p="[{\"op\":\"replace\",\"path\":\"/data/user-credentials.json\",\"value\":\"$B64\"}]" \
  -n ibm-event-automation

echo "-----------------------------------"
echo "✅ Secret successfully updated!"
echo "The credentials for your Event Processing instance are:"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "-----------------------------------"