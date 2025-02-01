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
    data = {sheet: xls.parse(sheet, header=2) for sheet in xls.sheet_names}  # Adjusted header row
    return data

# Load the data once at startup
data = load_data()

def get_treatment_data():
    df = data['RD_信頼区間_相関係数から_比']
    df = df[['アウトカムk', 'RDijkまたはMDijk 介入群の絶対リスク-対照群の絶対リスク=Eijk', '95%信頼区間下限値', '95%信頼区間上限値', 'Estimate']]
    df.columns = ['Outcome', 'Risk Difference', 'Lower CI', 'Upper CI', 'Net Benefit']
    df.dropna(subset=['Outcome'], inplace=True)
    
    # Convert numeric columns
    numeric_cols = ['Risk Difference', 'Lower CI', 'Upper CI', 'Net Benefit']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Normalize Net Benefit values
    max_benefit = df['Net Benefit'].max()
    min_benefit = df['Net Benefit'].min()
    if max_benefit != min_benefit:
        df['Normalized Net Benefit'] = (df['Net Benefit'] - min_benefit) / (max_benefit - min_benefit)
    else:
        df['Normalized Net Benefit'] = 1

    # Categorize Benefit Levels
    def classify_benefit(value):
        if value >= 0.07:
            return "高い利益 (High Benefit)"
        elif value >= 0.03:
            return "中程度の利益 (Moderate Benefit)"
        elif value >= 0.00:
            return "低い利益 (Low Benefit)"
        else:
            return "利益なし (No Benefit)"
    
    df['Benefit Category'] = df['Net Benefit'].apply(classify_benefit)
    return df

# App UI
st.title("脳卒中予防の意思決定ツール")
st.write("研究データに基づいた脳卒中予防治療の選択肢を理解しましょう。")

st.sidebar.header("患者情報入力")
age = st.sidebar.slider("年齢", 18, 100, 50)
conditions = st.sidebar.multiselect("既存の健康状態", ["高血圧", "糖尿病", "喫煙", "肥満"])
medications = st.sidebar.text_input("現在の服用薬")
risk_factors = st.sidebar.multiselect("その他のリスク要因", ["家族歴", "高コレステロール", "運動不足"])

# User input fields for modifying key treatment data
st.sidebar.subheader("カスタムデータ入力")
custom_risk_difference = st.sidebar.number_input("リスク差のカスタム値", value=0.0)
custom_lower_ci = st.sidebar.number_input("信頼区間下限のカスタム値", value=0.0)
custom_upper_ci = st.sidebar.number_input("信頼区間上限のカスタム値", value=0.0)
custom_net_benefit = st.sidebar.number_input("ネットベネフィットのカスタム値", value=0.0)

if st.sidebar.button("送信"):
    st.subheader("あなたのデータに基づく治療オプション")
    st.write("システムがリスクとベネフィットスコアを計算しています...")
    
    treatment_df = get_treatment_data()
    
    # Apply custom user inputs
    if not treatment_df.empty:
        treatment_df.at[0, 'Risk Difference'] = custom_risk_difference
        treatment_df.at[0, 'Lower CI'] = custom_lower_ci
        treatment_df.at[0, 'Upper CI'] = custom_upper_ci
        treatment_df.at[0, 'Net Benefit'] = custom_net_benefit
    
    st.write("### 治療の有効性")
    st.dataframe(treatment_df[['Outcome', 'Risk Difference', 'Lower CI', 'Upper CI', 'Benefit Category']])

    # Pie Chart Visualization
    st.subheader("治療の有効性（1000人あたり）")
    if not treatment_df.empty and treatment_df['Normalized Net Benefit'].sum() > 0:
        fig, ax = plt.subplots()
        ax.pie(treatment_df['Normalized Net Benefit'], labels=treatment_df['Outcome'], autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.write("データが不足しているため、円グラフを表示できません。")
    
    st.subheader("最終推奨事項")
    if not treatment_df.empty:
        best_treatment = treatment_df.sort_values(by='Net Benefit', ascending=False).iloc[0]
        st.write(f"計算結果に基づき、最も推奨される治療は **{best_treatment['Outcome']}** です。最終決定の前に医師に相談してください。")
    else:
        st.write("適切なデータがないため、推奨治療を計算できません。")
    
    st.button("最初からやり直す")
