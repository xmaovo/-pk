# 小微产品PK Demo

## 项目简介
基于 Streamlit 搭建的小微贷款产品对比原型，支持内置产品库展示、他行产品海报上传、OCR识别、字段抽取、人工修正与合并对比。

## 主要功能
- 内置产品库多选对比
- 海报图片上传
- OCR文字识别
- 规则抽取产品字段
- 人工修正后加入对比表
- 合并后产品表导出
- 横向PK对比表导出

## 技术路线
- Streamlit
- EasyOCR
- Rule-based NLP
- Pandas

## 运行方式
```bash
python -m streamlit run app.py
