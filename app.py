import streamlit as st

def profile_page():
    st.title("ユーザープロファイル")
    st.markdown("**年齢** と **性別** と **都道府県** を入力してください。")

    # Collect user profile information.
    age = st.number_input("年齢", min_value=0, max_value=120, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    
    # Example list of prefectures — expand or modify as needed.
    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県", 
        "山形県", "福島県", "茨城県", "栃木県", "群馬県",
        "埼玉県", "千葉県", "東京都", "神奈川県"
        # ... 以降追加 ...
    ]
    prefecture = st.selectbox("都道府県", prefectures)
    
    if st.button("次へ"):
        # Save the profile data and a flag to indicate profile completion.
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.prefecture = prefecture
        st.session_state.profile_complete = True  # Flag for profile completion

def main():
    # If the profile hasn't been completed, show the profile page.
    if not st.session_state.get("profile_complete", False):
        profile_page()
        return  # Stop execution until profile data is provided.

    # Display user profile information in the sidebar.
    st.sidebar.write(f"ユーザー情報:")
    st.sidebar.write(f"・年齢 = {st.session_state.age}")
    st.sidebar.write(f"・性別 = {st.session_state.gender}")
    st.sidebar.write(f"・都道府県 = {st.session_state.prefecture}")

    st.title("正味の益計算：効果推定値s & 効果推定値r + スター表示 + カラー解釈")
    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：2つの方式での正味の益を計算し、アウトカムごとに星、最終合計は色付きで表示）
        </p>
        <p>
        <strong>概要：</strong><br>
        - 各アウトカムで「リスク差(E)」と「重要度(i)」を入力。<br>
        - <em>効果推定値s</em>：合計重要度で割る（\\( i / \\sum i \\))<br>
        - <em>効果推定値r</em>：最重要アウトカムを100とした比（\\( i / 100 \\))<br>
        - 各アウトカムで2つの貢献度を計算し、それぞれ「net effect」を星表示（正⇒緑、負⇒赤、0⇒灰色ダッシュ）。<br>
        - 合計の正味の益は、プラスなら赤枠、0付近なら青枠、マイナスなら緑枠で表示。<br>
        </p>
        """,
        unsafe_allow_html=True
    )
    
    # Define outcomes for the calculation.
    # Define your 5 static outcomes
outcomes = [
    {"label": "脳卒中予防", "f": +1, "default_E": 0.10, "default_i": 100},
    {"label": "心不全予防", "f": +1, "default_E": -0.10, "default_i":  29},
    {"label": "めまい",     "f": -1, "default_E":  0.02, "default_i":   5},
    {"label": "頻尿",       "f": -1, "default_E": -0.01, "default_i":   4},
    {"label": "転倒",       "f": -1, "default_E": -0.02, "default_i":  13},
]

st.sidebar.header("① アウトカムの入力")

# calculate how many extra slots remain (max 7 total)
max_extra = 7 - len(outcomes)
extra_count = st.sidebar.number_input(
    f"追加アウトカム数 (0–{max_extra})",
    min_value=0, max_value=max_extra, value=0, step=1
)

# collect inputs for all static + custom outcomes
user_data = []

# 1) static outcomes
for item in outcomes:
    E_val = st.sidebar.number_input(
        f"{item['label']}：リスク差 (E)",
        value=float(item["default_E"]), step=0.01, format="%.3f",
        key=f"E_{item['label']}"
    )
    i_val = st.sidebar.slider(
        f"{item['label']}：重要度",
        0, 100, item["default_i"], step=1,
        key=f"i_{item['label']}"
    )
    user_data.append({
        "label": item["label"],
        "f": item["f"],
        "E": E_val,
        "i": i_val,
    })

# 2) custom outcomes, count = extra_count
for idx in range(extra_count):
    st.sidebar.markdown(f"**Custom Outcome {idx+1}**")
    label = st.sidebar.text_input(
        "Label", key=f"custom_label_{idx}"
    ) or f"Custom{idx+1}"
    type_choice = st.sidebar.selectbox(
        "Type", ["Benefit", "Side effect"], key=f"custom_type_{idx}"
    )
    f_val = +1 if type_choice=="Benefit" else -1

    E_val = st.sidebar.number_input(
        f"{label}：リスク差 (E)",
        value=0.0, step=0.01, format="%.3f",
        key=f"custom_E_{idx}"
    )
    i_val = st.sidebar.slider(
        f"{label}：重要度",
        0, 100, 50, step=1,
        key=f"custom_i_{idx}"
    )

    user_data.append({
        "label": label,
        "f": f_val,
        "E": E_val,
        "i": i_val,
    })

    
    st.sidebar.header("② 制約（Constraints）")
    constraint_options = ["問題なし", "やや問題", "重視する"]
    cost_label = st.sidebar.radio("費用面の問題", constraint_options, index=0)
    access_label = st.sidebar.radio("通院アクセスの問題", constraint_options, index=0)
    care_label = st.sidebar.radio("介助面の問題", constraint_options, index=0)
    
    cost_val = constraint_to_numeric(cost_label)
    access_val = constraint_to_numeric(access_label)
    care_val = constraint_to_numeric(care_label)
    
    if st.sidebar.button("正味の益を計算する"):
        show_results(user_data, cost_val, access_val, care_val)

def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")
    
    # --- 1) Compute net_s (Sheet2) & net_r (Sheet3) for each outcome.
    total_i = sum(d["i"] for d in user_data)
    if total_i == 0:
        st.error("重要度がすべて0のため計算できません。少なくとも1つは重要度を上げてください。")
        return
    
    net_sum_s = 0.0
    net_sum_r = 0.0
    
    st.markdown("### 各アウトカムの詳細 (効果推定値s & 効果推定値r)")
    for d in user_data:
        label = d["label"]
        E_val = d["E"]
        i_val = d["i"]
        f_val = d["f"]
        
        # Sheet2 calculation.
        w_s = i_val / total_i
        nb_s = E_val * w_s * f_val
        net_sum_s += nb_s
        star_s = star_html_5(nb_s)
        
        # Sheet3 calculation.
        w_r = i_val / 100.0
        nb_r = E_val * w_r * f_val
        net_sum_r += nb_r
        star_r = star_html_5(nb_r)
        
        st.markdown(
            f"- **{label}**: E={E_val:.3f}, i={i_val}<br>"
            f"&emsp;**効果推定値s**: {star_s} ( {nb_s:.4f} )  "
            f"&emsp;**効果推定値r**: {star_r} ( {nb_r:.4f} )",
            unsafe_allow_html=True
        )
    
    # --- 2) Final net sums.
    st.markdown("### 合計正味の益")
    s_1000 = int(round(net_sum_s * 1000, 0))
    r_1000 = int(round(net_sum_r * 1000, 0))
    
    if net_sum_s > 0:
        st.error(f"効果推定値s 全体として有害方向になる可能性があります（プラス）。\n"
                 f"Net=1000人あたり={s_1000}人")
    elif abs(net_sum_s) < 1e-9:
        st.info(f"効果推定値s 全体としてほぼ変化なし（ニュートラル）の可能性。\n"
                f"Net=1000人あたり={s_1000}人")
    else:
        st.success(f"効果推定値s 全体として有益方向になる可能性があります（マイナス）。\n"
                   f"Net=1000人あたり={s_1000}人")
    
    if net_sum_r > 0:
        st.error(f"効果推定値r 全体として有害方向になる可能性があります（プラス）。\n"
                 f"Net=1000人あたり={r_1000}人")
    elif abs(net_sum_r) < 1e-9:
        st.info(f"効果推定値r 全体としてほぼ変化なし（ニュートラル）の可能性。\n"
                f"Net=1000人あたり={r_1000}人")
    else:
        st.success(f"効果推定値r 全体として有益方向になる可能性があります（マイナス）。\n"
                   f"Net=1000人あたり={r_1000}人")
    
    # --- 3) Constraints の状況（最悪ケースのみ）
    st.subheader("制約（Constraints）の状況")
    max_sev = max(cost_val, access_val, care_val)

    if max_sev == 0.0:
        st.success("制約：すべて問題なし（緑）")
    elif max_sev == 0.5:
        st.warning("制約：懸念ありの項目があります（黄）")
    else:  # max_sev == 1.0
        st.error("制約：問題ありの項目があります（赤）")

    # それぞれのラベル表示はそのまま
    st.write(f"- 費用面: **{numeric_to_constraint_label(cost_val)}**")
    st.write(f"- アクセス面: **{numeric_to_constraint_label(access_val)}**")
    st.write(f"- 介助面: **{numeric_to_constraint_label(care_val)}**")

def constraint_to_numeric(label):
    """Convert constraint labels to numeric values."""
    if label == "問題なし":
        return 0.0
    elif label == "やや問題":
        return 0.5
    else:
        return 1.0

def numeric_to_constraint_label(value):
    """Convert numeric values back to constraint labels."""
    if value == 0.0:
        return "問題なし"
    elif value == 0.5:
        return "やや問題"
    else:
        return "重視する"

def star_html_5(net_effect):
    """
    Return HTML code for up to 5 stars based on the net effect.
      - Positive values produce green stars.
      - Negative values produce red stars.
      - Near zero returns a gray dash.
    """
    abs_val = abs(net_effect)
    
    if abs_val < 1e-9:
        return "<span style='color:gray;font-size:18px;'>—</span>"
    
    if abs_val < 0.01:
        star_count = 1
    elif abs_val < 0.03:
        star_count = 2
    elif abs_val < 0.06:
        star_count = 3
    elif abs_val < 0.10:
        star_count = 4
    else:
        star_count = 5
    
    star_color = "green" if net_effect > 0 else "red"
    result = ""
    for i in range(star_count):
        result += f"<span style='color:{star_color};font-size:18px;'>★</span>"
    for i in range(5 - star_count):
        result += "<span style='color:lightgray;font-size:18px;'>★</span>"
    return result

if __name__ == "__main__":
    main()
