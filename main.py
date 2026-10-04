"""
BIOLOGIYA VEKTOR - ASOSIY SERVER VA BOT INTEGRATSIYASI (main.py)
FastAPI, Aiogram 3 va Google GenAI
"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import CommandStart
from google import genai

from agents import AGENT_PROMPTS, CAPACITY_ANALYZER_PROMPT, AGENT_NAMES
from generator import create_document

# Muhit o'zgaruvchilari (Render Environment Variables)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

# Bot /start komandasi
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        f"<b>Assalomu alaykum!</b>\n\n"
        f"Biologiya Testologiya Fabrikasi tizimiga xush kelibsiz.\n"
        f"Sizning Telegram ID raqamingiz: <code>{message.chat.id}</code>\n\n"
        f"Mini App orqali generatsiya qilingan barcha materiallar to'g'ridan-to'g'ri shu yerga Word va PDF formatida yuboriladi.",
        parse_mode="HTML"
    )

# Lifespan: Server yoqilganda botni ishga tushirish, o'chganda to'xtatish
@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = None
    if bot:
        # Eski osilib qolgan ulanishlarni tozalaymiz
        await bot.delete_webhook(drop_pending_updates=True)
        polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    if polling_task:
        polling_task.cancel()
    if bot:
        await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render uchun uyg'oq saqlovchi yengil ping
@app.get("/ping")
async def ping():
    return "pong"

# Mini App bosh sahifasi (index.html)
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>index.html fayli topilmadi.</h3>"

# Gemini neyrotarmog'iga so'rov yuborish
def ask_gemini(system_prompt: str, user_text: str) -> str:
    if not ai_client:
        return "Xatolik: GEMINI_API_KEY o'rnatilmagan."
    response = ai_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"{system_prompt}\n\nTopshiriq:\n{user_text}"
    )
    return response.text

# -----------------------------------------------------------------------------
# 0. MAVZU SIG'IMINI TAHLIL QILISH (🧠 Tugmasi uchun)
# -----------------------------------------------------------------------------
@app.post("/api/analyze-topic")
async def analyze_topic(request: Request):
    data = await request.json()
    topic = data.get("topic", "")
    if not topic.strip():
        return JSONResponse({"success": False, "error": "Mavzu kiritilmadi."})

    analysis = ask_gemini(CAPACITY_ANALYZER_PROMPT, f"Mavzu yoki matn:\n{topic}")
    return JSONResponse({"success": True, "analysis": analysis})

# -----------------------------------------------------------------------------
# 1-DEPARTAMENT: BLITS SAVOL-JAVOB
# -----------------------------------------------------------------------------
@app.post("/api/generate-blits")
async def generate_blits(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    count = data.get("count", "10")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent1"], f"{topic} mavzusidan {count} ta blits savol-javob shakllantiring.")
    audited = ask_gemini(AGENT_PROMPTS["agent2"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Blits: {topic}", audited, f"Blits_{telegram_id}.docx")
        if os.path.exists(doc_path):
            await bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(doc_path),
                caption=f"⚡️ <b>{topic}</b> bo'yicha blits savol-javoblar tayyor!",
                parse_mode="HTML"
            )
            os.remove(doc_path)

    return JSONResponse({"success": True, "result": audited})

# -----------------------------------------------------------------------------
# 2-DEPARTAMENT: MAVZULASHTIRILGAN CHUQUR TESTLAR
# -----------------------------------------------------------------------------
@app.post("/api/generate-topic-test")
async def generate_topic_test(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    count = data.get("count", "10")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent3"], f"{topic} mavzusidan {count} ta chuqurlashtirilgan polimorf test tuzing.")
    audited = ask_gemini(AGENT_PROMPTS["agent4"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Mavzuli Testlar: {topic}", audited, f"Test_{telegram_id}.docx")
        if os.path.exists(doc_path):
            await bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(doc_path),
                caption=f"📝 <b>{topic}</b> bo'yicha {count} ta test va metodik tahlil tayyor!",
                parse_mode="HTML"
            )
            os.remove(doc_path)

    return JSONResponse({"success": True, "result": audited})

# -----------------------------------------------------------------------------
# 3-DEPARTAMENT: MILLIY SERTIFIKAT (43 TALIK TO'LIQ BLOK)
# -----------------------------------------------------------------------------
@app.post("/api/generate-sertifikat")
async def generate_sertifikat(request: Request):
    data = await request.json()
    variant_name = data.get("variantName", "BMBA Milliy Sertifikat")
    telegram_id = data.get("telegramId")

    # 5-Agent to'liq 43 talik variant tuzadi (mavzu so'ralmaydi, butun biologiya qamrab olinadi)
    exam = ask_gemini(
        AGENT_PROMPTS["agent5"],
        f"Butun biologiya kursi (Botanika, Zoologiya, Anatomiya, Sitologiya, Genetika) bo'yicha yangi rasmiy {variant_name} ni to'liq (1-43) shakllantiring."
    )
    # 6-Agent tekshiradi va M/A yechimlar rubrikasini tuzadi
    rubrika = ask_gemini(AGENT_PROMPTS["agent6"], exam)

    if telegram_id and bot:
        # O'quvchi varianti
        doc_exam = create_document(f"Savol Kitobi: {variant_name}", exam, f"Exam_{telegram_id}.docx")
        if os.path.exists(doc_exam):
            await bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(doc_exam),
                caption=f"📋 <b>{variant_name}</b> — Sinov varianti (O'quvchi uchun).",
                parse_mode="HTML"
            )
            os.remove(doc_exam)

        # O'qituvchi varianti (M/A mezonlari va qadamma-qadam yechimlar)
        doc_rubrika = create_document(f"Maxfiy Rubrika: {variant_name}", rubrika, f"Rubrika_{telegram_id}.docx")
        if os.path.exists(doc_rubrika):
            await bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(doc_rubrika),
                caption=f"🔑 <b>{variant_name}</b> — Ekspert rubrikasi va M/A baholash mezonlari (O'qituvchi uchun).",
                parse_mode="HTML"
            )
            os.remove(doc_rubrika)

    return JSONResponse({"success": True, "exam": exam, "rubrika": rubrika})

# -----------------------------------------------------------------------------
# 4-DEPARTAMENT: 7 BOSQICHLI QO'LLANMA VA KONSPEKT
# -----------------------------------------------------------------------------
@app.post("/api/generate-guide")
async def generate_guide(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent7"], f"{topic} mavzusini 7 bosqichli universal formula asosida to'liq yoriting.")
    final_guide = ask_gemini(AGENT_PROMPTS["agent8"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Qo'llanma: {topic}", final_guide, f"Qollanma_{telegram_id}.docx")
        if os.path.exists(doc_path):
            await bot.send_document(
                chat_id=telegram_id,
                document=FSInputFile(doc_path),
                caption=f"📚 <b>{topic}</b> bo'yicha 7 bosqichli akademik konspekt tayyor!",
                parse_mode="HTML"
            )
            os.remove(doc_path)

    return JSONResponse({"success": True, "result": final_guide})

# -----------------------------------------------------------------------------
# 5. AGENTLAR BILAN INDIVIDUAL CHAT MARKAZI
# -----------------------------------------------------------------------------
@app.post("/api/chat-agent")
async def chat_agent(request: Request):
    data = await request.json()
    agent_key = data.get("agentKey", "agent1")
    user_message = data.get("message", "")

    system_prompt = AGENT_PROMPTS.get(agent_key, AGENT_PROMPTS["agent1"])
    agent_name = AGENT_NAMES.get(agent_key, "Agent")

    reply = ask_gemini(
        f"{system_prompt}\nSiz hozir o'qituvchi/foydalanuvchi bilan bevosita professional chat qilyapsiz. O'z mutaxassisligingizdan kelib chiqib, aniq va ilmiy javob bering.",
        user_message
    )
    return JSONResponse({"success": True, "agent": agent_name, "reply": reply})

# -----------------------------------------------------------------------------
# 6. AGENTLAR SHTABI: PROMPTLARNI KO'RISH VA YANGILASH
# -----------------------------------------------------------------------------
@app.get("/api/prompts")
async def get_prompts():
    return JSONResponse(AGENT_PROMPTS)

@app.post("/api/prompts")
async def update_prompt(request: Request):
    data = await request.json()
    key = data.get("key")
    prompt = data.get("prompt")
    if key in AGENT_PROMPTS and prompt:
        AGENT_PROMPTS[key] = prompt
        return JSONResponse({"success": True, "message": f"{key} prompti muvaffaqiyatli yangilandi!"})
    return JSONResponse({"success": False, "error": "Bunday agent mavjud emas yoki matn bo'sh."}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
