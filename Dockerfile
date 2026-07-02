FROM mcr.microsoft.com/playwright/python:v1.61.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV HOST=0.0.0.0
ENV HEADLESS=true
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

COPY . .

RUN mkdir -p /data/whatsapp-session

EXPOSE 7860

CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
