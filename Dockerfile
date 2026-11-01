FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCUMIND_DB=/data/documind.db

WORKDIR /app

# 先只拷贝依赖描述文件，这样改代码不会让依赖层缓存失效，构建更快
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
