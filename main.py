"""
BIOLOGIYA VEKTOR - FASTAPI & AIOGRAM 3 (main.py)
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot
from aiogram.types import FSInputFile
from google import genai

from agents import AGENT_PROMPTS
from generator import create_document

# Muhit o'zgaruvchilari (Render Environment Variables)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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

# Render uchun uyg'oq saqlovchi ping
@app.get("/ping")
async def ping():
    return "pong"

# Mini App bosh sahifasi (index.html)
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

def ask_gemini(system_prompt: str, user_text: str) -> str:
    response = ai_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"{system_prompt}\n\nTopshiriq:\n{user_text}"
    )
    return response.text

# 1-Departament: Blits
@app.post("/api/generate-blits")
async def generate_blits(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent1_blits_tuzuvchi"], topic)
    audited = ask_gemini(AGENT_PROMPTS["agent2_blits_nazoratchi"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Blits: {topic}", audited, f"Blits_{telegram_id}.docx")
        doc_file = FSInputFile(doc_path)
        await bot.send_document(chat_id=telegram_id, document=doc_file, caption=f"✅ '{topic}' mavzusida blits savol-javoblar tayyor!")
        os.remove(doc_path)

    return JSONResponse({"success": True, "result": audited})

# 2-Departament: Mavzuli chuqur testlar
@app.post("/api/generate-topic-test")
async def generate_topic_test(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    count = data.get("count", "10")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent3_mavzu_testolog"], f"{topic} mavzusidan {count} ta polimorf test tuzing.")
    audited = ask_gemini(AGENT_PROMPTS["agent4_metodik_ekspert"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Testlar: {topic}", audited, f"Test_{telegram_id}.docx")
        doc_file = FSInputFile(doc_path)
        await bot.send_document(chat_id=telegram_id, document=doc_file, caption=f"✅ '{topic}' bo'yicha {count} ta test va metodik tahlil tayyor!")
        os.remove(doc_path)

    return JSONResponse({"success": True, "result": audited})

# 3-Departament: Milliy sertifikat (43 talik)
@app.post("/api/generate-sertifikat")
async def generate_sertifikat(request: Request):
    data = await request.json()
    variant_name = data.get("variantName", "Variant-1")
    telegram_id = data.get("telegramId")

    exam = ask_gemini(AGENT_PROMPTS["agent5_katta_testolog"], f"Milliy sertifikat uchun yangi {variant_name} ni tuzing.")
    rubrika = ask_gemini(AGENT_PROMPTS["agent6_bosh_auditor"], exam)

    if telegram_id and bot:
        # O'quvchi varianti
        doc_exam = create_document(f"Savol Kitobi: {variant_name}", exam, f"Exam_{telegram_id}.docx")
        await bot.send_document(chat_id=telegram_id, document=FSInputFile(doc_exam), caption=f"📋 Milliy sertifikat sinov varianti ({variant_name}).")
        os.remove(doc_exam)

        # O'qituvchi varianti (M/A mezonlari)
        doc_rubrika = create_document(f"Yechimlar va Rubrika: {variant_name}", rubrika, f"Rubrika_{telegram_id}.docx")
        await bot.send_document(chat_id=telegram_id, document=FSInputFile(doc_rubrika), caption=f"🔑 Maxfiy tekshiruv mezonlari va M/A yechimlar ({variant_name}).")
        os.remove(doc_rubrika)

    return JSONResponse({"success": True})

# 4-Departament: 7 bosqichli Qo'llanma
@app.post("/api/generate-guide")
async def generate_guide(request: Request):
    data = await request.json()
    topic = data.get("topic", "Biologiya")
    telegram_id = data.get("telegramId")

    draft = ask_gemini(AGENT_PROMPTS["agent7_qollanma_arxitektori"], topic)
    final_guide = ask_gemini(AGENT_PROMPTS["agent8_akademik_redaktor"], draft)

    if telegram_id and bot:
        doc_path = create_document(f"Qo'llanma: {topic}", final_guide, f"Qollanma_{telegram_id}.docx")
        doc_file = FSInputFile(doc_path)
        await bot.send_document(chat_id=telegram_id, document=doc_file, caption=f"📚 '{topic}' bo'yicha 7 bosqichli akademik konspekt tayyor!")
        os.remove(doc_path)

    return JSONResponse({"success": True, "result": final_guide})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
