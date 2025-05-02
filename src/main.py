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

def save_to_csv(results):
    os.makedirs("output", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join("output", f"{now_str}.csv")

    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)

def main(data_dir):
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    img_exts = ["*.jpg", "*.JPG","*.jpeg", "*.png", "*.bmp", "*.gif"]
    img_files = []
    for ext in img_exts:
        img_files.extend(glob.glob(os.path.join(data_dir, ext)))
    print("[progress]")
    print(f"    PDFファイル数: {len(pdf_files)}")
    print(f"    画像ファイル数: {len(img_files)}")
    results = []
    for pdf_path in pdf_files:
        images = pdf_to_images(pdf_path)
        print(f">> {os.path.basename(pdf_path)}")
        for i, img in enumerate(images):
            info = extract_receipt_info(img)
            print(f"  [{i+1}/{len(images)}]: {info}")
            if info:
                results.append(info)
                break
    for img_path in img_files:
        try:
            img = Image.open(img_path)
            info = extract_receipt_info(img)
            if info:
                results.append(info)
        except Exception:
            pass
    print(f"検出件数: {len(results)}")
    if results:
        save_to_csv(results)

if __name__ == "__main__":
    main("data")
