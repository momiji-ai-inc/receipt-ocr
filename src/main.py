import os
import glob
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
from ocr_llm import extract_receipt_info

def pdf_to_images(pdf_path: str):
    return convert_from_path(pdf_path)

def concat_images_vertically(images: list[Image.Image]) -> Image.Image:
    widths, heights = zip(*(img.size for img in images))
    total_height = sum(heights)
    max_width = max(widths)
    new_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))
    y_offset = 0
    for img in images:
        new_img.paste(img, (0, y_offset))
        y_offset += img.height
    return new_img

def sanitize_filename(s: str) -> str:
    return str(s).replace("/", "_").replace(" ", "_").replace("\t", "_")

def save_to_csv(results: list[dict]):
    os.makedirs("output", exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join("output", f"{now_str}.csv")

    df = pd.DataFrame(results)
    df["date"] = df["date"].str[:10]
    try:
        df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d")
    except Exception as e:
        print(f"date parse error: {e}")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    df = df[["date", "service", "detail", "price"]]
    df.to_csv(csv_path, index=False)

import shutil

def main(data_dir: str):
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    img_exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"]
    img_files = []
    for ext in img_exts:
        img_files.extend(glob.glob(os.path.join(data_dir, ext)))
        img_files.extend(glob.glob(os.path.join(data_dir, ext.upper())))
    print("[progress]")
    print(f"  PDFファイル数: {len(pdf_files)}")
    print(f"  画像ファイル数: {len(img_files)}")
    results = []

    if os.path.exists("output/pdfs"):
        shutil.rmtree("output/pdfs")
    os.makedirs("output/pdfs", exist_ok=True)

    # 画像ファイルを1枚ずつ処理
    for img_path in img_files:
        try:
            img = Image.open(img_path)
            info = extract_receipt_info(img)
            print(f">> {os.path.basename(img_path)}")
            print(f"  {info}")

            if info:
                results.append(info.model_dump())
                date = sanitize_filename(info.date.replace("/", ""))
                service = sanitize_filename(info.service)
                detail = sanitize_filename(info.detail)
                out_pdf = f"{date}_{service}_{detail}.pdf"
                out_pdf_path = os.path.join("output/pdfs", out_pdf)
                img.convert("RGB").save(out_pdf_path, "PDF")
        except Exception as e:
            print(f"image error: {img_path} {e}")

    # PDFは全ページを縦に連結して1枚の画像にして処理
    for pdf_path in pdf_files:
        try:
            pdf_images = pdf_to_images(pdf_path)
            if len(pdf_images) == 1:
                merged_img = pdf_images[0]
            elif len(pdf_images) >= 2:
                merged_img = concat_images_vertically(pdf_images)
            else:
                continue

            info = extract_receipt_info(merged_img)
            print(f">> {os.path.basename(pdf_path)}")
            print(f"  {info}")

            if info:
                results.append(info.model_dump())
                date = sanitize_filename(info.date.replace("/", ""))
                service = sanitize_filename(info.service)
                detail = sanitize_filename(info.detail)
                out_pdf = f"{date}_{service}_{detail}.pdf"
                out_pdf_path = os.path.join("output/pdfs", out_pdf)
                merged_img.convert("RGB").save(out_pdf_path, "PDF")
        except Exception as e:
            print(f"pdf error: {pdf_path} {e}")

    print(f"検出件数: {len(results)}")
    if results:
        save_to_csv(results)

if __name__ == "__main__":
    main("data")
