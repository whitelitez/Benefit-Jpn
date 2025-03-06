import streamlit as st

def main():
    st.title("正味の益計算：Sheet2 & Sheet3（2方式）＋色付きメッセージ")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：効果推定値s & 効果推定値r 両方計算＋色付き結果表示）
        </p>
        <p>
        - リスク差 (E) は数値入力またはスライダーでも可。<br>
        - 重要度 (i) は 0～100 スライダー。<br>
        - Sheet2 = 合計重要度で正規化 ( E × (i / Σi) × f )<br>
        - Sheet3 = 最重要100基準 ( E × (i / 100) × f )<br>
        - 最終的に両方式それぞれの結果を解釈し、正 (プラス方向) なら赤枠、負 (マイナス方向) なら緑枠、ほぼ 0 なら青枠で表示。
        </p>
        """,
        unsafe_allow_html=True
    )

    # Define outcomes
    outcomes = [
        {"label": "脳卒中予防", "f": +1, "default_e":  0.10, "default_i": 100},
        {"label": "心不全予防", "f": +1, "default_e": -0.10, "default_i": 29},
        {"label": "めまい",   "f": -1, "default_e":  0.02, "default_i":  5},
        {"label": "頻尿",     "f": -1, "default_e":  0.04, "default_i":  4},
        {"label": "転倒",     "f": -1, "default_e":  0.06, "default_i": 13},
    ]

    st.sidebar.header("① アウトカムの入力")
    user_data = []
    for item in outcomes:
        st.sidebar.subheader(item["label"])
        E_val = st.sidebar.number_input(
            f"{item['label']}：リスク差 E",
            value=float(item["default_e"]),
            step=0.01,
            format="%.3f"
        )
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
    """Compute and display results for both Sheet2 & Sheet3, with color-coded messages."""
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) Sheet2 => sum-based weighting
    net_s, details_s = compute_sheet2(user_data)

    # 2) Sheet3 => ratio-to-100 weighting
    net_r, details_r = compute_sheet3(user_data)

    st.markdown("### 各アウトカムの貢献度比較")
    for row_s, row_r in zip(details_s, details_r):
        # They should match the same outcome index
        label = row_s["label"]
        E_val = row_s["E"]
        i_val = row_s["i"]

        nb_s = row_s["contribution"]  # sheet2 net effect
        nb_r = row_r["contribution"]  # sheet3 net effect

        st.markdown(
            f"- **{label}**：E={E_val:.3f}, i={i_val} "
            f"<br>&emsp;Sheet2貢献度: {nb_s:.4f}, "
            f"Sheet3貢献度: {nb_r:.4f}",
            unsafe_allow_html=True
        )

    # Convert net sums to per 1000
    score_s = round(net_s * 1000, 0)
    score_r = round(net_r * 1000, 0)

    st.markdown("### 合計正味の益")

    # --- Sheet2 interpretation ---
    if net_s > 0:
        st.error(f"【Sheet2】全体として有害方向になる可能性があります（プラス）。\n"
                 f"Net={net_s:.4f}, 1000人あたり={score_s:.0f}人")
    elif abs(net_s) < 1e-9:
        st.info(f"【Sheet2】ほぼ変化なし（ニュートラル）の可能性。\n"
                f"Net={net_s:.4f}, 1000人あたり={score_s:.0f}人")
    else:
        st.success(f"【Sheet2】全体として有益方向になる可能性があります（マイナス）。\n"
                   f"Net={net_s:.4f}, 1000人あたり={score_s:.0f}人")

    # --- Sheet3 interpretation ---
    if net_r > 0:
        st.error(f"【Sheet3】全体として有害方向になる可能性があります（プラス）。\n"
                 f"Net={net_r:.4f}, 1000人あたり={score_r:.0f}人")
    elif abs(net_r) < 1e-9:
        st.info(f"【Sheet3】ほぼ変化なし（ニュートラル）の可能性。\n"
                f"Net={net_r:.4f}, 1000人あたり={score_r:.0f}人")
    else:
        st.success(f"【Sheet3】全体として有益方向になる可能性があります（マイナス）。\n"
                   f"Net={net_r:.4f}, 1000人あたり={score_r:.0f}人")

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
# Sheet2 / Sheet3 Functions
# --------------------------

def compute_sheet2(user_data):
    """
    Sheet2: "Sum-based weighting"
      net = sum( (i_k / sum_i) * E_k * f_k )
    """
    total_i = sum(d["i"] for d in user_data)
    if abs(total_i) < 1e-9:
        return (0.0, [])

    details = []
    net_sum = 0.0
    for d in user_data:
        w_s = d["i"] / total_i
        contrib = d["E"] * w_s * d["f"]
        net_sum += contrib
        details.append({
            "label": d["label"],
            "E":     d["E"],
            "i":     d["i"],
            "contribution": contrib
        })

    return (net_sum, details)

def compute_sheet3(user_data):
    """
    Sheet3: "Ratio-to-100 weighting"
      net = sum( (i_k / 100) * E_k * f_k )
    """
    details = []
    net_sum = 0.0
    for d in user_data:
        w_r = d["i"] / 100.0
        contrib = d["E"] * w_r * d["f"]
        net_sum += contrib
        details.append({
            "label": d["label"],
            "E":     d["E"],
            "i":     d["i"],
            "contribution": contrib
        })

    return (net_sum, details)


# --------------------------
# Constraints Helper
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


# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    main()
