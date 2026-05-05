docker compose down -v
docker compose build --no-cache
docker compose --profile tests up
pause