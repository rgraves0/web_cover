FROM python:3.11-slim

WORKDIR /app

# မြန်မာ Unicode စာလုံးပေါင်း အထားအသိုမှန်ကန်စေရန် libraqm ကို သွင်းပေးခြင်း
RUN apt-get update && apt-get install -y --no-install-recommends \
    libraqm0 \
    libfreetype6 \
    libfribidi0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
