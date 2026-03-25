import pandas as pd
from modules.data_utils import parse_amount_text

# 高亮函数
def highlight_compare_table(row):
    styles = [""] * len(row)

    row_name = row.name

    # 利率：越低越好
    if row_name == "利率":
        numeric_values = []
        for v in row:
            try:
                numeric_values.append(float(str(v).replace("%", "").strip()))
            except:
                numeric_values.append(None)

        valid_values = [v for v in numeric_values if v is not None]
        if valid_values:
            min_value = min(valid_values)
            for i, v in enumerate(numeric_values):
                if v == min_value:
                    styles[i] = "background-color: #d9f2d9"

    # 最高额度：越高越好
    elif "最高额度" in str(row_name):
        numeric_values = []
        for v in row:
            numeric_values.append(parse_amount_text(v))

        valid_values = [v for v in numeric_values if v is not None]
        if valid_values:
            max_value = max(valid_values)
            for i, v in enumerate(numeric_values):
                if v == max_value:
                    styles[i] = "background-color: #fff2cc"

    return styles

def highlight_combined_table(row):
    styles = [""] * len(row)

    # 如果是 OCR 识别产品，整行轻微着色
    if "数据来源" in row.index and row["数据来源"] == "海报OCR识别":
        styles = ["background-color: #f5f9ff"] * len(row)

    return styles

def highlight_pk_table(row):
    styles = [""] * len(row)
    row_name = row.name

    # 利率：越低越好
    if row_name == "利率":
        numeric_values = []
        for v in row:
            try:
                numeric_values.append(float(str(v).replace("%", "").strip()))
            except:
                numeric_values.append(None)

        valid_values = [v for v in numeric_values if v is not None]
        if valid_values:
            min_value = min(valid_values)
            for i, v in enumerate(numeric_values):
                if v == min_value:
                    styles[i] = "background-color: #d9f2d9"

    # 最高额度：越高越好
    elif row_name == "最高额度":
        numeric_values = []
        for v in row:
            numeric_values.append(parse_amount_text(v))

        valid_values = [v for v in numeric_values if v is not None]
        if valid_values:
            max_value = max(valid_values)
            for i, v in enumerate(numeric_values):
                if v == max_value:
                    styles[i] = "background-color: #fff2cc"

    return styles