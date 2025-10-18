FROM python:3.11-slim

WORKDIR /app/backend
COPY backend/ .

RUN pip install --upgrade pip
RUN pip install fastapi uvicorn ollama

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
