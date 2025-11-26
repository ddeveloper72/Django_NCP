web: gunicorn eu_ncp_server.wsgi --log-file -
release: rm -rf staticfiles staticfiles.json && python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput
