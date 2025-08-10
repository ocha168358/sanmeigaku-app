import streamlit as st
from datetime import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages
# from hayami import get_year_kanshi_from_risshun , get_month_kanshi
from kanshi_calc import get_month_kanshi_name
from month_kanshi_index_dict import month_kanshi_index_dict  # 追加
from kanshi_calc import get_kanshi_name

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
# 旧立春対応版
# def get_year_kanshi_from_risshun(birth_date):
#     year = birth_date.year
#     kanshi_index = ((year - 1984) % 60) + 1  # ← ここに +1 が必要
#     return kanshi_list[kanshi_index]

#　新立春対応版
def get_year_kanshi_from_risshun(birth_date):
    from risshun_data import risshun_dict
    year = birth_date.year
    risshun = risshun_dict.get(year)
    if risshun and birth_date < risshun:
        year -= 1
    kanshi_index = ((year - 1984) % 60) + 1
    return kanshi_list[kanshi_index]

def get_setsuge_month(birth_date):
    """立春ベースで節月（1～12）を算出"""
    year = birth_date.year
    risshun = risshun_dict.get(year)
    if risshun and birth_date < risshun:
        return 12  # 前年の12月節（1月〜立春前）
    return birth_date.month

def get_day_kanshi_from_table(birth_date):
    year = birth_date.year
    month = get_setsuge_month(birth_date)

    # 立春前は前年のテーブルを参照
    from risshun_data import risshun_dict
    risshun = risshun_dict.get(year)
    year_for_table = year - 1 if (risshun and birth_date < risshun) else year

    try:
        base_index = kanshi_index_table[year_for_table][month]  # 「0日目」インデックス
        # 1日目=base+1 なので、dayで進めて安全に60剰余
        day_index = (base_index + birth_date.day) % 60
        if day_index == 0:
            day_index = 60
        return kanshi_list[day_index], day_index
    except (KeyError, TypeError):
        return "該当なし", None

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
        min_value=datetime(1900, 1, 1),  # ←ここを修正
        max_value=datetime(2033, 12, 31)
    )
    # 今は1925〜2025年のデータのみ正確なため、範囲を制限中
    # データ拡張後に以下へ戻す：
    # min_value=datetime(1900, 1, 1)
    # max_value=datetime(2033, 12, 31)

    if st.button("診断する"):
        year_kanshi = get_year_kanshi_from_risshun(birth_date)
        month_kanshi = get_kanshi_name(month_kanshi_index_dict[(birth_date.year, birth_date.month)])
        day_kanshi, index = get_day_kanshi_from_table(birth_date)

        st.markdown(f"### 年干支（立春基準）: {year_kanshi}")
        st.markdown(f"### 月干支（立春基準）: {month_kanshi}")
        st.markdown(f"### 日干支＆天中殺用数値： {day_kanshi}（インデックス: {index}）")

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
