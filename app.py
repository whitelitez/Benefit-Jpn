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
        内部ロジックはエクセルでの計算式に準じています。
        </p>
        """,
        unsafe_allow_html=True
    )

    # アウトカムの定義（固定されたf値、初期E値、重要度など）
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
        # Normalize importance by total
        w_k = row["i"] / total_i
        # Net effect
        k_k = row["e"] * w_k * row["f"]
        k_values.append(k_k)

        # Show star rating (color-coded by sign, # of stars by magnitude)
        star_html = star_html_5(k_k)
        st.markdown(
            f"- <strong>{row['label']}</strong>: {star_html} "
            f"(推定リスク差={row['e']:.3f}, 重要度={row['i']}, 貢献度={k_k:.4f})",
            unsafe_allow_html=True
        )

    # Net benefit sum
    net_sum = sum(k_values)
    # Per 1000
    score_1000 = round(1000 * net_sum, 0)

    # Interpretation with color-coded message
    if net_sum > 0:
        # Red box
        st.error("全体として有害方向になる可能性があります（プラス方向）。")
    elif abs(net_sum) < 1e-9:
        # Blue box
        st.info("全体としてほぼ変化がない（ニュートラル）可能性があります。")
    else:
        # Green box
        st.success("全体として有益方向になる可能性があります（マイナス方向）。")

    st.markdown(
        f"**正味の益スコア（合計）**： {net_sum:.4f}<br>"
        f"**1000人あたりの人数**： {score_1000:.0f}人",
        unsafe_allow_html=True
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

    # Placeholder
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

def star_html_5(net_effect):
    """
    Return a string of up to 5 colored stars:
      - GREEN stars if net_effect > 0
      - RED stars if net_effect < 0
      - Gray dash if ~0
    The magnitude (absolute value) determines how many stars.

    Adjust these thresholds as desired. For example:
    - < 0.0005 => 0 stars
    - < 0.001  => 1 star
    - < 0.002  => 2 stars
    - < 0.004  => 3 stars
    - < 0.008  => 4 stars
    - else     => 5 stars
    """
    abs_val = abs(net_effect)

    if abs_val < 0.0005:
        # Show dash for near-zero
        return "<span style='color:gray;font-size:18px;'>—</span>"

    # Decide star_count
    if abs_val < 0.001:
        star_count = 1
    elif abs_val < 0.002:
        star_count = 2
    elif abs_val < 0.004:
        star_count = 3
    elif abs_val < 0.008:
        star_count = 4
    else:
        star_count = 5

    # If net_effect > 0 => green, net_effect < 0 => red
    star_color = "green" if net_effect > 0 else "red"

    stars = ""
    for _ in range(star_count):
        stars += f"<span style='color:{star_color};font-size:18px;'>★</span>"

    # Fill the remainder (up to 5) with lightgray
    for _ in range(5 - star_count):
        stars += "<span style='color:lightgray;font-size:18px;'>★</span>"

    return stars


if __name__ == "__main__":
    main()
