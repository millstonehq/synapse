#!/usr/bin/env bash
set -euo pipefail

VERSION=${1:?Usage: bump-version.sh <version>}

# Update all packages
for pkg in packages/schemas packages/cli packages/context-mcp packages/site; do
  jq --arg v "$VERSION" '.version = $v' "$pkg/package.json" > tmp.json && mv tmp.json "$pkg/package.json"
  echo "Updated $pkg to $VERSION"
done

# Update root
jq --arg v "$VERSION" '.version = $v' package.json > tmp.json && mv tmp.json package.json
echo "Updated root to $VERSION"

echo ""
echo "All packages updated to $VERSION"
echo "Next: git add -A && git commit -m 'chore: bump version to $VERSION' && git tag v$VERSION"
