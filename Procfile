web: python manage.py migrate && gunicorn trimrrsite.wsgi --log-file -
worker: celery -A trimrrsite worker --loglevel=info
