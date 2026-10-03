import os
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile

from agents import generate_bmba_tests, generate_blitz, generate_guide
from generator import build_student_docx, build_teacher_docx, build_pdf_document

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()
app = FastAPI()

# Mini App sahifasini uzatish
@app.get("/", response_class=HTMLResponse)
async def serve_webapp():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# /start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Boshqaruv Markazi (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "Xush kelibsiz! Biologiya Test Fabrikasi va Agentlar Shtabini ishga tushirish uchun quyidagi tugmani bosing:",
        reply_markup=kb
    )

# Mini App dan kelgan buyurtmani qabul qilish
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    dept = data.get("dept")
    topic = data.get("topic")
    count = data.get("count", 10)

    status_msg = await message.answer(
        f"⚙️ **Buyurtma qabul qilindi!**\n"
        f"Bo'lim: `{dept}`\n"
        f"Mavzu: *{topic}*\n"
        f"Soni: {count} ta\n\n"
        f"⏳ *Agentlar zanjirli ishga tushmoqda, iltimos kuting...*"
    )

    # 5 va 6-agentlar orqali BMBA testlarini generatsiya qilish
    if dept == "bmba":
        async def update_status(agent_num, text):
            try:
                await status_msg.edit_text(f"🤖 **{agent_num}-Agent ishlamoqda:**\n_{text}_")
            except Exception:
                pass

        tests = await generate_bmba_tests(topic, count=count, status_callback=update_status)

        await status_msg.edit_text("📑 Hujjatlar CMU Serif formatida shakllantirilmoqda...")

        # Fayllar yo'li
        os.makedirs("output", exist_ok=True)
        s_docx = f"output/Oquvchi_{message.chat.id}.docx"
        t_docx = f"output/Oqituvchi_{message.chat.id}.docx"
        s_pdf = f"output/Oquvchi_{message.chat.id}.pdf"
        t_pdf = f"output/Oqituvchi_{message.chat.id}.pdf"

        # Word va PDF larni qurish
        build_student_docx(tests, s_docx)
        build_teacher_docx(tests, t_docx)
        build_pdf_document(tests, s_pdf, is_teacher=False)
        build_pdf_document(tests, t_pdf, is_teacher=True)

        # Fayllarni yuborish
        await message.answer_document(FSInputFile(s_docx), caption="📄 O'quvchi to'plami (Word)")
        await message.answer_document(FSInputFile(s_pdf), caption="📑 O'quvchi to'plami (PDF)")
        await message.answer_document(FSInputFile(t_docx), caption="📄 O'qituvchi to'plami (Ekspertiza Word)")
        await message.answer_document(FSInputFile(t_pdf), caption="📑 O'qituvchi to'plami (Ekspertiza PDF)")

        await status_msg.delete()

# Server va Botni bir vaqtda yurgizish
async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())