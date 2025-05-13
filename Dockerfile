FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080  # ← Добавляем фиктивный порт, чтобы Timeweb не ругался

CMD ["python", "bot.py"]
