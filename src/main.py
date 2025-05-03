import os
import glob
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
from ocr_llm import extract_receipt_info
from models import Receipt

def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path)

def concat_images_vertically(images):
    widths, heights = zip(*(img.size for img in images))
    total_height = sum(heights)
    max_width = max(widths)
    new_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))
    y_offset = 0
    for img in images:
        new_img.paste(img, (0, y_offset))
        y_offset += img.height
    return new_img

def save_to_csv(results):
    os.makedirs("output", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join("output", f"{now_str}.csv")

    df = pd.DataFrame(results)
    df["date"] = df["date"].str[:10]
    df = df[["date", "service", "detail", "price"]]
    df.to_csv(csv_path, index=False)

def main(data_dir):
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    img_exts = ["*.jpg", "*.JPG", "*.jpeg", "*.png", "*.bmp", "*.gif"]
    img_files = []
    for ext in img_exts:
        img_files.extend(glob.glob(os.path.join(data_dir, ext)))
    print("[progress]")
    print(f"  PDFファイル数: {len(pdf_files)}")
    print(f"  画像ファイル数: {len(img_files)}")
    results = []

    # 画像ファイルを1枚ずつ処理
    for img_path in img_files:
        try:
            img = Image.open(img_path)
            info = extract_receipt_info(img)
            print(f">> {os.path.basename(pdf_path)}")
            print(f"  {info}")
            if info:
                results.append(info.model_dump())
        except Exception:
            pass

    # PDFは全ページを縦に連結して1枚の画像にして処理
    for pdf_path in pdf_files:
        try:
            pdf_images = pdf_to_images(pdf_path)
            if len(pdf_images) == 1:
                merged_img = pdf_images[0]
            elif len(pdf_images) >= 2:
                merged_img = concat_images_vertically(pdf_images)

            info = extract_receipt_info(merged_img)
            print(f">> {os.path.basename(pdf_path)}")
            print(f"  {info}")
            if info:
                results.append(info.model_dump())
        except Exception:
            pass

    print(f"検出件数: {len(results)}")
    if results:
        save_to_csv(results)

if __name__ == "__main__":
    main("data")
