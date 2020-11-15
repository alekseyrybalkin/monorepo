#!/bin/bash

set -e
sudo true
set +e

git add .
git commit -m 'python-addons updates'

if ! ping -c 1 ${CLOUD_DOMAIN} >/dev/null 2>&1; then
    echo "No ping to ${CLOUD_DOMAIN}, skipping git push."
else
    git push
fi

srcfetcher python-addons
sudo packmgr u python-addons
