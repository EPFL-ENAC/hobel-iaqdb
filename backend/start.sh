# Run migrations
# uvicorn reads FORWARDED_ALLOW_IPS (default 127.0.0.1): set it to the ingress
# addresses, never "*", which lets clients forge X-Forwarded-For
alembic upgrade head
uvicorn --host=0.0.0.0 --timeout-keep-alive=0 api.main:app --reload
