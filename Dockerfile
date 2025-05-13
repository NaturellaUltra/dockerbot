FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV BOT_TOKEN="dummy"
CMD ["python", "bot.py"]
