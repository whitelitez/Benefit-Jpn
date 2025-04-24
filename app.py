import streamlit as st

def profile_page():
    st.title("ユーザープロファイル")
    st.markdown("**年齢** と **性別** と **都道府県** を入力してください。")

    # Collect user profile information.
    age = st.number_input("年齢", min_value=0, max_value=120, value=25)
    gender = st.selectbox("性別", ["男性", "女性", "その他"])

    prefectures = [
        "北海道", "青森県", "岩手県", "宮城県", "秋田県",
        "山形県", "福島県", "茨城県", "栃木県", "群馬県",
        "埼玉県", "千葉県", "東京都", "神奈川県"
    ]
    prefecture = st.selectbox("都道府県", prefectures)

    if st.button("次へ"):
        st.session_state.age = age
        st.session_state.gender = gender
        st.session_state.prefecture = prefecture
        st.session_state.profile_complete = True


def constraint_to_numeric(label):
    if label == "問題なし":
        return 0.0
    elif label == "やや問題":
        return 0.5
    else:
        return 1.0


def numeric_to_constraint_label(value):
    if value == 0.0:
        return "問題なし"
    elif value == 0.5:
        return "やや問題"
    else:
        return "重視する"


def star_html_5(net_effect):
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
    for _ in range(star_count):
        result += f"<span style='color:{star_color};font-size:18px;'>★</span>"
    for _ in range(5 - star_count):
        result += "<span style='color:lightgray;font-size:18px;'>★</span>"
    return result


def show_results(user_data, cost_val, access_val, care_val):
    st.subheader("正味の益（Net Benefit）計算結果")
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
        w_s = i_val / total_i
        nb_s = E_val * w_s * f_val
        net_sum_s += nb_s
        star_s = star_html_5(nb_s)
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
    st.markdown("### 合計正味の益")
    s_1000 = int(round(net_sum_s * 1000, 0))
    r_1000 = int(round(net_sum_r * 1000, 0))
    if net_sum_s > 0:
        st.error(f"効果推定値s 全体として有害方向になる可能性があります（プラス）。\nNet=1000人あたり={s_1000}人")
    elif abs(net_sum_s) < 1e-9:
        st.info(f"効果推定値s 全体としてほぼ変化なし（ニュートラル）の可能性。\nNet=1000人あたり={s_1000}人")
    else:
        st.success(f"効果推定値s 全体として有益方向になる可能性があります（マイナス）。\nNet=1000人あたり={s_1000}人")
    if net_sum_r > 0:
        st.error(f"効果推定値r 全体として有害方向になる可能性があります（プラス）。\nNet=1000人あたり={r_1000}人")
    elif abs(net_sum_r) < 1e-9:
        st.info(f"効果推定値r 全体としてほぼ変化なし（ニュートラル）の可能性。\nNet=1000人あたり={r_1000}人")
    else:
        st.success(f"効果推定値r 全体として有益方向になる可能性があります（マイナス）。\nNet=1000人あたり={r_1000}人")
    st.subheader("制約（Constraints）の状況")
    max_sev = max(cost_val, access_val, care_val)
    if max_sev == 0.0:
        st.success("制約：すべて問題なし（緑）")
    elif max_sev == 0.5:
        st.warning("制約：懸念ありの項目があります（黄）")
    else:
        st.error("制約：問題ありの項目があります（赤）")
    st.write(f"- 費用面: **{numeric_to_constraint_label(cost_val)}**")
    st.write(f"- アクセス面: **{numeric_to_constraint_label(access_val)}**")
    st.write(f"- 介助面: **{numeric_to_constraint_label(care_val)}**")


def main():
    if not st.session_state.get("profile_complete", False):
        profile_page()
        return
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
        - <em>効果推定値s</em
