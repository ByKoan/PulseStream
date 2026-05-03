docker compose down -v
docker compose build --no-cache
docker compose --profile tests up --build tests
pause