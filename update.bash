#!/bin/bash

sudo true

git add .
git commit -m 'python-addons updates'

if ! ping -c 1 ${HEAVEN_DOMAIN} >/dev/null 2>&1; then
    echo "No ping to ${HEAVEN_DOMAIN}, skipping git push."
else
    git push
fi

ji pull python-addons
sudo ji u python-addons
