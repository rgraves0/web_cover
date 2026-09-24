import os
import io
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

FONT_PATH = "Pyidaungsu.ttf"

bot = Client(
    "cover_gen_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Admin တစ်ယောက်တည်းသာ သုံးနိုင်စေရန် စစ်ဆေးခြင်း
def is_admin(_, __, message: Message):
    return message.from_user and message.from_user.id == ADMIN_ID

admin_filter = filters.create(is_admin)

def process_cover(image_bytes: bytes, album_name: str, artist_name: str) -> str:
    target_width, target_height = 1200, 628
    
    # ပုံကို ဖွင့်ခြင်း
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # အဓိကအရောင် (Dominant Color) ရှာဖွေခြင်း
    small = img.resize((150, 150))
    palette_img = small.quantize(colors=1)
    dominant_color = palette_img.getpalette()[:3]
    dominant_rgb = tuple(dominant_color)
    
    # 1200x628 Background Canvas တည်ဆောက်ခြင်း
    canvas = Image.new("RGB", (target_width, target_height), color=dominant_rgb)
    
    # ပုံကို 628x628 အဖြစ် Center ချခြင်း
    square_size = target_height
    img_resized = img.resize((square_size, square_size), Image.Resampling.LANCZOS)
    x_offset = (target_width - square_size) // 2
    canvas.paste(img_resized, (x_offset, 0))
    
    # Background အရောင်ပေါ်မူတည်ပြီး စာသားအရောင် အမည်း သို့မဟုတ် အဖြူ ရွေးခြင်း
    luminance = 0.299 * dominant_rgb[0] + 0.587 * dominant_rgb[1] + 0.114 * dominant_rgb[2]
    text_color = (20, 20, 20) if luminance > 130 else (240, 240, 240)
    
    # Text Layer ဖန်တီးခြင်း
    font_size = 24
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    display_text = f"{album_name}     {artist_name}"
    
    # စာသားကို ယာယီ layer ပေါ်ရေးပြီး ၉၀ ဒီဂရီ လှည့်ခြင်း
    txt_canvas = Image.new("RGBA", (550, 60), (255, 255, 255, 0))
    draw_txt = ImageDraw.Draw(txt_canvas)
    draw_txt.text((10, 10), display_text, font=font, fill=text_color)
    
    rotated_txt = txt_canvas.rotate(90, expand=True)
    canvas.paste(rotated_txt, (target_width - 70, 80), rotated_txt)
    
    # JPEG အဖြစ် Save ခြင်း (KB သာရှိစေရန် optimize ပြုလုပ်ထားသည်)
    output_path = f"{album_name}.jpg"
    canvas.save(output_path, "JPEG", quality=85, optimize=True)
    return output_path

@bot.on_message(filters.command("start") & admin_filter)
async def start_cmd(client: Client, message: Message):
    await message.reply_text("မင်္ဂလာပါ။ 1200x628 ပြုလုပ်လိုသည့် Cover ပုံကို ပေးပို့ပေးပါ။")

@bot.on_message(filters.photo & admin_filter)
async def handle_photo(client: Client, message: Message):
    status_msg = await message.reply_text(
        "ပုံကို ရရှိပါပြီ။\n\n**Album Name | Artist Name** ပုံစံဖြင့် စာသား ရိုက်ပို့ပေးပါ:\n(ဥပမာ - `ခေတ်ဟောင်းသီချင်းများ | စိုးသူ`)"
    )
    
    # User ထံမှ စာသားကို စောင့်ဆိုင်းခြင်း
    response = await client.listen.Message(
        filters.text & filters.user(ADMIN_ID),
        timeout=180
    )
    
    if not response or not response.text:
        await status_msg.edit_text("အချိန်ကျော်လွန်သွားပါပြီ။ ပုံကို ပြန်လည်ပို့ပေးပါ။")
        return

    text_input = response.text.strip()
    if "|" in text_input:
        album_name, artist_name = [part.strip() for part in text_input.split("|", 1)]
    else:
        album_name = text_input
        artist_name = ""

    await status_msg.edit_text("ပုံကို ဖန်တီးနေပါသည်...")
    
    # Photo ကို download ဆွဲခြင်း
    photo_bytes = await message.download(in_memory=True)
    
    output_file = process_cover(photo_bytes.getbuffer(), album_name, artist_name)
    
    # ရလဒ်ပုံကို Document အဖြစ် ပြန်ပို့ပေးခြင်း
    await message.reply_document(
        document=output_file,
        caption=f"**Album:** {album_name}\n**Artist:** {artist_name}"
    )
    
    if os.path.exists(output_file):
        os.remove(output_file)
    await status_msg.delete()

bot.run()
