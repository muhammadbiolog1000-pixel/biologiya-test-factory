import os
import json
from google import genai
from google.genai import types

# Gemini API mijozi
api_key = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=api_key) if api_key else None

MODEL_NAME = "gemini-2.5-pro"

# 1 & 2-AGENTLAR: BLITS SAVOL-JAVOB
PROMPT_AGENT_1_BLITZ = """
Siz biologiya fanidan tezkor faktik xotira bo'yicha mutaxassisiz.
Vazifangiz darslik matnidan qisqa, aniq va lo'nda "Savol -> Javob" to'plamini tuzish.
Qoidalar:
- Savol 1 jumlada aniq qo'yiladi.
- Javob qat'iy ravishda 1-3 ta so'zdan (yoki aniq sondan/atamadan) oshmasligi shart.
- Bahsli, bir nechta talqinga ega savollar tuzish taqiqlanadi.
Format: JSON ro'yxat: [{"id": 1, "savol": "...", "javob": "..."}]
"""

# 3 & 4-AGENTLAR: MAVZULASHTIRILGAN TESTLAR
PROMPT_AGENT_3_TOPIC = """
Siz biologiya fanidan mavzulashtirilgan testologsiz.
Vazifangiz berilgan mavzular doirasida chuqur ilmiy solishtirma (o'xshashlik a, farqlar b), xususiyatlarni moslashtirish va tahliliy testlar tuzish.
Qoidalar:
- Belgilangan mavzulardan chetga chiqilmasin.
- Sun'iy integratsiya qilinmasin, biologik mohiyatga (fermentlar, tuzilmalar, mexanizmlar farqiga) e'tibor berilsin.
- Variantlar (A, B, C, D) aynan shu mavzulardagi faktlar bilan adashtiruvchi bo'lsin.
Format: JSON ro'yxat.
"""

# 5-AGENT: MILLIY SERTIFIKAT (BMBA ELIT) TUZUVCHI
PROMPT_AGENT_5_BMBA = """
Siz Respublika BMBA (DTM) milliy sertifikatining yetakchi biologiya testolog-ekspertisiz.
Vazifangiz o'quvchini chuqur fikrlashga, sabab-oqibatni tahlil qilishga majbur qiluvchi ELIT savollar tuzish.
Asosiy qoliplar:
1. Ko'p faktli hukmlar (8-11 ta fakt) -> 'Nechtasi to'g'ri/noto'g'ri?'
2. To'g'ri (a) va noto'g'ri (b) guruhlash (6-8 ta hukm).
3. Uch bosqichli kross-moslashtirish (I-II-III / 1-2-3 / a-b-c).
Variantlar simmetrik va chalg'ituvchi bo'lsin, chiqarib tashlash (isklyucheniye) usuliga yo'l qo'yilmasin.
Chiqish formati QAT'IY JSON:
{
  "shart": "Savol matni",
  "hukmlar": ["1) ...", "2) ..."],
  "variantlar": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "kalit": "A",
  "tahlil": {
    "ilmiy_asos": "Har bir hukmning to'g'ri/xatolik isboti",
    "distraktorlar_mantiqi": "Boshqa variantlar qanday tuzoqqa qurilgan",
    "taksonomiya": "Tahlil / Baholash"
  }
}
"""

# 6-AGENT: BMBA BOSH AUDITOR (QATTIQQO'L NAZORAT)
PROMPT_AGENT_6_AUDITOR = """
Siz BMBA Bosh Auditorisiz. 5-Agent tuzgan testni quyidagi 4 filtrdan o'tkazasiz:
1. Isklyucheniye filtri: O'quvchi faqat bitta faktni bilish bilan to'g'ri javobni topib ololmaydimi?
2. Ilmiy aniqlik: Darslikka 100% mosmi, ikki xil ma'no yo'qmi?
3. Distraktor kuchi: Noto'g'ri variantlar yetarlicha kuchlimi?
4. Qat'iy format talabiga muvofiqlik.
Agar xato bo'lsa testni to'g'rilab, mukammal JSON holatida qaytaring.
"""

# 7 & 8-AGENTLAR: QO'LLANMA VA KONSPEKT
PROMPT_AGENT_7_GUIDE = """
Siz biologiya bo'yicha pedagogik dizayner va metodistsiz.
Vazifangiz mavzuni quyidagi 4 ta blokda konspekt qilish:
1. Kalit terminlar va ularning aniq ma'nosi.
2. Taqqoslash jadvallari (O'xshashlik va farqlar).
3. Jarayonlar va mexanizmlar bosqichlari.
4. "Diqqat: Test tuzog'i!" (BMBA/DTM da eng ko'p chalg'itadigan nuqtalar).
Ortiqcha quruq gaplarsiz, sof biologik ma'lumot bering.
"""

async def generate_bmba_tests(topic_text: str, count: int = 10, status_callback=None):
    """5 va 6-agentlar orqali BMBA testlarini zanjirli yaratish va audit qilish"""
    results = []
    for i in range(count):
        if status_callback:
            await status_callback(5, f"{i+1}/{count}-savol BMBA qolipida tuzilmoqda...")
        
        # 5-Agent: Yaratish
        prompt_draft = f"Mavzu/Matn: {topic_text}\nUshbu manbadan {i+1}-raqamli elit BMBA testini tuzing."
        resp_draft = client.models.generate_content(
            model=MODEL_NAME,
            contents=[PROMPT_AGENT_5_BMBA, prompt_draft],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        if status_callback:
            await status_callback(6, f"{i+1}/{count}-savol Bosh Auditor tekshiruvidan o'tmoqda...")
            
        # 6-Agent: Qattiqqo'l audit
        audit_prompt = f"Mana 5-Agent tuzgan test loyihasi:\n{resp_draft.text}\nBuni qat'iy auditdan o'tkazing va yakuniy mukammal JSON ni qaytaring."
        resp_final = client.models.generate_content(
            model=MODEL_NAME,
            contents=[PROMPT_AGENT_6_AUDITOR, audit_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        try:
            test_obj = json.loads(resp_final.text)
            test_obj["id"] = i + 1
            results.append(test_obj)
        except Exception:
            pass

    return results

async def generate_blitz(topic_text: str, count: int = 20):
    """1 va 2-agentlar orqali Blits savol-javob to'plami"""
    prompt = f"Mavzu: {topic_text}\nJami {count} ta qisqa va aniq savol-javob to'plamini tuzing."
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[PROMPT_AGENT_1_BLITZ, prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(resp.text)

async def generate_guide(topic_text: str):
    """7 va 8-agentlar orqali O'quv qo'llanma / Konspekt tayyorlash"""
    prompt = f"Mavzu: {topic_text}\nUshbu mavzu bo'yicha to'liq 4 blokli konspekt-qo'llanma tayyorlang."
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[PROMPT_AGENT_7_GUIDE, prompt]
    )
    return resp.text