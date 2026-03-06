@echo off
REM ------------------------------
REM Script para ejecutar manage_database_script.py en el contenedor webserver
REM ------------------------------

REM Entrar al contenedor webserver y ejecutar el script
docker exec -it webserver bash -c "cd /app/resources && python manage_database_script.py"
pause