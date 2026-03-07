@echo off
docker exec -it webserver bash -c "cd /app/resources && python manage_database_script.py"
pause