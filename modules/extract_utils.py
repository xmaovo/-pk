import re

# 清洗函数
def clean_ocr_text(ocr_text):
    """
    对 OCR 原始文本做基础清洗
    """
    if not ocr_text:
        return ""

    text = ocr_text

    # 统一中英文标点和空白
    text = text.replace("：", ":")
    text = text.replace("；", ";")
    text = text.replace("，", ",")
    text = text.replace("。", "。")
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]+", " ", text)

    # 去掉过多空行
    text = re.sub(r"\n+", "\n", text).strip()

    return text

# 提取内容
def extract_bank_name(text):
    bank_map = {
        "中国邮政储蓄银行": "中国邮政储蓄银行",
        "邮储银行": "中国邮政储蓄银行",
        "中国农业银行": "中国农业银行",
        "农业银行": "中国农业银行",
        "中国工商银行": "中国工商银行",
        "工商银行": "中国工商银行",
        "中国建设银行": "中国建设银行",
        "建设银行": "中国建设银行",
        "中国银行": "中国银行",
        "交通银行": "交通银行",
        "招商银行": "招商银行",
        "浦发银行": "浦发银行",
        "中信银行": "中信银行"
    }

    for k, v in bank_map.items():
        if k in text:
            return v

    return ""

def extract_product_name(text):
    product_keywords = [
        "科创贷",
        "小微易贷",
        "线上信用户贷款",
        "续捷e贷",
        "助农贷",
        "经营贷",
        "商户贷",
        "税贷",
        "发票贷"
    ]

    # 先做简单纠错
    corrected_text = text.replace("伦创贷", "科创贷")
    corrected_text = corrected_text.replace("小微易笕", "小微易贷")

    for product in product_keywords:
        if product in corrected_text:
            return product

    # 兜底：尝试匹配以“贷”结尾的短语
    match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,12}贷)", corrected_text)
    if match:
        return match.group(1)

    return ""

def extract_loan_amount_max(text):
    patterns = [
        r"贷款额度最高可达(\d+\.?\d*)万元",
        r"额度最高可达(\d+\.?\d*)万元",
        r"授信额度.*?可达(\d+\.?\d*)万元",
        r"可达(\d+\.?\d*)万元",
        r"额度高至(\d+\.?\d*)万",
        r"最高可达(\d+\.?\d*)万元",
        r"最高(\d+\.?\d*)万元"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}万元"

    return ""

def extract_loan_term(text):
    patterns = [
        r"贷款期限[:：]?\s*最长(\d+)个月",
        r"期限[:：]?\s*最长(\d+)个月",
        r"最长(\d+)个月",
        r"贷款期限[:：]?\s*(\d+)个月",
        r"额度使用期[:：]?\s*(\d+)个月"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}个月"

    return ""

def extract_repayment_method(text):
    keywords = [
        "按月结息,到期一次性还本",
        "按月结息",
        "到期一次性还本",
        "随借随还",
        "先息后本",
        "等额本息",
        "一次性还本"
    ]

    found = []
    for kw in keywords:
        if kw in text:
            found.append(kw)

    # 去重后再处理包含关系
    found = list(dict.fromkeys(found))

    # 如果已经有“到期一次性还本”，就去掉更泛的“一次性还本”
    if "到期一次性还本" in found and "一次性还本" in found:
        found.remove("一次性还本")

    return "；".join(found)

def extract_guarantee_type(text):
    found = []

    # 优先匹配具体表达
    priority_keywords = [
        "免抵押",
        "免担保",
        "保证保险",
        "政府增信"
    ]

    for kw in priority_keywords:
        if kw in text:
            found.append(kw)

    # 仅当没有更具体词时，再补充泛化词
    if "抵押" in text and "免抵押" not in text:
        found.append("抵押")

    if "担保" in text and "免担保" not in text and "保证保险" not in text:
        found.append("担保")

    return "；".join(list(dict.fromkeys(found)))

def extract_product_features(text):
    keywords = [
        "线上操作",
        "在线申请",
        "秒批额度",
        "循环使用",
        "便捷高效",
        "一次授信",
        "多次支用",
        "额度可循环",
        "贷款利率低"
    ]

    found = []
    for kw in keywords:
        if kw in text:
            found.append(kw)

    return "；".join(list(dict.fromkeys(found)))

def extract_product_fields(ocr_text):
    cleaned_text = clean_ocr_text(ocr_text)

    result = {
        "bank_name": extract_bank_name(cleaned_text),
        "product_name": extract_product_name(cleaned_text),
        "loan_amount_max": extract_loan_amount_max(cleaned_text),
        "loan_term": extract_loan_term(cleaned_text),
        "repayment_method": extract_repayment_method(cleaned_text),
        "guarantee_type": extract_guarantee_type(cleaned_text),
        "product_features": extract_product_features(cleaned_text),
        "raw_text": cleaned_text
    }

    return result

# 中文映射函数
field_name_map = {
    "bank_name": "银行",
    "product_name": "产品名称",
    "interest_rate": "利率",
    "loan_amount_min": "最低额度",
    "loan_amount_max": "最高额度",
    "loan_term": "贷款期限",
    "repayment_method": "还款方式",
    "guarantee_type": "担保方式",
    "target_customer": "目标客群",
    "application_mode": "申请方式",
    "approval_speed": "审批时效",
    "remark": "备注"
}

extract_field_name_map = {
    "bank_name": "银行名称",
    "product_name": "产品名称",
    "loan_amount_max": "最高额度",
    "loan_term": "贷款期限",
    "repayment_method": "还款方式",
    "guarantee_type": "担保方式",
    "product_features": "产品特点"
}