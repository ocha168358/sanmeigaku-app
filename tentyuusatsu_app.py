import streamlit as st
from datetime import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages
from month_kanshi_index_dict import month_kanshi_index_dict

# 1番目を空欄にして、干支の「1〜60番」と index を合わせる
kanshi_list = [
    "",  # index=0 を空に
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

def get_year_kanshi_from_risshun(birth_date):
    """立春基準で年干支名を返す（立春前は前年）"""
    year = birth_date.year
    rs = risshun_dict.get(year)
    if rs and birth_date < rs:
        year -= 1
    idx = ((year - 1984) % 60) + 1
    return kanshi_list[idx]

def main():
    st.title("天中殺診断アプリ【簡易版】")

    birth_date = st.date_input(
        "生年月日を入力してください（範囲：1900年～2033年）",
        value=datetime(2000, 1, 1),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2033, 12, 31),
    )

    if st.button("診断する"):
        # ————— 立春基準の (y, m) を先に決める（立春前→前年12月節） —————
        rs = risshun_dict.get(birth_date.year)
        if rs and birth_date < rs:
            y, m = birth_date.year - 1, 12
        else:
            y, m = birth_date.year, birth_date.month

        # ————— 年干支（立春基準） —————
        year_kanshi = get_year_kanshi_from_risshun(birth_date)

        # ————— 月干支（固定表：month_kanshi_index_dict から 1..60） —————
        month_start = month_kanshi_index_dict.get((y, m))
        # 型揺れに備えて数値化
        try:
            month_start = int(month_start) if month_start is not None else None
        except Exception:
            month_start = None

        # 0→60 の保険
        if month_start == 0:
            month_start = 60

        month_kanshi = kanshi_list[month_start] if month_start else "該当なし"

        # ————— 日干支（固定表A方式：kanshi_index_table[y][m] + 日） —————
        try:
            base = int(kanshi_index_table[y][m])  # 月の「1日目-1」（0..59）
        except Exception:
            day_kanshi = "該当なし"
            day_idx = None
        else:
            day_idx = base + birth_date.day
            while day_idx > 60:
                day_idx -= 60
            if day_idx == 0:
                day_idx = 60
            day_kanshi = kanshi_list[day_idx]

        # ————— 表示 —————
        st.markdown(f"### 年干支（立春基準）：{year_kanshi}")
        st.markdown(f"### 月干支（立春基準）：{month_kanshi}")
        st.markdown(f"### 日干支＆天中殺用数値：{day_kanshi}（インデックス: {day_idx}）")

        if day_idx is None:
            st.warning("この月の干支データが未登録のため、天中殺の診断ができません。")
            return

        st.info("※ 表の月数値に日を足して求める伝統的な方法に基づいた計算です。")

        # ————— 天中殺 —————
        if 51 <= day_idx <= 60:
            tenchusatsu = "子丑"
        elif 41 <= day_idx <= 50:
            tenchusatsu = "寅卯"
        elif 31 <= day_idx <= 40:
            tenchusatsu = "辰巳"
        elif 21 <= day_idx <= 30:
            tenchusatsu = "午未"
        elif 11 <= day_idx <= 20:
            tenchusatsu = "申酉"
        else:  # 1..10
            tenchusatsu = "戌亥"

        st.markdown(f"### 天中殺：{tenchusatsu}")

        message = tentyuusatsu_messages.get(tenchusatsu)
        if message:
            for line in message:
                st.markdown(f"- {line}")
        else:
            st.warning("天中殺に対応するメッセージが見つかりませんでした。")

if __name__ == "__main__":
    main()
