FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY bot/requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]
