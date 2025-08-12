import streamlit as st
from datetime import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict
from tenchusatsu_messages import tentyuusatsu_messages

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

def get_month_kanshi_from_table(birth_date):
    """
    月干支：既存DB（月表）はタプルキー (年, 月) を最優先で参照。
    立春判定は年干支にのみ適用。月は“暦月”でキー参照（現行DBに合わせる）。
    """
    base_year = birth_date.year
    rs = risshun_dict.get(base_year)
    if rs and birth_date < rs:
        base_year -= 1

    # 最優先：タプルキー (年, 月)
    key_tuple = (base_year, birth_date.month)
    if key_tuple in month_kanshi_index_dict:
        idx = int(month_kanshi_index_dict[key_tuple])
        return kanshi_list[idx], idx

    # 念のための軽いフォールバック（壊さないため）
    try:
        idx = int(month_kanshi_index_dict[base_year][birth_date.month])
        return kanshi_list[idx], idx
    except Exception:
        return "該当なし", None

def get_day_kanshi_from_table(birth_date):
    """
    日干支：まず {年:{月:idx}} のネスト辞書を参照、
    見つからなければ (年, 月) タプルキーをフォールバック。
    取得した“その月の1日インデックス”に＋日（60超は折返し）。
    """
    base_year = birth_date.year
    rs = risshun_dict.get(base_year)
    if rs and birth_date < rs:
        base_year -= 1

    # ① ネスト辞書優先
    base_index = None
    try:
        base_index = int(kanshi_index_table[base_year][birth_date.month])
    except Exception:
        # ② タプルキーにフォールバック
        try:
            base_index = int(kanshi_index_table[(base_year, birth_date.month)])
        except Exception:
            return "該当なし", None

    idx = base_index + birth_date.day
    while idx > 60:
        idx -= 60
    return kanshi_list[idx], idx

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
        value=datetime(1972, 11, 20),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2033, 12, 31),
    )

    if st.button("診断する"):
        year_kanshi = get_year_kanshi_from_risshun(birth_date)
        month_kanshi, _ = get_month_kanshi_from_table(birth_date)
        day_kanshi, day_idx = get_day_kanshi_from_table(birth_date)

        # 表示順：年干支 → 月干支 → 日干支（インデックス付き）
        st.markdown(f"### 年干支（立春基準）：{year_kanshi}")
        st.markdown(f"### 月干支（立春基準・固定表）：{month_kanshi}")
        st.markdown(f"### 日干支＆天中殺用数値：{day_kanshi}（インデックス: {day_idx}）")

        if day_idx is None:
            st.warning("この月の干支データが未登録のため、天中殺の診断ができません。")
            return

        st.info("※ 表の月数値に日を足して求める伝統的な方法に基づいた計算です。")

        tenchusatsu = get_tenchusatsu_from_day_index(day_idx)
        st.markdown(f"### 天中殺：{tenchusatsu}")

        message = tentyuusatsu_messages.get(tenchusatsu)
        if message:
            for line in message:
                st.markdown(f"- {line}")
        else:
            st.warning("天中殺に対応するメッセージが見つかりませんでした。")

if __name__ == "__main__":
    main()
