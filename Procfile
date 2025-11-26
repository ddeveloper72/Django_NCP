web: gunicorn eu_ncp_server.wsgi --log-file -
release: rm -f staticfiles/staticfiles.json && python manage.py collectstatic --noinput --clear && python manage.py migrate --noinput
