import streamlit as st

def main():
    st.title("正味の益計算：複数手法対応（Sheet2 & Sheet3）")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：技術的表記は最小限に省略）
        </p>
        <p>
        <strong>概要：</strong><br>
        - 各アウトカムに対して、
          <em>① 効果推定値s (Sheet2用)</em> と 
          <em>② 効果推定値r (Sheet3用)</em> を小数で入力します。<br>
        - 重要度は従来通り 0～100 のスライダーで入力。<br>
        - 最後に、2つの異なる重みづけ方式で「正味の益」を計算・表示します。<br>
        &emsp;1) <strong>Sheet2</strong>：合計重要度で正規化<br>
        &emsp;2) <strong>Sheet3</strong>：最大アウトカムを100として相対化（= importance/100）
        </p>
        """,
        unsafe_allow_html=True
    )

    # Define each outcome's name, sign factor, default values, etc.
    outcomes = [
        {
            "label": "脳卒中予防",
            "f": +1,
            # default values for E_s and E_r
            "default_s": 0.10,
            "default_r": 0.10,
            "default_i": 100,
        },
        {
            "label": "心不全予防",
            "f": +1,
            "default_s": -0.10,
            "default_r": -0.10,
            "default_i": 29,
        },
        {
            "label": "めまい",
            "f": -1,
            "default_s": 0.02,
            "default_r": 0.02,
            "default_i": 5,
        },
        {
            "label": "頻尿",
            "f": -1,
            "default_s": -0.01,
            "default_r": -0.01,
            "default_i": 4,
        },
        {
            "label": "転倒",
            "f": -1,
            "default_s": -0.02,
            "default_r": -0.02,
            "default_i": 13,
        },
    ]

    # Sidebar input
    st.sidebar.header("① アウトカムごとの入力")

    user_data = []
    for item in outcomes:
        st.sidebar.subheader(item["label"])

        # 1) number_input for 効果推定値s
        E_s = st.sidebar.number_input(
            f"{item['label']}：効果推定値s",
            value=float(item["default_s"]),
            step=0.01,
            format="%.3f"
        )

        # 2) number_input for 効果推定値r
        E_r = st.sidebar.number_input(
            f"{item['label']}：効果推定値r",
            value=float(item["default_r"]),
            step=0.01,
            format="%.3f"
        )

        # 3) slider for importance 0..100
        i_val = st.sidebar.slider(
            f"{item['label']}：重要度（0=重要ではない, 100=非常に重要）",
            min_value=0,
            max_value=100,
            value=item["default_i"],
            step=1
        )

        user_data.append({
            "label": item["label"],
            "f":     item["f"],
            "E_s":   E_s,
            "E_r":   E_r,
            "i":     i_val
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
        # Compute & display both results
        show_results(user_data, cost_val, access_val, care_val)


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) Sum-based weighting (Sheet2)
    net_s, details_s = compute_sheet2(user_data)

    # 2) Ratio-to-100 weighting (Sheet3)
    net_r, details_r = compute_sheet3(user_data)

    # Display table of outcomes
    st.markdown("### 各アウトカムの詳細比較")
    st.write("""
    - 「Sheet2の貢献度」は合計重要度で正規化 (\\(w_k = i_k / \\sum i\\)).
    - 「Sheet3の貢献度」は最重要(100)を基準とする (\\(w_k = i_k / 100\\)).
    """)

    st.write("| アウトカム | E_s | E_r | 重要度 | Sheet2貢献度(★) | Sheet3貢献度(★) |")
    st.write("|---|---:|---:|---:|---:|---:|")

    # For star rating, we show the net effect for each method
    for row_s, row_r in zip(details_s, details_r):
        # They should correspond to the same outcome in the same index
        label = row_s["label"]
        # E_s / E_r / i
        E_s = row_s["E_s"]
        E_r = row_r["E_r"]
        i_val = row_s["i"]

        # net effect for sheet2
        k_s = row_s["contribution"]
        star_s = star_html_5(k_s)
        # net effect for sheet3
        k_r = row_r["contribution"]
        star_r = star_html_5(k_r)

        st.write(
            f"| **{label}** "
            f"| {E_s:.3f} "
            f"| {E_r:.3f} "
            f"| {i_val} "
            f"| {star_s} ( {k_s:.4f} )"
            f"| {star_r} ( {k_r:.4f} ) |"
        )

    # Show final net benefit for each method
    st.markdown("### 合計正味の益")
    score_s = round(net_s * 1000, 0)
    score_r = round(net_r * 1000, 0)

    # Interpretation
    interpret_sheet2 = interpret_net_benefit(net_s)
    interpret_sheet3 = interpret_net_benefit(net_r)

    st.markdown(f"**Sheet2 (合計重要度で正規化)**：Net = {net_s:.4f} → 1000人あたり {score_s:.0f}人, {interpret_sheet2}")
    st.markdown(f"**Sheet3 (最重要=100基準)**：Net = {net_r:.4f} → 1000人あたり {score_r:.0f}人, {interpret_sheet3}")

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


# ----------------------------------------------------
# Computation Functions
# ----------------------------------------------------

def compute_sheet2(user_data):
    """
    Sheet2: "Sum-based weighting"
      w_k = i_k / sum(i_k)
      net = sum( w_k * E_s_k * f_k )
    Returns (net_sum, details_list)
    """
    total_i = sum(o["i"] for o in user_data)
    if abs(total_i) < 1e-9:
        return (0.0, [])  # or handle error

    details = []
    net_sum = 0.0
    for o in user_data:
        w_k = o["i"] / total_i if total_i != 0 else 0
        contribution = o["E_s"] * w_k * o["f"]
        net_sum += contribution
        details.append({
            "label": o["label"],
            "E_s":   o["E_s"],
            "i":     o["i"],
            "contribution": contribution
        })
    return (net_sum, details)

def compute_sheet3(user_data):
    """
    Sheet3: "Ratio-to-100 weighting"
      w_k = i_k / 100
      net = sum( w_k * E_r_k * f_k )
    """
    details = []
    net_sum = 0.0
    for o in user_data:
        w_k = o["i"] / 100.0
        contribution = o["E_r"] * w_k * o["f"]
        net_sum += contribution
        details.append({
            "label": o["label"],
            "E_r":   o["E_r"],
            "i":     o["i"],
            "contribution": contribution
        })
    return (net_sum, details)

def interpret_net_benefit(value):
    """
    Positive => Possibly net harm
    Negative => Possibly net benefit
    """
    if value > 0:
        return "有害方向の可能性 (プラス)"
    elif abs(value) < 1e-9:
        return "ほぼ変化なし (ニュートラル)"
    else:
        return "有益方向の可能性 (マイナス)"


# ----------------------------------------------------
# Constraint Helper
# ----------------------------------------------------
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


# ----------------------------------------------------
# Star Rendering
# ----------------------------------------------------
def star_html_5(net_effect):
    """
    Show up to 5 color-coded stars:
      - GREEN if net_effect > 0
      - RED if net_effect < 0
      - Gray dash if ~0
    We'll use absolute value thresholds to decide how many stars to show.
    """
    abs_val = abs(net_effect)

    # Example thresholds (tweak as desired)
    if abs_val < 0.0005:
        star_count = 0
    elif abs_val < 0.001:
        star_count = 1
    elif abs_val < 0.002:
        star_count = 2
    elif abs_val < 0.004:
        star_count = 3
    elif abs_val < 0.008:
        star_count = 4
    else:
        star_count = 5

    if star_count == 0:
        return "<span style='color:gray;font-size:18px;'>—</span>"

    star_color = "green" if net_effect > 0 else "red"
    stars = ""
    for i in range(star_count):
        stars += f"<span style='color:{star_color};font-size:18px;'>★</span>"
    # fill up to 5
    for i in range(5 - star_count):
        stars += "<span style='color:lightgray;font-size:18px;'>★</span>"

    return stars


# ----------------------------------------------------
# Main Entry
# ----------------------------------------------------
if __name__ == "__main__":
    main()
