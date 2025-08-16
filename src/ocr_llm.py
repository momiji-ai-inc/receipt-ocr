import os
import base64
import json
from io import BytesIO
from dotenv import load_dotenv
import requests
from models import Receipt

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"

def image_to_base64(img) -> str:
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_receipt_info(img) -> Receipt | None:
    prompt = (
        "領収書画像から、次の情報を日本語で抽出してください："
        "date（購入日、時間は含めずYYYY/MM/DD形式）, service（店舗名またはサービス名）, detail（使用用途）, price（金額）をjson形式で返してください。"
        "例: {'date': '2024/04/01', 'service': 'Amazon', 'detail': '書籍代', 'price': 800}"
    )
    try:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        }
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ]
        }
        resp = requests.post(GEMINI_API_URL, headers=headers, json=data)
        resp.raise_for_status()
        resp_json = resp.json()
        # Geminiのレスポンステキスト抽出
        text = ""
        try:
            text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Gemini API response parse error: {e}\nRaw response: {resp_json}")
            return None
        # JSON部分を抽出してReceiptに変換
        try:
            json_str = text[text.find("{"):text.rfind("}")+1]
            data = json.loads(json_str)
            return Receipt(**data)
        except Exception as e:
            print(f"JSON parse error: {e}\nLLM response: {text}")
            return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None
