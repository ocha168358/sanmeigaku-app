
"""kanshi_calc.py

このモジュールでは、干支や天中殺の計算に関するロジックをまとめています。
年干支・月干支のインデックス計算を行い、その結果から干支名や天中殺グループを取得するための
関数群を提供します。日付から直接天中殺グループを求める補助関数も用意しています。

従来の `kanshi_month_start_index` を用いた方式は一部の年にしか対応しておらず、
算命学で一般的に用いられる月干支計算には「年ごとの揺らぎ」を考慮する必要があります。
ここでは `day_kanshi_dict.py` に定義されている `kanshi_index_table` を利用して、
年・節月ごとに正確な干支インデックスを取得できるようにしています。

注意: 月干支インデックスの計算では、立春前の場合に前年の12月節として扱うため、
`get_setsuge_month()` と `get_year_kanshi_index()` の結果を組み合わせて計算します。
"""

# app.py
import streamlit as st
from datetime import datetime, date

# --- 既存ロジック（インポート or 同ファイルに定義） ---
# from kanshi_calc import get_year_kanshi_from_risshun, get_day_kanshi_from_table, get_tenchusatsu_from_day_index
# from tenchusatsu_messages import tentyuusatsu_messages

# -----------------------------------------
# ウィザード共通設定
# -----------------------------------------
st.set_page_config(page_title="天中殺診断（ステップ式）", page_icon="🔮", layout="centered")

STEPS = ["生年月日入力", "確認", "診断結果"]

if "step" not in st.session_state:
    st.session_state.step = 0
if "birth_date" not in st.session_state:
    st.session_state.birth_date = None
if "result" not in st.session_state:
    st.session_state.result = {}

def go_next():
    st.session_state.step = min(st.session_state.step + 1, len(STEPS)-1)

def go_prev():
    st.session_state.step = max(st.session_state.step - 1, 0)

def reset_all():
    st.session_state.step = 0
    st.session_state.birth_date = None
    st.session_state.result = {}

# -----------------------------------------
# ヘッダー／進捗
# -----------------------------------------
st.title("天中殺診断 🔮")
st.caption("立春基準で年・月の扱いを整えた計算ロジックを使っています。")
st.progress((st.session_state.step+1)/len(STEPS))
st.write(f"**STEP {st.session_state.step+1} / {len(STEPS)}：{STEPS[st.session_state.step]}**")

# -----------------------------------------
# STEP 1: 生年月日入力
# -----------------------------------------
if st.session_state.step == 0:
    st.markdown("次の範囲で生年月日を選んでください。選んだら「次へ」。")

    with st.form("input_form", clear_on_submit=False):
        bd = st.date_input(
            "生年月日",
            value=st.session_state.birth_date or date(2000, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date(2033, 12, 31),
            help="※ 立春（2/3〜2/5頃）をまたぐ場合は内部で前年扱いになります。"
        )
        col1, col2 = st.columns([1,1])
        submitted = col1.form_submit_button("次へ ▶")
        cancel = col2.form_submit_button("リセット", on_click=reset_all)

    if submitted:
        st.session_state.birth_date = bd
        go_next()

# -----------------------------------------
# STEP 2: 確認
# -----------------------------------------
elif st.session_state.step == 1:
    bd = st.session_state.birth_date
    st.info("入力内容を確認してください。問題なければ「診断する」。修正したい場合は「戻る」。")

    with st.container(border=True):
        st.write("**生年月日**：", bd.strftime("%Y年 %m月 %d日（%a）"))

        # プレビュー（任意）：ここで年干支・日干支の“予定値”を一旦計算して見せることも可能
        try:
            year_kanshi = get_year_kanshi_from_risshun(bd)
            day_kanshi, idx = get_day_kanshi_from_table(bd)
            st.write("**年干支（立春基準）**：", year_kanshi)
            st.write("**日干支（伝統方式）**：", f"{day_kanshi}（index: {idx}）")
        except Exception:
            st.write("プレビューは省略します。")

    col1, col2 = st.columns([1,1])
    col1.button("◀ 戻る", on_click=go_prev, use_container_width=True)
    def _run_calc():
        bd2 = st.session_state.birth_date
        # --- ここで本計算 ---
        yk = get_year_kanshi_from_risshun(bd2)                  # 文字列（例: '甲子'）
        dk, idx = get_day_kanshi_from_table(bd2)                # ('丁巳', 54) のような戻り値を想定
        ts = get_tenchusatsu_from_day_index(idx) if idx else "該当なし"
        msg = tentyuusatsu_messages.get(ts, [])
        st.session_state.result = {
            "birth_date": bd2,
            "year_kanshi": yk,
            "day_kanshi": dk,
            "day_index": idx,
            "tenchusatsu": ts,
            "messages": msg,
        }
        go_next()
    col2.button("診断する ✅", on_click=_run_calc, type="primary", use_container_width=True)

# -----------------------------------------
# STEP 3: 結果
# -----------------------------------------
else:
    r = st.session_state.result
    if not r:
        st.warning("結果が見つかりません。最初からやり直してください。")
        st.button("最初に戻る", on_click=reset_all)
    else:
        with st.container(border=True):
            st.subheader("診断結果")
            st.write("**生年月日**：", r["birth_date"].strftime("%Y年 %m月 %d日"))
            st.write("**年干支（立春基準）**：", r["year_kanshi"])
            st.write("**日干支（伝統方式）**：", f"{r['day_kanshi']}（index: {r['day_index']}）")
            st.write("**天中殺**：", r["tenchusatsu"])

        if r["messages"]:
            st.markdown("—")
            st.write("**メッセージ**")
            for line in r["messages"]:
                st.markdown(f"- {line}")

        st.markdown("—")
        col1, col2 = st.columns([1,1])
        col1.button("◀ 入力に戻る", on_click=go_prev, use_container_width=True)
        col2.button("もう一度診断する 🔁", on_click=reset_all, use_container_width=True)

# -----------------------------------------
# サイドバー：手順ナビ（読み取り専用）
# -----------------------------------------
with st.sidebar:
    st.header("進行状況")
    for i, name in enumerate(STEPS):
        flag = "✅" if i < st.session_state.step else ("🟡" if i == st.session_state.step else "⚪")
        st.write(f"{flag}  STEP {i+1}: {name}")
    st.divider()
    st.caption("※ サイドバーはナビの表示のみで、直接のスキップはできません。")



