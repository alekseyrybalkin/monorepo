#!/bin/bash

set -e
sudo true
set +e

git add .
git commit -m 'monorepo updates'

if ! ping -c 1 ${CLOUD_DOMAIN} >/dev/null 2>&1; then
    echo "No ping to ${CLOUD_DOMAIN}, skipping git push."
else
    git push
fi

srcfetcher monorepo
sudo packmgr u monorepo
