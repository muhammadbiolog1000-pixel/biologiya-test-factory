"""
BIOLOGIYA VEKTOR - ASOSIY SERVER VA BOT INTEGRATSIYASI (main.py)
"""
import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telebot.async_telebot import AsyncTeleBot
from google import genai
from agents import AGENT_PROMPTS
from generator import create_document

app = Flask(__name__, static_folder='.')
CORS(app)

# Konfiguratsiya (Muhit o'zgaruvchilari)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "SIZNING_GEMINI_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "SIZNING_BOT_TOKEN")

ai_client = genai.Client(api_key=GEMINI_KEY)
bot = AsyncTeleBot(BOT_TOKEN)

# Cron-job uchun uyg'oq saqlovchi yengil ping
@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

# Mini App frontendini ochish
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Gemini neyrotarmog'ini chaqirish funksiyasi
def ask_gemini(system_prompt: str, user_text: str) -> str:
    response = ai_client.models.generate_content(
        model='gemini-2.5-pro',
        contents=f"{system_prompt}\n\nTopshiriq:\n{user_text}"
    )
    return response.text

# 1-Departament: Blits
@app.route('/api/generate-blits', methods=['POST'])
async def generate_blits():
    data = request.json or {}
    topic = data.get('topic', 'Biologiya')
    telegram_id = data.get('telegramId')

    # 1 va 2-agentlar zanjiri
    draft = ask_gemini(AGENT_PROMPTS["agent1_blits_tuzuvchi"], topic)
    audited = ask_gemini(AGENT_PROMPTS["agent2_blits_nazoratchi"], draft)

    if telegram_id:
        doc_path = create_document(f"Blits: {topic}", audited, f"Blits_{telegram_id}.docx")
        with open(doc_path, 'rb') as f:
            await bot.send_document(telegram_id, f, caption=f"✅ '{topic}' mavzusida blits savol-javoblar tayyor!")
        os.remove(doc_path)

    return jsonify({"success": True, "result": audited})

# 2-Departament: Mavzuli chuqur testlar
@app.route('/api/generate-topic-test', methods=['POST'])
async def generate_topic_test():
    data = request.json or {}
    topic = data.get('topic', 'Biologiya')
    count = data.get('count', '10')
    telegram_id = data.get('telegramId')

    draft = ask_gemini(AGENT_PROMPTS["agent3_mavzu_testolog"], f"{topic} mavzusidan {count} ta polimorf test tuzing.")
    audited = ask_gemini(AGENT_PROMPTS["agent4_metodik_ekspert"], draft)

    if telegram_id:
        doc_path = create_document(f"Testlar: {topic}", audited, f"Test_{telegram_id}.docx")
        with open(doc_path, 'rb') as f:
            await bot.send_document(telegram_id, f, caption=f"✅ '{topic}' bo'yicha {count} ta test va metodik tahlil tayyor!")
        os.remove(doc_path)

    return jsonify({"success": True, "result": audited})

# 3-Departament: Milliy sertifikat (43 talik)
@app.route('/api/generate-sertifikat', methods=['POST'])
async def generate_sertifikat():
    data = request.json or {}
    variant_name = data.get('variantName', 'Variant-1')
    telegram_id = data.get('telegramId')

    exam = ask_gemini(AGENT_PROMPTS["agent5_katta_testolog"], f"Milliy sertifikat uchun yangi {variant_name} ni tuzing.")
    rubrika = ask_gemini(AGENT_PROMPTS["agent6_bosh_auditor"], exam)

    if telegram_id:
        # O'quvchi varianti
        doc_exam = create_document(f"Savol Kitobi: {variant_name}", exam, f"Exam_{telegram_id}.docx")
        with open(doc_exam, 'rb') as f:
            await bot.send_document(telegram_id, f, caption=f"📋 Milliy sertifikat sinov varianti ({variant_name}).")
        os.remove(doc_exam)

        # O'qituvchi varianti (M/A mezonlari)
        doc_rubrika = create_document(f"Yechimlar va Rubrika: {variant_name}", rubrika, f"Rubrika_{telegram_id}.docx")
        with open(doc_rubrika, 'rb') as f:
            await bot.send_document(telegram_id, f, caption=f"🔑 Maxfiy tekshiruv mezonlari va M/A yechimlar ({variant_name}).")
        os.remove(doc_rubrika)

    return jsonify({"success": True})

# 4-Departament: Qo'llanma
@app.route('/api/generate-guide', methods=['POST'])
async def generate_guide():
    data = request.json or {}
    topic = data.get('topic', 'Biologiya')
    telegram_id = data.get('telegramId')

    draft = ask_gemini(AGENT_PROMPTS["agent7_qollanma_arxitektori"], topic)
    final_guide = ask_gemini(AGENT_PROMPTS["agent8_akademik_redaktor"], draft)

    if telegram_id:
        doc_path = create_document(f"Qo'llanma: {topic}", final_guide, f"Qollanma_{telegram_id}.docx")
        with open(doc_path, 'rb') as f:
            await bot.send_document(telegram_id, f, caption=f"📚 '{topic}' bo'yicha 7 bosqichli akademik konspekt tayyor!")
        os.remove(doc_path)

    return jsonify({"success": True, "result": final_guide})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
