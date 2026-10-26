#!/usr/bin/env bash
# Render build step: install, collect static files, migrate, seed the shared foods.
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cd mysite
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_foods            # idempotent: never overwrites existing foods

# Optional demo account (demo / DemoPass123!) with 3 weeks of data: set SEED_DEMO=true.
if [ "$SEED_DEMO" = "true" ]; then
  python manage.py seed_demo           # no-op if the demo user already exists
fi
