FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BLOOM_DATA_DIR=/data
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY bloom_world ./bloom_world
RUN mkdir -p /data/packages && useradd --create-home --uid 10001 bloom && chown -R bloom:bloom /app /data
USER bloom
EXPOSE 8000
CMD ["sh", "-c", "uvicorn bloom_world.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
