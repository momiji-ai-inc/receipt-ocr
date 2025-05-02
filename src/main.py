import os
import glob
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
from ocr_llm import extract_receipt_info

def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path)

def save_to_csv(results, csv_path):
    if results:
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)

def main(data_dir):
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    img_exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"]
    img_files = []
    for ext in img_exts:
        img_files.extend(glob.glob(os.path.join(data_dir, ext)))
    print(f"PDFファイル数: {len(pdf_files)}")
    print(f"画像ファイル数: {len(img_files)}")
    results = []
    for pdf_path in pdf_files:
        images = pdf_to_images(pdf_path)
        print(f"{os.path.basename(pdf_path)}: ページ数={len(images)}")
        for i, img in enumerate(images):
            info = extract_receipt_info(img)
            print(f"  ページ{i+1} OCR結果: {info}")
            if info:
                results.append(info)
    for img_path in img_files:
        try:
            img = Image.open(img_path)
            info = extract_receipt_info(img)
            if info:
                results.append(info)
        except Exception:
            pass
    print(f"OCR抽出結果数: {len(results)}")
    os.makedirs("output", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join("output", f"{now_str}.csv")
    save_to_csv(results, csv_path)
    print(f"CSV出力: {csv_path}")

if __name__ == "__main__":
    main("data")
