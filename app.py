import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Get the absolute path to the Excel file
FILE_PATH = os.path.join(os.path.dirname(__file__), "net_benefit_rd_md_v0.97.xlsx")

# Load Excel file directly from the app's directory
@st.cache_data
def load_data():
    xls = pd.ExcelFile(FILE_PATH)
    data = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    return data

# Load the data once at startup
data = load_data()

def get_treatment_data():
    df = data['RD_信頼区間_相関係数から_比']
    df = df.iloc[3:, [2, 5, 6, 7, 8, 9, 37, 38, 39, 40]]  # Extract relevant columns
    df.columns = ['Outcome', 'Risk Difference', 'Lower CI', 'Upper CI', 'Relative Importance', 'Standardized Importance', 'Threshold Low', 'Threshold High', 'Estimate', 'Net Benefit']
    df.dropna(inplace=True)
    return df

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
    
    treatment_df = get_treatment_data()
    
    st.write("### 治療の有効性")
    st.dataframe(treatment_df[['Outcome', 'Risk Difference', 'Lower CI', 'Upper CI', 'Net Benefit']])

    # Pie Chart Visualization of Treatment Effectiveness
    st.subheader("治療の有効性（1000人あたり）")
    fig, ax = plt.subplots()
    ax.pie(treatment_df['Net Benefit'], labels=treatment_df['Outcome'], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig)
    
    st.subheader("閾値分析")
    st.write("このセクションでは、治療効果が信頼できる範囲内にあるかどうかを強調します。")
    st.dataframe(treatment_df[['Outcome', 'Threshold Low', 'Threshold High']])

    st.subheader("最終推奨事項")
    best_treatment = treatment_df.sort_values(by='Net Benefit', ascending=False).iloc[0]
    st.write(f"計算結果に基づき、最も推奨される治療は **{best_treatment['Outcome']}** です。最終決定の前に医師に相談してください。")
    st.button("最初からやり直す")
