web: gunicorn fuzhou_ev_charging.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
release: python manage.py migrate --noinput && python data/init_fuzhou_data.py && python knowledge_base/build_knowledge_base.py
