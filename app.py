import streamlit as st

def main():
    st.title("正味の益計算：Sheet2 & Sheet3 両方式対応 (改訂版)")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：技術的表記は非表示）
        </p>
        <p>
        <strong>概要：</strong><br>
        - 各アウトカムについて：リスク差を小数で入力（sliderではなくnumber_input）。<br>
        - 重要度は0～100のスライダー。<br>
        - <em>Sheet2 (効果推定値s)</em> と <em>Sheet3 (効果推定値r)</em> の2つの方式で
          正味の益を計算し、それぞれ星の表示と「1000人あたり」スコアを出します。<br>
        - Net Benefitの符号：
          プラス → 有害方向, マイナス → 有益方向, として解釈を表示します。
        </p>
        """,
        unsafe_allow_html=True
    )

    # Define each outcome's info
    outcomes = [
        {
            "label": "脳卒中予防",
            "f": +1,
            "default_e":  0.10,
            "default_i": 100,
        },
        {
            "label": "心不全予防",
            "f": +1,
            "default_e": -0.10,
            "default_i": 29,
        },
        {
            "label": "めまい",
            "f": -1,
            "default_e":  0.02,
            "default_i":  5,
        },
        {
            "label": "頻尿",
            "f": -1,
            "default_e":  0.04,
            "default_i":  4,
        },
        {
            "label": "転倒",
            "f": -1,
            "default_e":  0.06,
            "default_i": 13,
        },
    ]

    st.sidebar.header("① アウトカムのリスク差・重要度の入力")

    user_data = []
    for item in outcomes:
        st.sidebar.subheader(item["label"])

        # Numeric input for E
        e_val = st.sidebar.number_input(
            f"{item['label']}：リスク差 (小数可)",
            value=float(item["default_e"]),
            step=0.01,
            format="%.3f"
        )

        # Slider for importance (0..100)
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
            "E":     e_val,
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
        show_results(user_data, cost_val, access_val, care_val)


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) Sheet2 => sum-based weighting
    net_s, details_s = compute_sheet2(user_data)

    # 2) Sheet3 => ratio-to-100 weighting
    net_r, details_r = compute_sheet3(user_data)

    # Build an HTML table so that star HTML renders properly
    table_html = """
    <table border="1" style="border-collapse: collapse;">
      <thead>
        <tr>
          <th style="padding:4px;">アウトカム</th>
          <th style="padding:4px;">リスク差 (E)</th>
          <th style="padding:4px;">重要度 (i)</th>
          <th style="padding:4px;">Sheet2 貢献度</th>
          <th style="padding:4px;">Sheet3 貢献度</th>
        </tr>
      </thead>
      <tbody>
    """

    # Combine row info
    for s_row, r_row in zip(details_s, details_r):
        label = s_row["label"]  # same as r_row["label"]
        E_val = s_row["E"]      # single E
        i_val = s_row["i"]

        # Sheet2 contribution
        contrib_s = s_row["contribution"]  # numeric
        star_s = star_html_5(contrib_s)

        # Sheet3 contribution
        contrib_r = r_row["contribution"]
        star_r = star_html_5(contrib_r)

        table_html += f"""
        <tr>
          <td style="padding:4px;">{label}</td>
          <td style="padding:4px; text-align:right;">{E_val:.3f}</td>
          <td style="padding:4px; text-align:right;">{i_val}</td>
          <td style="padding:4px;">{star_s} &nbsp;({contrib_s:.4f})</td>
          <td style="padding:4px;">{star_r} &nbsp;({contrib_r:.4f})</td>
        </tr>
        """

    table_html += """
      </tbody>
    </table>
    """

    st.markdown("### 各アウトカムの詳細 (Sheet2 & Sheet3)")
    st.markdown(table_html, unsafe_allow_html=True)

    # Final net benefit
    score_s = round(net_s * 1000, 0)
    score_r = round(net_r * 1000, 0)

    interpret_s = interpret_net_benefit(net_s)
    interpret_r = interpret_net_benefit(net_r)

    st.markdown("### 合計正味の益")
    st.markdown(f"- **Sheet2 (効果推定値s)**：Net = {net_s:.4f} → 1000人あたり {score_s:.0f}人, {interpret_s}")
    st.markdown(f"- **Sheet3 (効果推定値r)**：Net = {net_r:.4f} → 1000人あたり {score_r:.0f}人, {interpret_r}")

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
# Computation: Sheet2 & Sheet3
# ----------------------------------------------------
def compute_sheet2(user_data):
    """
    Sheet2: Sum-based weighting
      w_k = i_k / sum(i_k)
      net = sum( w_k * E_k * f_k )
    """
    total_i = sum(d["i"] for d in user_data)
    if abs(total_i) < 1e-9:
        # Avoid dividing by zero
        return (0.0, [])

    details = []
    net_sum = 0.0
    for d in user_data:
        w_k = d["i"] / total_i
        contribution = d["E"] * w_k * d["f"]
        net_sum += contribution
        details.append({
            "label":        d["label"],
            "E":            d["E"],
            "i":            d["i"],
            "contribution": contribution
        })

    return (net_sum, details)

def compute_sheet3(user_data):
    """
    Sheet3: Ratio-to-100 weighting
      w_k = i_k / 100
      net = sum( w_k * E_k * f_k )
    """
    details = []
    net_sum = 0.0
    for d in user_data:
        w_k = d["i"] / 100.0
        contribution = d["E"] * w_k * d["f"]
        net_sum += contribution
        details.append({
            "label":        d["label"],
            "E":            d["E"],
            "i":            d["i"],
            "contribution": contribution
        })

    return (net_sum, details)

# ----------------------------------------------------
# Interpretation
# ----------------------------------------------------
def interpret_net_benefit(value):
    if value > 0:
        return "有害方向の可能性 (プラス)"
    elif abs(value) < 1e-9:
        return "ほぼ変化なし (ニュートラル)"
    else:
        return "有益方向の可能性 (マイナス)"

# ----------------------------------------------------
# Constraint Helpers
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
      - Gray dash if near zero
    Uses absolute thresholds to decide number of stars.
    """
    abs_val = abs(net_effect)

    # Example thresholds
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

    # If net_effect > 0 => "harm" => show green. If net_effect < 0 => show red.
    star_color = "green" if net_effect > 0 else "red"

    stars = ""
    for _ in range(star_count):
        stars += f"<span style='color:{star_color};font-size:18px;'>★</span>"
    # Fill up to 5 with lightgray
    for _ in range(5 - star_count):
        stars += "<span style='color:lightgray;font-size:18px;'>★</span>"

    return stars


if __name__ == "__main__":
    main()
