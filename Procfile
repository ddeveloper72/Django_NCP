web: gunicorn eu_ncp_server.wsgi --log-file -
release: python manage.py compile_scss && python manage.py collectstatic --noinput && python manage.py migrate --noinput
