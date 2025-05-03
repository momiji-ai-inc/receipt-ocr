import os
import json
import base64
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from models import Receipt

# プロジェクトルートの.envを明示的に読み込む
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extract_receipt_info(img) -> Receipt:
    client = OpenAI(api_key=OPENAI_API_KEY)
    img_b64 = image_to_base64(img)
    prompt = (
        "領収書画像から、次の情報を日本語で抽出してください："
        "date（購入日、時間は含めずYYYY/MM/DD形式）, service（店舗名またはサービス名）, detail（使用用途）, price（金額）をjson形式で返してください。"
        "例: {'date': '2024/04/01', 'service': 'Amazon', 'detail': '書籍代', 'price': 800}"
    )
    completion = client.beta.chat.completions.parse(
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
        response_format=Receipt,
    )
    receipt = completion.choices[0].message.parsed
    return receipt
