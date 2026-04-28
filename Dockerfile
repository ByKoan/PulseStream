FROM python:3.15-rc-alpine3.23

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY src/ .  

EXPOSE 8080 50000

CMD ["python", "main.py"]  