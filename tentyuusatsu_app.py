import streamlit as st
from datetime import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages
from month_kanshi_index_dict import month_kanshi_index_dict  # ← 追加：月干支の固定表

# 1番目を空欄にして、干支の「1〜60番」と index を合わせる
kanshi_list = [
    "",  # ← index=0 を空にして1始まりに
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"
]

def get_year_kanshi_from_risshun(birth_date):
    """立春基準で年干支を求める（最小修正：立春前は前年にする）"""
    year = birth_date.year
    rs = risshun_dict.get(year)
    if rs and birth_date < rs:
        year -= 1
    kanshi_index = ((year - 1984) % 60) + 1
    return kanshi_list[kanshi_index]

def _calc_base_year_and_setsuge(birth_date):
    """立春判定で基準年（base_year）を決め、節月番号(寅=1..丑=12)も計算"""
    y = birth_date.year
    rs = risshun_dict.get(y)
    base_year = y if (not rs or birth_date >= rs) else (y - 1)
    setsu_no = ((birth_date.month - 2) % 12) + 1  # 2月→1, …, 1月→12
    return base_year, setsu_no

def get_setsuge_month(birth_date):
    """節月番号（寅=1..丑=12）。2月→1, 3月→2, …, 12月→11, 1月→12。
       立春前は12（前年の丑月）扱い。"""
    y = birth_date.year
    rs = risshun_dict.get(y)
    if rs and birth_date < rs:
        return 12  # 1月〜立春前は前年の丑月
    return ((birth_date.month - 2) % 12) + 1

# ーーー 追加：月干支の取得（固定表＋立春年で参照） ーーー
def get_month_kanshi_from_table(birth_date):
    base_year, setsu_no = _calc_base_year_and_setsuge(birth_date)
    # 暦月優先 → 立春年×暦月 → 立春年×節月 → 暦年×暦月
    cand_keys = [
        (base_year, birth_date.month),  # ← 先頭に
        (base_year, setsu_no),
        (birth_date.year, birth_date.month),
    ]
    for y, m in cand_keys:
        try:
            idx = int(month_kanshi_index_dict[y][m])
            return kanshi_list[idx], idx, {"hit": (y, m), "base_year": base_year, "setsu_no": setsu_no}
        except Exception:
            pass
    return "該当なし", None, {"hit": None, "base_year": base_year, "setsu_no": setsu_no}

def get_day_kanshi_from_table(birth_date):
    base_year, setsu_no = _calc_base_year_and_setsuge(birth_date)
    cand_keys = [
        (base_year, birth_date.month),  # ← 先頭に
        (base_year, setsu_no),
        (birth_date.year, birth_date.month),
    ]
    last_dbg = {"hit": None, "base_year": base_year, "setsu_no": setsu_no, "base_index": None}
    for y, m in cand_keys:
        try:
            base_index = int(kanshi_index_table[y][m])
            day_index = base_index + birth_date.day
            while day_index > 60:
                day_index -= 60
            last_dbg.update({"hit": (y, m), "base_index": base_index, "day_index": day_index})
            return kanshi_list[day_index], day_index, last_dbg
        except Exception:
            pass
    return "該当なし", None, last_dbg

def get_tenchusatsu_from_day_index(index):
    if index is None:
        return "該当なし"
    if 51 <= index <= 60 or index == 0:
        return "子丑"
    elif 41 <= index <= 50:
        return "寅卯"
    elif 31 <= index <= 40:
        return "辰巳"
    elif 21 <= index <= 30:
        return "午未"
    elif 11 <= index <= 20:
        return "申酉"
    elif 1 <= index <= 10:
        return "戌亥"
    return "不明"

def main():
    st.title("天中殺診断アプリ【簡易版】")

    birth_date = st.date_input(
        "生年月日を入力してください（範囲：1900年～2033年）",
        value=datetime(2000, 1, 1),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2033, 12, 31)
    )

    if st.button("診断する"):
        # 診断ボタン内
        year_kanshi = get_year_kanshi_from_risshun(birth_date)
        month_kanshi, month_idx, month_dbg = get_month_kanshi_from_table(birth_date)  # ← 変更
        day_kanshi, index, day_dbg = get_day_kanshi_from_table(birth_date)  # ← 変更

        st.markdown(f"### 年干支（立春基準）: {year_kanshi}")
        st.markdown(f"### 月干支（立春基準・固定表）: {month_kanshi}")
        st.markdown(f"### 日干支＆天中殺用数値： {day_kanshi}（インデックス: {index}）")

        with st.expander("デバッグ情報"):
            st.write({"month": month_dbg, "day": day_dbg})

        if index is None:
            st.warning("この年の干支データは未登録のため、天中殺の診断ができません。")
            return

        st.info("※ 表の月数値に日を足して求める伝統的な方法に基づいた計算です。")

        tenchusatsu = get_tenchusatsu_from_day_index(index)
        st.markdown(f"### 天中殺 : {tenchusatsu}")

        message = tentyuusatsu_messages.get(tenchusatsu)
        if message:
            for line in message:
                st.markdown(f"- {line}")
        else:
            st.warning("天中殺に対応するメッセージが見つかりませんでした。")

if __name__ == "__main__":
    main()
