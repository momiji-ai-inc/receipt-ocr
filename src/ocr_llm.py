import os
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import openai
import json
from main import Receipt

# プロジェクトルートの.envを明示的に読み込む
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_receipt_info(img):
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key" or OPENAI_API_KEY == "YOUR_API_KEY":
        print("【警告】.envのOPENAI_API_KEYが未設定です。正しいAPIキーをセットしてください。")
        return None
    openai.api_key = OPENAI_API_KEY
    img_b64 = image_to_base64(img)
    prompt = (
        "領収書画像から、次の情報を日本語で抽出してください："
        "date（日時）, service（店舗名またはサービス名）, detail（使用用途）, price（金額）をjson形式で返してください。"
        "例: {\"date\": \"2024/04/01 12:34\", \"service\": \"コンビニ\", \"detail\": \"昼食\", \"price\": 800}"
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは日本語の領収書解析アシスタントです。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ],
            max_tokens=256
        )
        text = response.choices[0].message.content.strip()
        try:
            data = json.loads(text)
            receipt = Receipt(**data)
            return receipt.model_dump()
        except Exception:
            return None
    except Exception as e:
        print(f"OpenAI APIエラー: {e}")
        return None
