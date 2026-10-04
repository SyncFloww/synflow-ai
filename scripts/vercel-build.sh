#!/bin/sh
set -eu
# Dependencies are installed by the Django framework's install step.
# Preview builds must never migrate a shared production database.
if [ "${VERCEL_ENV:-}" = "production" ]; then
  if [ -z "${DATABASE_URL:-}" ]; then
    echo 'Set DATABASE_URL to the existing Neon database before building production.' >&2
    exit 1
  fi
  python manage.py migrate --noinput
fi
