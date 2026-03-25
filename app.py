import pandas as pd
import streamlit as st
import numpy as np
from PIL import Image
import easyocr
import re

from modules.data_utils import (
    parse_rate,
    parse_amount,
    parse_amount_text,
    format_amount_as_wanyuan,
    load_products,
    convert_extracted_to_product_record,
    build_combined_products_df,
    dataframe_to_csv_download,
    get_lowest_rate_product,
    get_highest_amount_product
)

from modules.ocr_utils import (
    format_file_size,
    load_ocr_model,
    run_ocr_on_image
)

from modules.extract_utils import (
    field_name_map,
    extract_field_name_map,
    extract_product_fields
)

from modules.compare_utils import (
    highlight_compare_table,
    highlight_combined_table,
    highlight_pk_table
)

# 1.页面基础设置
st.set_page_config(
    page_title="小微产品PK Demo",
    page_icon="📊",
    layout="wide"
)

st.title("小微产品PK Demo")

df_products = load_products("data/products.csv")

# 3. 数据预览
with st.expander("查看原始产品库数据"):
    st.dataframe(df_products, use_container_width=True)

# 4. 侧边栏筛选
st.sidebar.header("筛选条件")

bank_options = ["全部"] + sorted(df_products["bank_name"].dropna().unique().tolist())
selected_bank = st.sidebar.selectbox("选择银行", bank_options)

if selected_bank != "全部":
    df_filtered = df_products[df_products["bank_name"] == selected_bank].copy()
else:
    df_filtered = df_products.copy()

product_options = df_filtered["product_name"].tolist()
selected_products = st.sidebar.multiselect(
    "选择需要对比的产品",
    options=product_options,
    default=product_options[:2] if len(product_options) >= 2 else product_options
)

field_options = [
    "bank_name",
    "product_name",
    "interest_rate",
    "loan_amount_min",
    "loan_amount_max",
    "loan_term",
    "repayment_method",
    "guarantee_type",
    "target_customer",
    "application_mode",
    "approval_speed",
    "remark"
]

default_fields = [
    "bank_name",
    "product_name",
    "interest_rate",
    "loan_amount_max",
    "loan_term",
    "repayment_method",
    "application_mode",
    "approval_speed"
]

display_fields = st.sidebar.multiselect(
    "选择展示字段",
    options=field_options,
    default=default_fields,
    format_func=lambda x: field_name_map.get(x, x)
)

# 5. 选择结果
st.subheader("已选产品")

if not selected_products:
    st.warning("请先在左侧选择至少一个产品。")
    st.stop()

df_selected = df_filtered[df_filtered["product_name"].isin(selected_products)].copy()

df_selected_display = df_selected.copy()
df_selected_display["loan_amount_min"] = df_selected_display["loan_amount_min"].apply(format_amount_as_wanyuan)
df_selected_display["loan_amount_max"] = df_selected_display["loan_amount_max"].apply(format_amount_as_wanyuan)

df_selected_display = df_selected_display.rename(columns=field_name_map)
st.dataframe(df_selected_display, use_container_width=True)

# 6. 产品对比表
st.subheader("产品对比表")
st.caption("说明：绿色高亮表示利率最低，黄色高亮表示最高额度。")

if display_fields:
    compare_fields = display_fields.copy()
    if "product_name" not in compare_fields:
        compare_fields = ["product_name"] + compare_fields

    df_compare = df_selected[compare_fields].copy()

    if "loan_amount_min" in df_compare.columns:
        df_compare["loan_amount_min"] = df_compare["loan_amount_min"].apply(format_amount_as_wanyuan)

    if "loan_amount_max" in df_compare.columns:
        df_compare["loan_amount_max"] = df_compare["loan_amount_max"].apply(format_amount_as_wanyuan)

    df_compare = df_compare.rename(columns=field_name_map)

    df_compare_t = df_compare.set_index("产品名称").T

    styled_df = df_compare_t.style.apply(highlight_compare_table, axis=1)

    st.write(styled_df)
else:
    st.info("请至少选择一个展示字段。")

# 7. 简单指标展示
st.subheader("快速概览")

lowest_rate_row = df_selected.sort_values("interest_rate_num").iloc[0]
selected_count = len(df_selected)
max_amount = df_selected["loan_amount_max"].max()
lowest_rate_product = f'{lowest_rate_row["product_name"]}（{lowest_rate_row["interest_rate"]}）'

st.markdown("""
<style>
.metric-card {
    background-color: #ffffff;
    border: 1px solid #e6eaf1;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    min-height: 140px;
}

.metric-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #4a5568;
    margin-bottom: 18px;
    line-height: 1.4;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1f2937;
    line-height: 1.2;
    word-break: break-word;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">已选产品数</div>
        <div class="metric-value">{selected_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">最高额度产品数值（万元）</div>
        <div class="metric-value">{max_amount}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">最低利率产品</div>
        <div class="metric-value" style="font-size: 1.5rem;">{lowest_rate_product}</div>
    </div>
    """, unsafe_allow_html=True)

# 8. 图片上传
if "uploaded_product_records" not in st.session_state:
    st.session_state.uploaded_product_records = {}

st.markdown("---")
st.subheader("他行产品图片上传")

uploaded_files = st.file_uploader(
    "请上传他行产品海报或截图",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="可一次上传一张或多张图片，支持 PNG / JPG / JPEG 格式。"
)

if uploaded_files:
    st.success(f"已上传 {len(uploaded_files)} 张图片。")

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        st.markdown(f"### 图片 {idx}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(
                uploaded_file,
                caption=uploaded_file.name,
                use_container_width=True
            )

        with col2:
            st.markdown("**图片信息**")
            st.write(f"文件名：{uploaded_file.name}")
            st.write(f"文件类型：{uploaded_file.type}")
            st.write(f"文件大小：{format_file_size(uploaded_file.size)}")

        with st.expander(f"查看图片 {idx} 的 OCR 识别结果", expanded=True):
            try:
                with st.spinner("正在进行 OCR 识别，请稍候..."):
                    ocr_text, ocr_lines = run_ocr_on_image(uploaded_file)

                if ocr_text.strip():
                    st.markdown("**OCR 原始文本：**")
                    st.text_area(
                        label=f"ocr_text_{idx}",
                        value=ocr_text,
                        height=220,
                        label_visibility="collapsed"
                    )

                    st.markdown("**按行识别结果：**")
                    ocr_df = pd.DataFrame(ocr_lines)
                    ocr_df["score"] = ocr_df["score"].apply(lambda x: round(float(x), 4))
                    st.dataframe(ocr_df, use_container_width=True)

                    # ===== 新增：字段抽取 =====
                    st.markdown("**结构化字段抽取结果：**")
                    extracted_result = extract_product_fields(ocr_text)

                    # product_record = convert_extracted_to_product_record(extracted_result, idx=idx)
                    # uploaded_product_records.append(product_record)

                    extracted_display = {
                        extract_field_name_map[k]: v
                        for k, v in extracted_result.items()
                        if k in extract_field_name_map
                    }

                    extracted_df = pd.DataFrame(
                        list(extracted_display.items()),
                        columns=["字段", "识别结果"]
                    )

                    st.dataframe(extracted_df, use_container_width=True)
                    st.markdown("**人工修正后加入对比表：**")

                    with st.form(f"manual_edit_form_{idx}"):
                        corrected_bank_name = st.text_input("银行名称", value=extracted_result.get("bank_name", ""), key=f"bank_{idx}")
                        corrected_product_name = st.text_input("产品名称", value=extracted_result.get("product_name", ""), key=f"product_{idx}")
                        corrected_interest_rate = st.text_input("利率", value="", key=f"rate_{idx}")
                        corrected_loan_amount_max = st.text_input("最高额度", value=extracted_result.get("loan_amount_max", ""), key=f"amount_{idx}")
                        corrected_loan_term = st.text_input("贷款期限", value=extracted_result.get("loan_term", ""), key=f"term_{idx}")
                        corrected_repayment_method = st.text_input("还款方式", value=extracted_result.get("repayment_method", ""), key=f"repayment_{idx}")
                        corrected_guarantee_type = st.text_input("担保方式", value=extracted_result.get("guarantee_type", ""), key=f"guarantee_{idx}")
                        corrected_remark = st.text_area("备注/产品特点", value=extracted_result.get("product_features", ""), key=f"remark_{idx}")

                        submit_btn = st.form_submit_button("应用修正并加入对比表")

                    if submit_btn:
                        corrected_result = {
                            "bank_name": corrected_bank_name,
                            "product_name": corrected_product_name,
                            "loan_amount_max": corrected_loan_amount_max,
                            "loan_term": corrected_loan_term,
                            "repayment_method": corrected_repayment_method,
                            "guarantee_type": corrected_guarantee_type,
                            "product_features": corrected_remark
                        }

                        product_record = convert_extracted_to_product_record(corrected_result, idx=idx)
                        product_record["interest_rate"] = corrected_interest_rate
                        product_record["data_source"] = "海报OCR识别(人工修正)"

                        st.session_state.uploaded_product_records[idx] = product_record
                        st.success("已应用修正并加入对比表。")

                else:
                    st.warning("未识别出明显文字内容，请尝试更清晰的图片。")

            except Exception as e:
                st.error(f"OCR 识别失败：{e}")

        st.markdown("---")
else:
    st.info("你还没有上传图片。可拖拽图片到上传框中，或点击后选择本地文件。")

# 9.合并后产品对比表
col_a, col_b = st.columns([1, 5])

with col_a:
    if st.button("清空OCR产品"):
        st.session_state.uploaded_product_records = {}
        st.success("已清空 OCR 加入的产品。")

st.subheader("合并后产品对比表")
st.caption("包含已选内置产品 + 上传海报识别出的他行产品")

uploaded_records_list = list(st.session_state.uploaded_product_records.values())

# 先把 OCR 产品单独转成 DataFrame
if uploaded_records_list:
    df_uploaded_only = pd.DataFrame(uploaded_records_list)
else:
    df_uploaded_only = pd.DataFrame()

# 这里只让用户选择 OCR 产品
if not df_uploaded_only.empty and "product_name" in df_uploaded_only.columns:
    ocr_product_options = sorted(
        [x for x in df_uploaded_only["product_name"].dropna().unique().tolist() if str(x).strip() != ""]
    )

    selected_ocr_products = st.multiselect(
        "选择需要加入对比的 OCR 产品",
        options=ocr_product_options,
        default=ocr_product_options,
        key="ocr_product_filter_v1"
    )

    if selected_ocr_products:
        df_uploaded_only = df_uploaded_only[df_uploaded_only["product_name"].isin(selected_ocr_products)].copy()
    else:
        df_uploaded_only = df_uploaded_only.iloc[0:0].copy()
else:
    st.info("当前还没有可加入对比的 OCR 产品。")
    df_uploaded_only = pd.DataFrame()

df_combined = build_combined_products_df(df_selected, df_uploaded_only.to_dict("records") if not df_uploaded_only.empty else [])

if not df_combined.empty:
    combined_display_fields = [
        "data_source",
        "bank_name",
        "product_name",
        "interest_rate",
        "loan_amount_max",
        "loan_term",
        "repayment_method",
        "guarantee_type",
        "remark"
    ]

    valid_fields = [col for col in combined_display_fields if col in df_combined.columns]
    df_combined_display = df_combined[valid_fields].copy()

    if "loan_amount_max" in df_combined_display.columns:
        df_combined_display["loan_amount_max"] = df_combined_display["loan_amount_max"].apply(format_amount_as_wanyuan)

    combined_field_name_map = {
        "data_source": "数据来源",
        "bank_name": "银行",
        "product_name": "产品名称",
        "interest_rate": "利率",
        "loan_amount_max": "最高额度",
        "loan_term": "贷款期限",
        "repayment_method": "还款方式",
        "guarantee_type": "担保方式",
        "remark": "备注/产品特点"
    }

    df_combined_display = df_combined_display.rename(columns=combined_field_name_map)

    df_combined_t = df_combined_display.set_index("产品名称").T

    st.markdown("**导出结果：**")
    col_download1, col_download2 = st.columns(2)

    with col_download1:
        st.download_button(
            label="下载合并后产品表（CSV）",
            data=dataframe_to_csv_download(df_combined_display),
            file_name="合并后产品表.csv",
            mime="text/csv"
        )

    with col_download2:
        st.download_button(
            label="下载横向PK对比表（CSV）",
            data=dataframe_to_csv_download(
                df_combined_t.reset_index().rename(columns={"index": "字段"})
            ),
            file_name="横向PK对比表.csv",
            mime="text/csv"
        )

    styled_combined_df = df_combined_display.style.apply(highlight_combined_table, axis=1)
    st.write(styled_combined_df)

    st.markdown("**横向 PK 对比视图：**")
    styled_pk_df = df_combined_t.style.apply(highlight_pk_table, axis=1)
    st.write(styled_pk_df)
else:
    st.info("当前没有可展示的合并产品数据。")

st.markdown("### 快速概览")

combined_product_count = len(df_combined)
combined_bank_count = df_combined["bank_name"].replace("", pd.NA).dropna().nunique()

lowest_rate_product, lowest_rate_value = get_lowest_rate_product(df_combined)
highest_amount_product, highest_amount_value = get_highest_amount_product(df_combined)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">当前对比产品数</div>
        <div class="metric-value">{combined_product_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">参与对比银行数</div>
        <div class="metric-value">{combined_bank_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    highest_amount_display = (
        f"{highest_amount_product}（{highest_amount_value}）"
        if highest_amount_product else "暂无"
    )
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">最高额度产品</div>
        <div class="metric-value" style="font-size: 1.5rem;">{highest_amount_display}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    lowest_rate_display = (
        f"{lowest_rate_product}（{lowest_rate_value}）"
        if lowest_rate_product else "暂无"
    )
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">最低利率产品</div>
        <div class="metric-value" style="font-size: 1.5rem;">{lowest_rate_display}</div>
    </div>
    """, unsafe_allow_html=True)