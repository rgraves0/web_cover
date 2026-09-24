import os
import io
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Client(
    "cover_gen_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def is_admin(_, __, message: Message):
    return message.from_user and message.from_user.id == ADMIN_ID

admin_filter = filters.create(is_admin)

def process_cover(image_bytes: bytes) -> str:
    target_width, target_height = 1200, 628
    
    # ၁။ မူရင်းပုံကို ဖွင့်ခြင်း
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # ၂။ အဓိကအရောင် (Dominant Color) ရှာဖွေခြင်း
    small = img.resize((150, 150))
    palette_img = small.quantize(colors=1)
    dominant_color = palette_img.getpalette()[:3]
    dominant_rgb = tuple(dominant_color)
    
    # ၃။ 1200x628 Canvas အသစ်တည်ဆောက်ပြီး အဓိကအရောင် ဖြည့်ခြင်း
    canvas = Image.new("RGB", (target_width, target_height), color=dominant_rgb)
    
    # ၄။ မူရင်းပုံကို 628x628 အဖြစ် Resize လုပ်ပြီး Center တည့်တည့် ချခြင်း
    square_size = target_height
    img_resized = img.resize((square_size, square_size), Image.Resampling.LANCZOS)
    x_offset = (target_width - square_size) // 2
    canvas.paste(img_resized, (x_offset, 0))
    
    # ၅။ KB အရွယ်အစားသာရှိစေရန် Optimize လုပ်ပြီး JPEG အဖြစ် Save ခြင်း
    output_path = "cover_1200x628.jpg"
    canvas.save(output_path, "JPEG", quality=85, optimize=True)
    return output_path

@bot.on_message(filters.command("start") & admin_filter)
async def start_cmd(client: Client, message: Message):
    await message.reply_text("မင်္ဂလာပါ။ 1200x628 ပြုလုပ်လိုသည့် Cover ပုံကို ပေးပို့ပေးပါ။")

@bot.on_message(filters.photo & admin_filter)
async def handle_photo(client: Client, message: Message):
    status_msg = await message.reply_text("ပုံကို ပြင်ဆင်နေပါသည်...")
    
    try:
        # ပုံကို download ရယူခြင်း
        photo_bytes = await message.download(in_memory=True)
        
        # 1200x628 သို့ ပြောင်းလဲခြင်း
        output_file = process_cover(photo_bytes.getbuffer())
        
        # ရလဒ်ပုံကို Document (File) အဖြစ် တိုက်ရိုက် ပြန်ပို့ပေးခြင်း
        await message.reply_document(
            document=output_file,
            caption="1200 x 628 Cover Photo အဆင်သင့်ဖြစ်ပါပြီ။"
        )
        
        # ယာယီဖိုင်ကို ပြန်ဖျက်ခြင်း
        if os.path.exists(output_file):
            os.remove(output_file)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"Error ဖြစ်ပွားပါသည်: {str(e)}")

bot.run()
