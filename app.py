import streamlit as st

def main():
    st.title("正味の益計算 プロトタイプ（カスタムスライダー範囲）")

    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （日本語版：セル参照などの技術的表記は非表示）
        </p>
        <p>
        <strong>概要：</strong><br>
        このアプリでは、各アウトカム（脳卒中予防・心不全予防・めまい・頻尿・転倒）に関する
        <em>推定リスク差</em> と <em>重要度</em> を入力し、正味の益スコアを計算します。<br>
        スライダーの範囲は下記のようにカスタマイズされています：
        <ul>
          <li>脳卒中予防 / 心不全予防：–0.10 ～ +0.10</li>
          <li>めまい / 頻尿 / 転倒：–0.02 ～ +0.02</li>
        </ul>
        内部ロジックはエクセルでの計算式（K<sub>k</sub>, K17, K24）に準じています。
        </p>
        """,
        unsafe_allow_html=True
    )

    # アウトカムの定義（固定されたF値、初期E値、重要度など）
    outcomes = [
        {
            "display_name": "脳卒中予防",
            "f":  1,
            "default_e":  0.10,
            "default_i": 100,
            "min_e": -0.10,
            "max_e":  0.10
        },
        {
            "display_name": "心不全予防",
            "f":  1,
            "default_e": -0.10,
            "default_i": 29,
            "min_e": -0.10,
            "max_e":  0.10
        },
        {
            "display_name": "めまい",
            "f": -1,
            "default_e":  0.02,
            "default_i":  5,
            "min_e": -0.02,
            "max_e":  0.02
        },
        {
            "display_name": "頻尿",
            "f": -1,
            "default_e": -0.01,
            "default_i":  4,
            "min_e": -0.02,
            "max_e":  0.02
        },
        {
            "display_name": "転倒",
            "f": -1,
            "default_e": -0.02,
            "default_i": 13,
            "min_e": -0.02,
            "max_e":  0.02
        },
    ]

    # --------------------------
    # サイドバー：アウトカムの入力
    # --------------------------
    st.sidebar.header("① アウトカムとその重要度の調整")

    user_data = []
    for item in outcomes:
        st.sidebar.subheader(item["display_name"])

        e_val = st.sidebar.slider(
            f"{item['display_name']}：推定リスク差",
            min_value=item["min_e"],
            max_value=item["max_e"],
            value=float(item["default_e"]),
            step=0.001
        )

        i_val = st.sidebar.slider(
            f"{item['display_name']}：重要度（0 = 重要ではない, 100 = 非常に重要）",
            min_value=0,
            max_value=100,
            value=item["default_i"],
            step=1
        )

        user_data.append({
            "label": item["display_name"],
            "f": item["f"],
            "e": e_val,
            "i": i_val
        })

    # --------------------------
    # サイドバー：制約(Constraints)
    # --------------------------
    st.sidebar.header("② 制約（Constraints）")
    st.sidebar.write("各種制約レベルを選んでください：")

    constraint_options = ["問題なし", "やや問題", "大きな問題"]
    cost_label = st.sidebar.radio("費用面の問題", constraint_options, index=0)
    access_label = st.sidebar.radio("通院アクセスの問題", constraint_options, index=0)
    care_label = st.sidebar.radio("介助面の問題", constraint_options, index=0)

    cost_val = constraint_to_numeric(cost_label)
    access_val = constraint_to_numeric(access_label)
    care_val = constraint_to_numeric(care_label)

    # ボタン
    if st.sidebar.button("正味の益を計算する"):
        show_results(user_data, cost_val, access_val, care_val)


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")

    # 1) 重要度の合計
    total_i = sum(row["i"] for row in user_data)
    if abs(total_i) < 1e-9:
        st.error("すべてのアウトカムの重要度が0です。少なくとも1つは重要度を0より大きくしてください。")
        return

    # 2) アウトカムごとの貢献度計算
    st.markdown("### 各アウトカムの詳細")
    k_values = []
    for row in user_data:
        # Normalize importance by total importance
        j_k = row["i"] / total_i

        # Weighted effect
        k_k = row["e"] * j_k * row["f"]
        k_values.append(k_k)

        # Determine arrow (direction of effect)
        arrow_html = get_arrow(row["e"] * row["f"])
        # Convert importance to star rating
        stars = star_html_3(row["i"])

        # Display outcome info with arrow + stars
        st.markdown(
            f"- <strong>{row['label']}</strong>: "
            f"{stars} {arrow_html} "
            f"(推定リスク差 = {row['e']:.3f}, 重要度 = {row['i']})",
            unsafe_allow_html=True
        )

    # Sum net benefit
    net_sum = sum(k_values)
    # Per 1000
    score_1000 = round(1000 * net_sum, 0)

    # Interpretation
    if net_sum > 0:
        st.warning("全体として有害方向になる可能性があります（プラス方向）。")
    elif abs(net_sum) < 1e-9:
        st.info("全体としてほぼ変化がない（ニュートラル）可能性があります。")
    else:
        st.success("全体として有益方向になる可能性があります（マイナス方向）。")

    st.markdown(
        f"**正味の益スコア（合計）**: {net_sum:.4f}<br>"
        f"**1000人あたりの人数**: {score_1000:.0f}人",
        unsafe_allow_html=True
    )

    # Constraints section
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

    st.write(f"- 費用面: **{numeric_to_constraint_label(cost_val)}**")
    st.write(f"- アクセス面: **{numeric_to_constraint_label(access_val)}**")
    st.write(f"- 介助面: **{numeric_to_constraint_label(care_val)}**")

    # Placeholder for advanced analysis
    st.subheader("その他の高度な解析（Placeholder）")
    st.markdown(
        """
        <p style='color:red; font-weight:bold;'>
        （本番環境では非表示）
        </p>
        <ul>
          <li>相関や高度な加重（AHP, DCE）を取り入れた計算</li>
          <li>信頼区間を考慮した確率的アプローチ</li>
          <li>有益・有害アウトカムの整理や図表化</li>
        </ul>
        """,
        unsafe_allow_html=True
    )


# ---------------- HELPER FUNCTIONS ----------------

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
    Show an arrow indicating direction of effect.
    Use color coding for clarity:
      - Green arrow up if strongly positive
      - Red arrow down if strongly negative
      - Gray arrow right if near zero
    """
    if value > 0.05:
        return "<span style='color:green;'>⬆️</span>"
    elif value < -0.05:
        return "<span style='color:red;'>⬇️</span>"
    else:
        return "<span style='color:gray;'>➡️</span>"

def star_html_3(importance_0to100):
    """
    0..100 の重要度を 1〜3 の星に変換
      0〜33  => ★1
      34〜66 => ★2
      67〜100=> ★3
    """
    if importance_0to100 == 0:
        # Show no stars if importance is 0
        return "<span style='color:lightgray;font-size:18px;'>―</span>"

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

if __name__ == "__main__":
    main()
