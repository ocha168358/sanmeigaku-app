import streamlit as st
import datetime

# --- 立春データ（1925〜2033年）
risshun_dict = {
    1925: datetime.date(1925, 2, 4), 1926: datetime.date(1926, 2, 5), 1927: datetime.date(1927, 2, 4),
    1928: datetime.date(1928, 2, 5), 1929: datetime.date(1929, 2, 4), 1930: datetime.date(1930, 2, 4),
    1931: datetime.date(1931, 2, 4), 1932: datetime.date(1932, 2, 5), 1933: datetime.date(1933, 2, 4),
    1934: datetime.date(1934, 2, 4), 1935: datetime.date(1935, 2, 4), 1936: datetime.date(1936, 2, 5),
    1937: datetime.date(1937, 2, 4), 1938: datetime.date(1938, 2, 4), 1939: datetime.date(1939, 2, 4),
    1940: datetime.date(1940, 2, 5), 1941: datetime.date(1941, 2, 4), 1942: datetime.date(1942, 2, 4),
    1943: datetime.date(1943, 2, 4), 1944: datetime.date(1944, 2, 5), 1945: datetime.date(1945, 2, 4),
    1946: datetime.date(1946, 2, 4), 1947: datetime.date(1947, 2, 4), 1948: datetime.date(1948, 2, 5),
    1949: datetime.date(1949, 2, 4), 1950: datetime.date(1950, 2, 4), 1951: datetime.date(1951, 2, 4),
    1952: datetime.date(1952, 2, 5), 1953: datetime.date(1953, 2, 4), 1954: datetime.date(1954, 2, 4),
    1955: datetime.date(1955, 2, 4), 1956: datetime.date(1956, 2, 5), 1957: datetime.date(1957, 2, 4),
    1958: datetime.date(1958, 2, 4), 1959: datetime.date(1959, 2, 4), 1960: datetime.date(1960, 2, 5),
    1961: datetime.date(1961, 2, 4), 1962: datetime.date(1962, 2, 4), 1963: datetime.date(1963, 2, 4),
    1964: datetime.date(1964, 2, 5), 1965: datetime.date(1965, 2, 4), 1966: datetime.date(1966, 2, 4),
    1967: datetime.date(1967, 2, 4), 1968: datetime.date(1968, 2, 5), 1969: datetime.date(1969, 2, 4),
    1970: datetime.date(1970, 2, 4), 1971: datetime.date(1971, 2, 4), 1972: datetime.date(1972, 2, 5),
    1973: datetime.date(1973, 2, 4), 1974: datetime.date(1974, 2, 4), 1975: datetime.date(1975, 2, 4),
    1976: datetime.date(1976, 2, 5), 1977: datetime.date(1977, 2, 4), 1978: datetime.date(1978, 2, 4),
    1979: datetime.date(1979, 2, 4), 1980: datetime.date(1980, 2, 5), 1981: datetime.date(1981, 2, 4),
    1982: datetime.date(1982, 2, 4), 1983: datetime.date(1983, 2, 4), 1984: datetime.date(1984, 2, 5),
    1985: datetime.date(1985, 2, 4), 1986: datetime.date(1986, 2, 4), 1987: datetime.date(1987, 2, 4),
    1988: datetime.date(1988, 2, 4), 1989: datetime.date(1989, 2, 4), 1990: datetime.date(1990, 2, 4),
    1991: datetime.date(1991, 2, 4), 1992: datetime.date(1992, 2, 4), 1993: datetime.date(1993, 2, 4),
    1994: datetime.date(1994, 2, 4), 1995: datetime.date(1995, 2, 4), 1996: datetime.date(1996, 2, 4),
    1997: datetime.date(1997, 2, 4), 1998: datetime.date(1998, 2, 4), 1999: datetime.date(1999, 2, 4),
    2000: datetime.date(2000, 2, 4), 2001: datetime.date(2001, 2, 4), 2002: datetime.date(2002, 2, 4),
    2003: datetime.date(2003, 2, 4), 2004: datetime.date(2004, 2, 4), 2005: datetime.date(2005, 2, 4),
    2006: datetime.date(2006, 2, 4), 2007: datetime.date(2007, 2, 4), 2008: datetime.date(2008, 2, 4),
    2009: datetime.date(2009, 2, 4), 2010: datetime.date(2010, 2, 4), 2011: datetime.date(2011, 2, 4),
    2012: datetime.date(2012, 2, 4), 2013: datetime.date(2013, 2, 4), 2014: datetime.date(2014, 2, 4),
    2015: datetime.date(2015, 2, 4), 2016: datetime.date(2016, 2, 4), 2017: datetime.date(2017, 2, 4),
    2018: datetime.date(2018, 2, 4), 2019: datetime.date(2019, 2, 4), 2020: datetime.date(2020, 2, 4),
    2021: datetime.date(2021, 2, 3), 2022: datetime.date(2022, 2, 4), 2023: datetime.date(2023, 2, 4),
    2024: datetime.date(2024, 2, 4), 2025: datetime.date(2025, 2, 3), 2026: datetime.date(2026, 2, 4),
    2027: datetime.date(2027, 2, 4), 2028: datetime.date(2028, 2, 4), 2029: datetime.date(2029, 2, 3),
    2030: datetime.date(2030, 2, 4), 2031: datetime.date(2031, 2, 4), 2032: datetime.date(2032, 2, 4),
    2033: datetime.date(2033, 2, 3)
}

#--- 干支計算関数（立春考慮）
def get_eto(birth_date):
    year = birth_date.year
    if birth_date < risshun_dict.get(year, datetime.date(year, 2, 4)):
        year -= 1
    eto_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    eto = eto_list[(year - 1924) % 12]
    return eto

# --- 天中殺判定関数
def get_tentyuusatsu(eto):
    tentyuu_map = {
        "子": "午未", "丑": "午未",
        "寅": "申酉", "卯": "申酉",
        "辰": "戌亥", "巳": "戌亥",
        "午": "子丑", "未": "子丑",
        "申": "寅卯", "酉": "寅卯",
        "戌": "辰巳", "亥": "辰巳",
    }
    return tentyuu_map.get(eto, "")

# --- 天中殺の意味メッセージ
tentyuusatsu_messages = {
    "子丑": [
        "欠けているもの：「家系」「居場所」「帰る場所としての安定」",
        "あなたは、家庭や先祖との縁が薄く、家に対して違和感を抱きやすい宿命があります。",
        "組織やグループでも“自分の居場所がない”と感じることがあるかもしれません。",
        "魂の成長に必要なのは、自分自身が“誰かの帰る場所”になる覚悟。",
        "「私はここにいていい」と、自分の存在に許可を出しましょう。"
    ],
    "寅卯": [
        "欠けているもの：「他者との共鳴」「対人の調和」",
        "強い信念を持ち、自分を貫く力はありますが、孤立しやすい傾向も。",
        "他人の意見に心を開くことで、新しい可能性が拓かれます。",
        "魂の成長に必要なのは、“共に創る”という意識。",
        "一人で背負わず、共鳴・共感できる仲間を信じましょう。"
    ],
    "辰巳": [
        "欠けているもの：「権威」「地位」「名誉」",
        "表舞台に立つことへの抵抗感があるかもしれません。",
        "目立たず控えめな人生を選びやすい傾向がありますが、それが自己制限となる場合も。",
        "魂の成長に必要なのは、“堂々と光を浴びる勇気”。",
        "「自分にはその価値がある」と信じて、舞台に立ちましょう。"
    ],
    "午未": [
        "欠けているもの：「目下」「子ども」「感情の共有」",
        "年下や部下、子どもとの関係に課題を持ちやすい宿命です。",
        "感情よりも理性で判断する傾向が強く、冷たく思われることも。",
        "魂の成長に必要なのは、“情熱を見守る愛”。",
        "管理より信頼を、支配より共感を意識しましょう。"
    ],
    "申酉": [
        "欠けているもの：「現実的な成果」「お金」「物質」",
        "理想主義的な発想になりがちで、現実面での苦労を感じやすい宿命です。",
        "地に足をつけること、経済的自立への意識が必要です。",
        "魂の成長に必要なのは、“地道な積み上げ”。",
        "夢を現実にするための具体的な行動を大切にしましょう。"
    ],
    "戌亥": [
        "欠けているもの：「直感」「スピリチュアル」「非論理の世界」",
        "感性や目に見えないものへの感受性が弱く、損得や理屈に偏りがちです。",
        "合理的であることに価値を置く一方、心の声を無視しやすい傾向も。",
        "魂の成長に必要なのは、“見えない力を信じること”。",
        "心で感じること、直感で動くこともあなたの大切な武器になります。"
    ]
}

# --- Streamlit UI
st.title("天中殺 診断アプリ（立春精密対応）")
birth_date = st.date_input("生年月日を入力")
if st.button("診断する") and birth_date:
    eto = get_eto(birth_date)
    tentyuu = get_tentyuusatsu(eto)
    st.write(f"あなたの干支：{eto}年生まれ")
    st.write(f"天中殺：{tentyuu}")
    if tentyuu in tentyuusatsu_messages:
        for line in tentyuusatsu_messages[tentyuu]:
            st.write(line)
    else:
        st.warning("この天中殺には現在、メッセージが登録されていません。")
