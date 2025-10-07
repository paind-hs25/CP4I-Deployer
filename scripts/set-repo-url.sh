#!/bin/bash
set -e

# Check if the environment variable is set
if [ -z "$REPO_URL" ]; then
  echo "❌ Error: Please set the REPO_URL variable first, e.g.:"
  echo "   export REPO_URL='https://github.com/youruser/yourrepo.git'"
  exit 1
fi

echo "🔄 Setting all repoURLs to: $REPO_URL"

# Find all YAML files under the argocd directory and update them
find argocd -type f \( -name "*.yaml" -o -name "*.yml" \) | while read -r file; do
    sed -i.bak -E "s|repoURL:.*|repoURL: '${REPO_URL}'|" "$file" && rm "$file.bak"
    echo "✅ Updated $file"
done

echo "🎉 All repoURLs were successfully set."
