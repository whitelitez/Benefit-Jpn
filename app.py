import streamlit as st

def main():
    st.title("高血圧治療 オプション評価ツール (カラー星バージョン)")
    st.markdown("""
    重要度を3つの星で表しますが、星は同じ形 (★) を使い、
    色によって「埋まっている (金色)」「埋まっていない (灰色)」を区別します。
    """)

    # ------------------------------------------
    # 1) Dictionaries for user-friendly vs numeric
    # ------------------------------------------
    importance_map = {"重要": 1.0, "やや重要": 0.5, "重要でない": 0.0}
    sign_map = {"良い": +1, "悪い": -1}
    constraint_map = {
        "特に問題ない": 0.0,
        "少し問題がある": 0.5,
        "大きな問題": 1.0
    }

    # ------------------------------------------
    # 2) Five outcomes
    # ------------------------------------------
    outcome_defs = [
        {"label": "脳卒中予防", "default_slider": 50, "default_sign": "良い"},
        {"label": "心不全予防", "default_slider": 50, "default_sign": "良い"},
        {"label": "めまい", "default_slider": 50, "default_sign": "悪い"},
        {"label": "頻尿", "default_slider": 50, "default_sign": "悪い"},
        {"label": "転倒", "default_slider": 50, "default_sign": "悪い"},
    ]

    # ------------------------------------------
    # 3) Main Section: Outcomes
    # ------------------------------------------
    st.header("① 高血圧に対する内服薬のアウトカム")
    user_data = []
    for od in outcome_defs:
        st.write(f"### {od['label']} ({'益' if od['default_sign'] == '良い' else '害'})")

        # Slider for magnitude of change
        val = st.slider(
            f"{od['label']} の変化の大きさ (0=良くなる〜100=悪くなる目安)",
            min_value=0, max_value=100,
            value=od["default_slider"], step=1
        )
        rd_value = slider_to_rd(val)  # Convert 0..100 => -0.2..+0.2

        # Importance selection
        chosen_imp_label = st.radio(
            f"{od['label']} の重要度は？",
            list(importance_map.keys()),
            index=0
        )
        imp_value = importance_map[chosen_imp_label]

        # Store user data
        user_data.append({
            "outcome": od["label"],
            "rd": rd_value,
            "sign": sign_map[od["default_sign"]],
            "importance": imp_value,
        })

    # ------------------------------------------
    # 4) Sidebar: Constraints (UNCHANGED)
    # ------------------------------------------
    st.sidebar.header("② 追加の制約を考慮")
    st.sidebar.write("費用面・アクセス面・介助面などの問題度を選んでください。")

    financial_label = st.sidebar.radio(
        "費用面の制約",
        list(constraint_map.keys()),
        index=0
    )
    financial_val = constraint_map[financial_label]

    access_label = st.sidebar.radio(
        "アクセス面の制約（通院など）",
        list(constraint_map.keys()),
        index=0
    )
    access_val = constraint_map[access_label]

    care_label = st.sidebar.radio(
        "介助面の制約（自宅での世話など）",
        list(constraint_map.keys()),
        index=0
    )
    care_val = constraint_map[care_label]

    # ------------------------------------------
    # Button (UNCHANGED)
    # ------------------------------------------
    if st.button("結果を見る"):
        show_results(user_data, financial_val, access_val, care_val)

# ------------------------------------------
# Rest of the code (UNCHANGED)
# ------------------------------------------
def show_results(user_data, financial_val, access_val, care_val):
    net_effect = sum(row["rd"] * row["sign"] * row["importance"] for row in user_data)

    st.subheader("A) 治療アウトカムに関するコメント")
    if net_effect > 0.05:
        st.error("全体として、やや悪化する可能性が高いかもしれません。")
    elif net_effect > 0:
        st.warning("どちらかと言うと悪い方向ですが、大きくはないかもしれません。")
    elif abs(net_effect) < 1e-9:
        st.info("良い影響と悪い影響が釣り合っているか、ほぼ変化がないかもしれません。")
    else:
        # net_effect < 0
        if net_effect < -0.05:
            st.success("全体的に改善が期待できるかもしれません。")
        else:
            st.info("多少の改善があるかもしれませんが、大きくはないでしょう。")

    st.markdown("### 各項目の様子")
    for row in user_data:
        arrow = get_arrow(row["rd"])
        stars_html = star_html_3(row["importance"])  # HTML-based star approach
        sign_text = "良い" if row["sign"] == +1 else "悪い"

        # Note: we use st.markdown(..., unsafe_allow_html=True) to show color stars
        st.markdown(
            f"- **{row['outcome']}**：{stars_html} {arrow} ({sign_text})",
            unsafe_allow_html=True
        )

    # Constraints
    st.subheader("B) 制約に関するコメント")
    constraint_total = financial_val + access_val + care_val
    if constraint_total <= 0.0:
        st.success("特に大きな問題はなさそうです。治療を進めやすい状況と言えます。")
    elif constraint_total <= 1.0:
        st.info("多少気になる点がありますが、比較的対処しやすい可能性があります。")
    elif constraint_total <= 2.0:
        st.warning("いくつかの面で大きな負担が想定されます。対策が必要でしょう。")
    else:
        st.error("費用や通院・介助など、非常に大きな制約があるようです。慎重な検討が必要です。")

    st.markdown("### 制約の内訳")
    st.write(f"- 費用面: {value_to_label(financial_val)}")
    st.write(f"- アクセス面: {value_to_label(access_val)}")
    st.write(f"- 介助面: {value_to_label(care_val)}")

# ---------------- HELPER FUNCTIONS (UNCHANGED) ----------------

def slider_to_rd(val):
    """
    Convert a 0..100 slider to -0.2..+0.2 range
    so that 50 => 0.0, 0 => -0.2, 100 => +0.2
    """
    normalized = (val - 50) / 50.0  # -1..+1
    return 0.2 * normalized        # -0.2..+0.2

def get_arrow(rd):
    """Return arrow emoji based on RD threshold."""
    if rd > 0.05:
        return "↑"
    elif rd < -0.05:
        return "↓"
    else:
        return "→"

def value_to_label(val):
    """ Convert 0.0/0.5/1.0 -> textual label for constraints """
    if val == 0.0:
        return "特に問題ない"
    elif val == 0.5:
        return "少し問題がある"
    else:
        return "大きな問題"

def star_html_3(importance):
    """
    Return an HTML string with 3 stars in a row:
      - Gold (color:gold) for 'filled'
      - LightGray (color:lightgray) for 'empty'
    High (1.0): 3 gold
    Medium (0.5): 2 gold, 1 gray
    Low (0.0): 1 gold, 2 gray
    """
    # Decide how many "filled" stars to show
    if importance == 1.0:
        filled = 3
    elif importance == 0.5:
        filled = 2
    else:
        filled = 1  # or 0 if you want no gold for low

    total = 3
    stars_html = ""
    for i in range(total):
        if i < filled:
            # Filled star
            stars_html += "<span style='color:gold;font-size:18px;'>★</span>"
        else:
            # Hollow star (same shape but gray color)
            stars_html += "<span style='color:lightgray;font-size:18px;'>★</span>"

    return stars_html

if __name__ == "__main__":
    main()
