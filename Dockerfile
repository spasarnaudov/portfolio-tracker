FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV HOST=0.0.0.0
ENV PORT=5000

WORKDIR /app

COPY apps/flask/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --chdir apps/flask --bind 0.0.0.0:${PORT:-5000} --log-level ${LOG_LEVEL:-info} app:app"]
