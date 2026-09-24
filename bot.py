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

# Admin စစ်ဆေးခြင်း
def is_admin(_, __, message: Message):
    return message.from_user and message.from_user.id == ADMIN_ID

admin_filter = filters.create(is_admin)

# ပို့ထားသော ပုံကို ယာယီမှတ်ထားမည့် dictionary
user_states = {}

def process_cover(image_bytes: bytes, album_name: str, artist_name: str) -> str:
    target_width, target_height = 1200, 628
    
    # ၁။ မူရင်းပုံကို ဖွင့်ခြင်း
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # ၂။ အဓိကအရောင် (Dominant Color) ရှာဖွေခြင်း
    small = img.resize((150, 150))
    palette_img = small.quantize(colors=1)
    dominant_color = palette_img.getpalette()[:3]
    dominant_rgb = tuple(dominant_color)
    
    # ၃။ 1200x628 Canvas အသစ်တည်ဆောက်ခြင်း
    canvas = Image.new("RGB", (target_width, target_height), color=dominant_rgb)
    
    # ၄။ ပုံကို 628x628 အဖြစ် အလယ်ချခြင်း
    square_size = target_height
    img_resized = img.resize((square_size, square_size), Image.Resampling.LANCZOS)
    x_offset = (target_width - square_size) // 2
    canvas.paste(img_resized, (x_offset, 0))
    
    # ၅။ Background အရောင်ပေါ်မူတည်ပြီး Text အရောင် (အဖြူ/အမည်း) ရွေးခြင်း
    luminance = 0.299 * dominant_rgb[0] + 0.587 * dominant_rgb[1] + 0.114 * dominant_rgb[2]
    text_color = (20, 20, 20) if luminance > 130 else (240, 240, 240)
    
    # ၆။ Font နှင့် စာသားပြင်ဆင်ခြင်း
    font_size = 24
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    display_text = f"{album_name}     {artist_name}"
    
    # စာသားရှည်ပါက မပြတ်သွားစေရန် အလျား 800px ယူထားပါသည်
    txt_canvas = Image.new("RGBA", (800, 80), (255, 255, 255, 0))
    draw_txt = ImageDraw.Draw(txt_canvas)
    
    # မြန်မာ Unicode စာလုံးပေါင်း အထားအသိုမှန်စေရန် direction="ltr" ဖြင့် ဆွဲခြင်း
    try:
        draw_txt.text(
            (10, 15),
            display_text,
            font=font,
            fill=text_color,
            direction="ltr",
            features=["kern", "liga"]
        )
    except TypeError:
        draw_txt.text((10, 15), display_text, font=font, fill=text_color)
    
    # စာသားကို ၉၀ ဒီဂရီ လှည့်ခြင်း
    rotated_txt = txt_canvas.rotate(90, expand=True)
    canvas.paste(rotated_txt, (target_width - 80, 50), rotated_txt)
    
    # ၇။ JPEG အဖြစ် သိမ်းဆည်းခြင်း
    output_path = f"{album_name}.jpg"
    canvas.save(output_path, "JPEG", quality=85, optimize=True)
    return output_path

@bot.on_message(filters.command("start") & admin_filter)
async def start_cmd(client: Client, message: Message):
    await message.reply_text("မင်္ဂလာပါ။ 1200x628 ပြုလုပ်လိုသည့် Cover ပုံကို ပေးပို့ပေးပါ။")

@bot.on_message(filters.photo & admin_filter)
async def handle_photo(client: Client, message: Message):
    photo_bytes = await message.download(in_memory=True)
    user_states[message.from_user.id] = photo_bytes.getbuffer()
    
    await message.reply_text(
        "ပုံကို လက်ခံရရှိပါပြီ။\n\n**Album Name | Artist Name** ပုံစံဖြင့် စာသား ရိုက်ပို့ပေးပါ:\n(ဥပမာ - `ခေတ်ဟောင်းသီချင်းများ | စိုးသူ`)"
    )

@bot.on_message(filters.text & admin_filter & ~filters.command(["start"]))
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        await message.reply_text("ကျေးဇူးပြု၍ အရင်ဆုံး Cover ပုံကို ပေးပို့ပေးပါခင်ဗျာ။")
        return

    text_input = message.text.strip()
    if "|" in text_input:
        album_name, artist_name = [part.strip() for part in text_input.split("|", 1)]
    else:
        album_name = text_input
        artist_name = ""

    status_msg = await message.reply_text("ပုံကို ပြင်ဆင်နေပါသည်...")
    
    try:
        photo_buffer = user_states[user_id]
        output_file = process_cover(photo_buffer, album_name, artist_name)
        
        await message.reply_document(
            document=output_file,
            caption=f"**Album:** {album_name}\n**Artist:** {artist_name}"
        )
        
        if os.path.exists(output_file):
            os.remove(output_file)
            
        del user_states[user_id]
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"Error ဖြစ်ပွားပါသည်: {str(e)}")

bot.run()
