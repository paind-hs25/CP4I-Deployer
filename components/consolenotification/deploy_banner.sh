#!/usr/bin/env bash
set -euo pipefail

# === Configuration ===
NAMESPACE="integration"
ROUTE_NAME="integration-quickstart-pn"

# === Reading Host from Route ===
echo "🔍 Reading Route $ROUTE_NAME in Namespace $NAMESPACE..."
HOST=$(oc -n "$NAMESPACE" get route "$ROUTE_NAME" -o jsonpath='{.spec.host}')

if [ -z "$HOST" ]; then
  echo "❌ Could not find route host!"
  exit 1
fi
echo "✅ Found host: $HOST"

# === Kustomize Build + replace Host + Apply ===
echo "🚀 Deploying ConsoleNotification..."
kustomize build . | sed "s|\$(PLATFORM_UI_HOST)|$HOST|g" | oc apply -f -

echo "🎉 Banner with link https://$HOST deployed!"
