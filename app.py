import streamlit as st

def main():
    st.title("正味の益計算：Sheet2 & Sheet3 両方式")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：アローなし・人は整数表示・正負で星色を変える）
        </p>
        <p>
        このアプリは下記を行います：
        <ul>
          <li>各アウトカムでリスク差(E)を数値入力、重要度(i)をスライダー(0～100)で入力</li>
          <li>効果推定値s (Sheet2)と効果推定値r (Sheet3)を計算し、正味の益を2種類出す</li>
          <li>星マーク(最大3)で、正か負かによって色を変えて表示（正⇒緑、負⇒赤、ほぼ0⇒灰色ダッシュ）</li>
          <li>1000人あたりの結果は整数で表示 (小数点なし)</li>
        </ul>
        </p>
        """,
        unsafe_allow_html=True
    )

    # Define outcomes
    outcomes = [
        {"label": "脳卒中予防", "f": +1, "default_E":  0.10, "default_i": 100},
        {"label": "心不全予防", "f": +1, "default_E": -0.10, "default_i":  29},
        {"label": "めまい",   "f": -1, "default_E":  0.02, "default_i":   5},
        {"label": "頻尿",     "f": -1, "default_E":  -0.01, "default_i":   4},
        {"label": "転倒",     "f": -1, "default_E":  -0.02, "default_i":  13},
    ]

    st.sidebar.header("① アウトカムの入力")

    user_data = []
    for item in outcomes:
        st.sidebar.subheader(item["label"])

        # Numeric input for E
        E_val = st.sidebar.number_input(
            f"{item['label']}：リスク差 E",
            value=float(item["default_E"]),
            step=0.01,
            format="%.3f"
        )
        # Slider for importance i
        i_val = st.sidebar.slider(
            f"{item['label']}：重要度 (0=重要でない, 100=非常に重要)",
            min_value=0,
            max_value=100,
            value=item["default_i"],
            step=1
        )

        user_data.append({
            "label": item["label"],
            "f":     item["f"],
            "E":     E_val,
            "i":     i_val,
        })

    # Constraints
    st.sidebar.header("② 制約（Constraints）")
    constraint_options = ["問題なし", "やや問題", "大きな問題"]
    cost_label = st.sidebar.radio("費用面の問題", constraint_options, index=0)
    access_label = st.sidebar.radio("通院アクセスの問題", constraint_options, index=0)
    care_label = st.sidebar.radio("介助面の問題", constraint_options, index=0)

    cost_val = constraint_to_numeric(cost_label)
    access_val = constraint_to_numeric(access_label)
    care_val = constraint_to_numeric(care_label)

    # Button to compute
    if st.sidebar.button("正味の益を計算する"):
        show_results(user_data, cost_val, access_val, care_val)


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) sum of importance for Sheet2
    total_i = sum(d["i"] for d in user_data)
    if abs(total_i) < 1e-9:
        st.error("重要度がすべて0のため計算できません。少なくとも1つは重要度を上げてください。")
        return

    # 2) We'll calculate net sums for both Sheet2 & Sheet3
    net_sum_s = 0.0
    net_sum_r = 0.0

    # Show outcome-level details
    st.markdown("### 各アウトカムの詳細")
    for d in user_data:
        label = d["label"]
        f_val = d["f"]
        E_val = d["E"]
        i_val = d["i"]

        # Sheet2: net effect
        w_s = i_val / total_i if total_i != 0 else 0
        nb_s = E_val * w_s * f_val
        net_sum_s += nb_s
        star_s = star_html_3_net(nb_s)

        # Sheet3: net effect
        w_r = i_val / 100.0
        nb_r = E_val * w_r * f_val
        net_sum_r += nb_r
        star_r = star_html_3_net(nb_r)

        st.markdown(
            f"- **{label}**：E={E_val:.3f}, 重要度={i_val} "
            f"<br>&emsp;効果推定値s: {star_s} ( {nb_s:.4f} ) "
            f"&emsp;効果推定値r: {star_r} ( {nb_r:.4f} )",
            unsafe_allow_html=True
        )

    # 3) Convert net sums to per 1000
    score_s = int(round(net_sum_s * 1000, 0))  # integer
    score_r = int(round(net_sum_r * 1000, 0))  # integer

    # 4) Interpret sign
    interpret_s = interpret_net_benefit(net_sum_s)
    interpret_r = interpret_net_benefit(net_sum_r)

    st.markdown("### 合計正味の益")
    st.markdown(
        f"- **効果推定値s**：Net = 1000人あたり {score_s}人, {interpret_s}"
    )
    st.markdown(
        f"- **効果推定値r**：Net = 1000人あたり {score_r}人, {interpret_r}"
    )

    # Constraints
    st.subheader("制約（Constraints）の状況")
    constraint_total = cost_val + access_val + care_val
    if constraint_total == 0:
        st.success("大きな制約は見当たりません。導入しやすい状況です。")
    elif constraint_total <= 1:
        st.info("多少の制約はありますが、比較的対応できそうです。")
    elif constraint_total <= 2:
        st.warning("複数の制約が見られます。追加のサポートや対策を検討してください。")
    else:
        st.error("費用・通院アクセス・介助面など、大きな問題がある可能性があります。慎重な検討が必要です。")

    st.write(f"- 費用面：**{numeric_to_constraint_label(cost_val)}**")
    st.write(f"- アクセス面：**{numeric_to_constraint_label(access_val)}**")
    st.write(f"- 介助面：**{numeric_to_constraint_label(care_val)}**")


# ---------------------
# Helper Functions
# ---------------------

def constraint_to_numeric(label):
    """制約レベルを数値に変換"""
    if label == "問題なし":
        return 0.0
    elif label == "やや問題":
        return 0.5
    else:
        return 1.0

def numeric_to_constraint_label(value):
    """数値を制約レベルに戻す"""
    if value == 0.0:
        return "問題なし"
    elif value == 0.5:
        return "やや問題"
    else:
        return "大きな問題"

def interpret_net_benefit(value):
    """
    Positive => 有害方向
    Negative => 有益方向
    ~0 => ニュートラル
    """
    if value > 0:
        return "有害方向 (プラス)"
    elif abs(value) < 1e-9:
        return "ほぼ変化なし (ニュートラル)"
    else:
        return "有益方向 (マイナス)"

def star_html_3_net(net_effect):
    """
    Show up to 3 stars based on absolute magnitude of net_effect.
    - If net_effect > 0 => green stars
    - If net_effect < 0 => red stars
    - If ~0 => gray dash
    Thresholds (example):
      < 0.01 => 1 star
      < 0.03 => 2 stars
      else   => 3 stars
    """
    val = abs(net_effect)
    if val < 1e-9:
        # basically zero
        return "<span style='color:gray;font-size:18px;'>—</span>"

    if val < 0.01:
        star_count = 1
    elif val < 0.03:
        star_count = 2
    else:
        star_count = 3

    # Color
    star_color = "green" if net_effect > 0 else "red"

    stars = ""
    for i in range(star_count):
        stars += f"<span style='color:{star_color};font-size:18px;'>★</span>"
    # Fill up to 3 with lightgray
    for i in range(3 - star_count):
        stars += "<span style='color:lightgray;font-size:18px;'>★</span>"

    return stars


if __name__ == "__main__":
    main()
