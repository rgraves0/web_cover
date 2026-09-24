FROM python:3.11-slim

WORKDIR /app

# Font နှင့် image processing အတွက် လိုအပ်သော package များ
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
