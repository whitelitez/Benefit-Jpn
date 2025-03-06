import streamlit as st

def main():
    st.title("正味の益計算：Sheet2 & Sheet3 両方式（シンプル版）")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：簡易実装例）
        </p>
        <p>
        このアプリは下記を行います：<br>
        1. 各アウトカムについて、リスク差(E)を数値入力（小数OK）し、重要度(i)をスライダーで入力。<br>
        2. 効果推定値s (Sheet2)の式：\\( E \\times \\frac{i}{\\sum i} \\times f \\) と、
           効果推定値r (Sheet3)の式：\\( E \\times \\frac{i}{100} \\times f \\) を両方計算。<br>
        3. 各アウトカムの重要度を3段階の星(★)で表示し、リスク差\\(\\times f\\) の方向を矢印(⬆,⬇,➡)で表示。<br>
        4. 最後に「正味の益」の合計値を2種類それぞれ算出し、1000人あたりの人数として表示します。<br>
        </p>
        """,
        unsafe_allow_html=True
    )

    # Define outcomes: label, direction factor f, default risk diff, default importance
    outcomes = [
        {
            "label": "脳卒中予防",
            "f": +1,
            "default_E": 0.10,
            "default_i": 100,
        },
        {
            "label": "心不全予防",
            "f": +1,
            "default_E": -0.10,
            "default_i": 29,
        },
        {
            "label": "めまい",
            "f": -1,
            "default_E": 0.02,
            "default_i": 5,
        },
        {
            "label": "頻尿",
            "f": -1,
            "default_E": 0.04,
            "default_i": 4,
        },
        {
            "label": "転倒",
            "f": -1,
            "default_E": 0.06,
            "default_i": 13,
        },
    ]

    st.sidebar.header("① 各アウトカムの入力")

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
        # Slider for importance
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

    # Button
    if st.sidebar.button("正味の益を計算する"):
        show_results(user_data, cost_val, access_val, care_val)


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) Calculate sum of importance
    total_importance = sum(d["i"] for d in user_data)
    if total_importance == 0:
        st.error("重要度がすべて0のため計算できません。少なくとも1つは重要度を大きくしてください。")
        return

    # 2) We'll accumulate net sums for both methods
    net_sum_s = 0.0  # Sheet2
    net_sum_r = 0.0  # Sheet3

    st.markdown("### 各アウトカムの詳細")
    for d in user_data:
        label = d["label"]
        E_val = d["E"]
        i_val = d["i"]
        f_val = d["f"]

        # Importance star rating (just reusing original logic)
        stars = star_html_3(i_val)

        # Arrows for the sign of (E*f) — same for s/r, since E is the same
        arrow = get_arrow(E_val * f_val)

        # Net effect for Sheet2
        w_s = (i_val / total_importance) if total_importance != 0 else 0
        nb_s = E_val * w_s * f_val
        net_sum_s += nb_s

        # Net effect for Sheet3
        w_r = (i_val / 100.0)
        nb_r = E_val * w_r * f_val
        net_sum_r += nb_r

        st.markdown(
            f"- **{label}**: {stars} (重要度={i_val}), リスク差={E_val:.3f} → {arrow} "
            f"<br>&emsp; [Sheet2 貢献度: {nb_s:.4f}] "
            f"&emsp; [Sheet3 貢献度: {nb_r:.4f}]",
            unsafe_allow_html=True
        )

    # 3) Convert net sums to per 1000
    score_s = round(net_sum_s * 1000, 1)
    score_r = round(net_sum_r * 1000, 1)

    # 4) Interpretation
    interpret_s = interpret_net_benefit(net_sum_s)
    interpret_r = interpret_net_benefit(net_sum_r)

    st.markdown("### 正味の益：合計")
    st.markdown(
        f"- **Sheet2 (効果推定値s)**：Net = {net_sum_s:.4f} → 1000人あたり {score_s}人, {interpret_s}"
    )
    st.markdown(
        f"- **Sheet3 (効果推定値r)**：Net = {net_sum_r:.4f} → 1000人あたり {score_r}人, {interpret_r}"
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


# --------------------------
# Helper functions
# --------------------------

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

def get_arrow(value):
    """
    Original arrow function for sign:
      >0.05 = up, < -0.05 = down, else right
    """
    if value > 0.05:
        return "⬆️"
    elif value < -0.05:
        return "⬇️"
    else:
        return "➡️"

def star_html_3(importance_0to100):
    """
    Original star function (importance-based):
      0..33 => 1 star
      34..66 => 2 stars
      67..100 => 3 stars
      If importance=0 => show no star or dash
    """
    if importance_0to100 == 0:
        return "<span style='color:lightgray;'>—</span>"

    if importance_0to100 <= 33:
        filled = 1
    elif importance_0to100 <= 66:
        filled = 2
    else:
        filled = 3

    stars = ""
    for i in range(3):
        if i < filled:
            stars += "<span style='color:gold;font-size:18px;'>★</span>"
        else:
            stars += "<span style='color:lightgray;font-size:18px;'>★</span>"
    return stars

def interpret_net_benefit(value):
    """
    Original logic:
      >0 => 有害方向
      ~0 => ニュートラル
      <0 => 有益方向
    """
    if value > 0:
        return "有害方向 (プラス)"
    elif abs(value) < 1e-9:
        return "ほぼ変化なし (ニュートラル)"
    else:
        return "有益方向 (マイナス)"


if __name__ == "__main__":
    main()
