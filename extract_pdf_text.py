"""
从 PDF 中提取每页的文字内容和位置信息，保存为文本文件。
使用方法：python extract_pdf_text.py
"""
import os, sys, json
os.system(f"{sys.executable} -m pip install PyMuPDF --quiet")

import fitz

PDF_PATH = r"C:\Users\X\AppData\Local\Claude-3p\local-agent-mode-sessions\61a0cb38-cf3b-4d3d-a794-a1d69c1ade4e\00000000-0000-4000-8000-000000000001\local_0412bd85-f8b5-4f06-8159-0ee85c6fcc5b\uploads\RMT_Analytics_Perfect_Final.html"
OUT_DIR = r"D:\毕业论文\毕业设计\pdf_pages"

os.makedirs(OUT_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)
print(f"PDF 共 {len(doc)} 页\n")

for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text")
    blocks = page.get_text("blocks")  # 文字块：坐标 + 内容

    # 保存纯文本
    txt_path = os.path.join(OUT_DIR, f"page_{i+1:02d}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 保存结构化信息
    json_path = os.path.join(OUT_DIR, f"page_{i+1:02d}.json")
    structured = []
    for b in blocks:
        if b[6] == 0:  # 文字块
            structured.append({
                "x0": round(b[0], 1), "y0": round(b[1], 1),
                "x1": round(b[2], 1), "y1": round(b[3], 1),
                "text": b[4].strip()
            })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    print(f"第 {i+1} 页: {len(structured)} 个文字块 → {txt_path}")

doc.close()
print(f"\n✅ 完成！文字内容已保存到 {OUT_DIR}")
