import pandas as pd
import streamlit as st

# 利率数值
def parse_rate(rate_str):
    if pd.isna(rate_str):
        return None

    rate_str = str(rate_str).replace("%", "").strip()

    try:
        return float(rate_str)
    except ValueError:
        return None
    
# 额度数值
def parse_amount(amount):
    if pd.isna(amount):
        return None
    try:
        return float(amount)
    except ValueError:
        return None
    
def parse_amount_text(amount_text):
    if pd.isna(amount_text):
        return None

    text = str(amount_text).strip()
    text = text.replace("万元", "").replace("万", "").strip()

    try:
        return float(text)
    except ValueError:
        return None
    
def format_amount_as_wanyuan(value):
    """
    将额度统一显示为“数字+万元”
    例如：
    300 -> 300万元
    300.0 -> 300万元
    15万元 -> 15万元
    空值 -> ""
    """
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if text == "":
        return ""

    # 已经带“万元”就直接返回
    if "万元" in text:
        return text

    # 去掉可能已有的“万”
    text = text.replace("万", "").strip()

    try:
        num = float(text)
        if num.is_integer():
            return f"{int(num)}万元"
        return f"{num}万元"
    except ValueError:
        return text
    
@st.cache_data
def load_products(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["interest_rate_num"] = df["interest_rate"].apply(parse_rate)
    df["loan_amount_max_num"] = df["loan_amount_max"].apply(parse_amount)
    df["data_source"] = "内置产品库"
    return df

# 标准化OCR产品记录
def convert_extracted_to_product_record(extracted_result, idx=None):
    record = {
        "product_id": f"OCR_{idx}" if idx is not None else "OCR_TEMP",
        "bank_name": extracted_result.get("bank_name", ""),
        "product_name": extracted_result.get("product_name", ""),
        "interest_rate": "",
        "loan_amount_min": "",
        "loan_amount_max": extracted_result.get("loan_amount_max", ""),
        "loan_term": extracted_result.get("loan_term", ""),
        "repayment_method": extracted_result.get("repayment_method", ""),
        "guarantee_type": extracted_result.get("guarantee_type", ""),
        "target_customer": "",
        "application_mode": "",
        "approval_speed": "",
        "remark": extracted_result.get("product_features", ""),
        "data_source": "海报OCR识别"
    }
    return record

# 合并产品表
def build_combined_products_df(df_selected, uploaded_product_records):
    """
    将内置产品与 OCR 提取出的产品合并为统一 DataFrame
    """
    if uploaded_product_records:
        df_uploaded = pd.DataFrame(uploaded_product_records)
        combined_df = pd.concat([df_selected, df_uploaded], ignore_index=True, sort=False)
    else:
        combined_df = df_selected.copy()

    return combined_df

def dataframe_to_csv_download(df):
    """
    将 DataFrame 转为可下载的 CSV 字节流（UTF-8 with BOM，兼容 Excel 打开中文）
    """
    return df.to_csv(index=False).encode("utf-8-sig")

def get_lowest_rate_product(df):
    df_valid = df[df["interest_rate_num"].notna()].copy()
    if df_valid.empty:
        return "", ""
    row = df_valid.sort_values("interest_rate_num").iloc[0]
    return row["product_name"], row["interest_rate"]


def get_highest_amount_product(df):
    temp_df = df.copy()
    temp_df["loan_amount_max_calc"] = temp_df["loan_amount_max"].apply(parse_amount_text)
    df_valid = temp_df[temp_df["loan_amount_max_calc"].notna()].copy()
    if df_valid.empty:
        return "", ""
    row = df_valid.sort_values("loan_amount_max_calc", ascending=False).iloc[0]
    return row["product_name"], format_amount_as_wanyuan(row["loan_amount_max"])