#!/usr/bin/env bash

set -e

envsubst < .gitlab/proxy.env > tmp_proxy.env && mv tmp_proxy.env .gitlab/proxy.env
export $(cat .gitlab/proxy.env | xargs)

mkdir -p static/ /app/log

# load py file
echo $PY_HEX | xxd -r -p > /app/cohort_back/conf_cohort_job_api.py

# restart nginx
service nginx restart

# Install the settings
python manage.py migrate

celery worker -B -A cohort_back --loglevel=info >> /app/log/celery.log 2>&1 &
sleep 10
python manage.py runserver 49026 >> /app/log/django.log 2>&1 &

tail -f /app/log/django.log
