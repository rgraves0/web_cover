FROM python:3.11-alpine

WORKDIR /app

# Alpine အတွက် Pillow dependencies အနည်းငယ်သာ သွင်းခြင်း
RUN apk add --no-cache \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    gcc \
    musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build ပြီးတာနဲ့ compiler များကို ပြန်ဖျက်ပြီး storage ရှင်းထုတ်ခြင်း
RUN apk del gcc musl-dev

COPY . .

CMD ["python", "bot.py"]
