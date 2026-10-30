#!/usr/bin/env bash
# Starts DefectDojo locally using the official project. Requires Docker with Compose and git.
set -euo pipefail
[ -d django-DefectDojo ] || git clone --depth 1 https://github.com/DefectDojo/django-DefectDojo.git
cd django-DefectDojo
./dc-build.sh && ./dc-up.sh postgres-redis
echo "Waiting for startup, then fetch the admin password with:"
echo "  docker compose logs initializer | grep 'Admin password'"
echo "UI: http://localhost:8080  (API token under your profile)"
