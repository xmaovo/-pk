import numpy as np
import streamlit as st
import easyocr
from PIL import Image

# 统一图片格式
def format_file_size(file_size_bytes):
    """将文件大小格式化为更易读的形式"""
    if file_size_bytes < 1024:
        return f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        return f"{file_size_bytes / 1024:.1f} KB"
    else:
        return f"{file_size_bytes / (1024 * 1024):.2f} MB"
    
# easyOCR初始
@st.cache_resource
def load_ocr_model():
    reader = easyocr.Reader(['ch_sim', 'en'])
    return reader

def run_ocr_on_image(uploaded_file):
    """
    对上传图片执行 OCR，返回：
    1. ocr_text: 拼接后的完整文本
    2. ocr_lines: 按行拆分的识别结果
    """
    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)

    ocr_model = load_ocr_model()
    result = ocr_model.readtext(image_np)

    ocr_lines = []

    if result:
        for line in result:
            # EasyOCR 返回格式通常是：
            # [bbox, text, score]
            text = line[1]
            score = line[2]
            ocr_lines.append({
                "text": text,
                "score": score
            })

    ocr_text = "\n".join([item["text"] for item in ocr_lines])

    return ocr_text, ocr_lines
