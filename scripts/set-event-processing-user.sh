#!/bin/bash

# Namespace
NAMESPACE="ibm-event-automation"

# Paths to JSON files
USER_FILE="components/instances/ibm-event-processing/ep-user.json"
ROLE_FILE="components/instances/ibm-event-processing/ep-user-role-mapping.json"

# Check if user file exists
if [ ! -f "$USER_FILE" ]; then
  echo "Error: File not found: $USER_FILE"
  exit 1
fi

# Check if role file exists
if [ ! -f "$ROLE_FILE" ]; then
  echo "Error: File not found: $ROLE_FILE"
  exit 1
fi

# Extract username and password using jq
USERNAME=$(jq -r '.users[0].username' "$USER_FILE")
PASSWORD=$(jq -r '.users[0].password' "$USER_FILE")

# Base64 encode depending on OS (for user file)
if base64 --help 2>&1 | grep -q "\-w"; then
  USER_B64=$(base64 -w 0 "$USER_FILE")
  ROLE_B64=$(base64 -w 0 "$ROLE_FILE")
else
  USER_B64=$(base64 < "$USER_FILE" | tr -d '\n')
  ROLE_B64=$(base64 < "$ROLE_FILE" | tr -d '\n')
fi

# Patch first secret: user credentials
oc patch secret eventprocessing-instance-ibm-ep-user-credentials \
  --type='json' \
  -p="[{\"op\":\"replace\",\"path\":\"/data/user-credentials.json\",\"value\":\"$USER_B64\"}]" \
  -n "$NAMESPACE"

# Patch second secret: user roles
oc patch secret eventprocessing-instance-ibm-ep-user-roles \
  --type='json' \
  -p="[{\"op\":\"replace\",\"path\":\"/data/user-mapping.json\",\"value\":\"$ROLE_B64\"}]" \
  -n "$NAMESPACE"

echo "-----------------------------------"
echo "✅ Secrets successfully updated!"
echo "Event Processing user credentials:"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "-----------------------------------"
