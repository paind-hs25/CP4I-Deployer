#!/bin/bash
set -e

# Check if environment variables are set
if [ -z "$BLOCK_STORAGE_CLASS" ]; then
  echo "❌ Error: Please set the BLOCK_STORAGE_CLASS variable first, e.g.:"
  echo "   export BLOCK_STORAGE_CLASS='<your-block-storage-class-name>'"
  exit 1
fi

if [ -z "$FILE_STORAGE_CLASS" ]; then
  echo "❌ Error: Please set the FILE_STORAGE_CLASS variable first, e.g.:"
  echo "   export FILE_STORAGE_CLASS='<your-file-storage-class-name>'"
  exit 1
fi

echo "🔄 Setting storageClasses: Block='$BLOCK_STORAGE_CLASS', File='$FILE_STORAGE_CLASS'"

# Find and update YAML files
find components/instances -type f \( -name "*.yaml" -o -name "*.yml" \) | while read -r file; do
  updated=0

  # #block replacements
  for key in storageClassName storageClass class defaultClass; do
    if grep -q "${key}:.*#block" "$file"; then
      sed -i.bak -E "s|^([[:space:]]*${key}:[[:space:]]*)[^[:space:]]+([[:space:]]*#block)|\1${BLOCK_STORAGE_CLASS}\2|" "$file"
      updated=1
    fi
  done

  # #file replacements
  for key in storageClassName storageClass class defaultClass; do
    if grep -q "${key}:.*#file" "$file"; then
      sed -i.bak -E "s|^([[:space:]]*${key}:[[:space:]]*)[^[:space:]]+([[:space:]]*#file)|\1${FILE_STORAGE_CLASS}\2|" "$file"
      updated=1
    fi
  done

  # Remove backup only if it exists
  [ -f "$file.bak" ] && rm "$file.bak"

  # Print only if updated
  [ $updated -eq 1 ] && echo "✅ Updated $file"
done

echo "🎉 All storageClasses were successfully updated based on #block/#file comments."
