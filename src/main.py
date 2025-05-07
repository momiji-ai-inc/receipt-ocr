import os
import glob
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
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

def load_image(img_path):
    try:
        img = Image.open(img_path)
        return (img_path, img)
    except Exception as e:
        print(f"image load error: {img_path} {e}")
        return None

def load_pdf(pdf_path):
    try:
        pdf_images = pdf_to_images(pdf_path)
        if len(pdf_images) == 1:
            merged_img = pdf_images[0]
        elif len(pdf_images) >= 2:
            merged_img = concat_images_vertically(pdf_images)
        else:
            return None
        return (pdf_path, merged_img)
    except Exception as e:
        print(f"pdf load error: {pdf_path} {e}")
        return None

def ocr_and_save(args):
    path, img = args
    try:
        # OpenAI Vision APIの制限に合わせてリサイズ（長辺1024px以下、RGB化）
        max_side = 1024
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        scale = max(w, h) / max_side if max(w, h) > max_side else 1
        if scale > 1:
            img = img.resize((int(w / scale), int(h / scale)), Image.LANCZOS)
        info = extract_receipt_info(img)
        print(f">> {os.path.basename(path)}")
        print(f"  {info}")
        if info:
            result = info.model_dump()
            date = sanitize_filename(info.date.replace("/", ""))
            service = sanitize_filename(info.service)
            detail = sanitize_filename(info.detail)
            out_pdf = f"{date}_{service}_{detail}.pdf"
            out_pdf_path = os.path.join("output/pdfs", out_pdf)
            img.save(out_pdf_path, "PDF")
            return result
    except Exception as e:
        print(f"OCR error: {path} {e}")
    return None

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

    from concurrent.futures import ProcessPoolExecutor, as_completed
    from concurrent.futures import ThreadPoolExecutor

    # 画像・PDFの前処理（Image生成）をプロセス並列
    images = []
    with ProcessPoolExecutor() as p_executor:
        img_futures = [p_executor.submit(load_image, img_path) for img_path in img_files]
        pdf_futures = [p_executor.submit(load_pdf, pdf_path) for pdf_path in pdf_files]
        for future in as_completed(img_futures + pdf_futures):
            r = future.result()
            if r:
                images.append(r)

    # OCR部分をスレッド並列
    with ThreadPoolExecutor() as t_executor:
        ocr_futures = [t_executor.submit(ocr_and_save, args) for args in images]
        for future in as_completed(ocr_futures):
            r = future.result()
            if r:
                results.append(r)

    print(f"検出件数: {len(results)}")
    if results:
        save_to_csv(results)

if __name__ == "__main__":
    main("data")
