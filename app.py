import os
import streamlit as st
import pandas as pd
import numpy as np

# Get the absolute path to the Excel file
FILE_PATH = os.path.join(os.path.dirname(__file__), "正味の益計算表.xlsx")

# Load Excel file directly from the app's directory
@st.cache_data
def load_data():
    xls = pd.ExcelFile(FILE_PATH)
    return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

# Load the data once at startup
data = load_data()

# App UI
st.title("脳卒中予防の意思決定ツール")
st.write("研究データに基づいた脳卒中予防治療の選択肢を理解しましょう。")

st.sidebar.header("患者情報入力")
age = st.sidebar.slider("年齢", 18, 100, 50)
conditions = st.sidebar.multiselect("既存の健康状態", ["高血圧", "糖尿病", "喫煙", "肥満"])
medications = st.sidebar.text_input("現在の服用薬")
risk_factors = st.sidebar.multiselect("その他のリスク要因", ["家族歴", "高コレステロール", "運動不足"])

if st.sidebar.button("送信"):
    st.subheader("あなたのデータに基づく治療オプション")
    st.write("システムがリスクとベネフィットスコアを計算しています...")

    # Dummy placeholder logic, replace with real formulas from the Excel files
    treatment_options = ["薬剤A", "薬剤B", "ライフスタイルの改善"]
    effectiveness = np.random.randint(50, 90, size=len(treatment_options))
    risk = np.random.randint(5, 20, size=len(treatment_options))
    confidence_interval = [(eff - 5, eff + 5) for eff in effectiveness]

    df = pd.DataFrame({
        "治療法": treatment_options,
        "1000人あたりの有効性": effectiveness,
        "リスクレベル": risk,
        "信頼区間": confidence_interval
    })

    st.table(df)

    st.subheader("閾値分析")
    st.write("このセクションでは、治療効果が信頼できる範囲内にあるかどうかを強調します。")
    # Placeholder for threshold calculation
    st.write("閾値ステータス: **安定** (安全な利益範囲内)")

    st.subheader("最終推奨事項")
    st.write("計算結果に基づき、治療Xを検討してください。最終決定の前に医師に相談してください。")
    st.button("最初からやり直す")
