# 🤖 AI Техподдержка Росатом

<div align="center">

🚀 **Автоматическая система техподдержки на базе AI-агентов**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-yellow?logo=python)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-phi3:mini-purple)](https://ollama.ai/)

</div>

## 📋 Требования к системе

- **Docker Desktop**: [Скачать с официального сайта](https://www.docker.com/products/docker-desktop/)
- **Оперативная память**: минимум 4 GB
- **Свободное место на диске**: 5 GB

## 🚀 Инструкция по запуску

### Шаг 1: Установите Docker Desktop

1. Перейдите на [официальный сайт Docker](https://www.docker.com/products/docker-desktop/)
2. Скачайте версию для вашей операционной системы
3. Установите Docker Desktop, следуя инструкциям установщика
4. Запустите Docker Desktop и дождитесь полной загрузки

### Шаг 2: Скачайте проект

**Вариант A - Через Git (рекомендуется):**
```bash
git clone https://github.com/sxaryu/ai_rosatom_helper
cd ai_rosatom_helper
```

### Шаг 3: Запустите проект 
Откройте терминал/командную строку в папке проекта и выполните:
```
docker-compose up --build
```

### Шаг 4: Дождитесь загрузки
Первый запуск займет 5-10 минут. Система автоматически:

📦 Соберет все необходимые контейнеры

🧠 Скачает AI модель phi3:mini (2.2 GB)

🔧 Настроит бэкенд на Python 3.11

🌐 Запустит веб-сервер

#### Готовность системы определяется по логам:

backend_1  | INFO:     Application startup complete.
backend_1  | INFO:     Uvicorn running on http://0.0.0.0:8000\

### Шаг 5: Откройте веб-интерфейс
После успешного запуска откройте ваш браузер и перейдите по адресу:
[http://localhost ](http://localhost)    