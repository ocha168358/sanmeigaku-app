import streamlit as st
from datetime import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict
from tenchusatsu_messages import tentyuusatsu_messages

# 干支リスト
kanshi_list = [
    "",  # index=0
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

# ========= 基本ユーティリティ =========
def _wrap60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _get_risshun(y: int):
    return risshun_dict.get(y, datetime(y, 2, 4).date())

def _prev_month(y: int, m: int):
    return (y-1, 12) if m == 1 else (y, m-1)

# ========= 年干支 =========
def get_year_kanshi_from_table(birth_date: datetime):
    y, m, d = birth_date.year, birth_date.month, birth_date.day
    r = _get_risshun(y)
    base_year = y if (birth_date >= r) else (y - 1)
    idx = _wrap60((base_year - 1984) % 60 + 1)  # 1984=甲子を基準
    return kanshi_list[idx], idx, {"base_year": base_year}

# ========= 月干支 =========
def get_setsuge_month(birth_date: datetime) -> int:
    """節月を返す（立春前なら12、以降は暦月と同じ）"""
    y, m, d = birth_date.year, birth_date.month, birth_date.day
    r = _get_risshun(y)
    if m == 1:  # 1月は必ず12月節
        return 12
    if m == 2 and d < r.day:
        return 12
    return m

def get_month_kanshi_from_table(birth_date: datetime):
    y, m, d = birth_date.year, birth_date.month, birth_date.day
    r = _get_risshun(y)
    base_year = y if (birth_date >= r) else (y - 1)
    setsu_no = get_setsuge_month(birth_date)

    # 節月を最優先で参照
    candidates = [
        (base_year, setsu_no),
        (y, m),
        (base_year, m),
    ]
    for key in candidates:
        idx = month_kanshi_index_dict.get(key)
        if isinstance(idx, str):
            try: idx = int(idx)
            except: pass
        if isinstance(idx, int) and 1 <= idx <= 60:
            return kanshi_list[idx], idx, {"hit": key, "base_year": base_year, "setsu_no": setsu_no}

    # ダメなら文字列キーも探す
    cand_str = [
        f"{base_year}-{setsu_no:02d}", f"{y}-{m:02d}",
        f"{base_year}{setsu_no:02d}", f"{y}{m:02d}",
    ]
    for k in cand_str:
        idx = month_kanshi_index_dict.get(k)
        if idx is not None:
            try: idx = int(idx)
            except: pass
            if isinstance(idx, int) and 1 <= idx <= 60:
                return kanshi_list[idx], idx, {"hit": k, "base_year": base_year, "setsu_no": setsu_no}

    return "該当なし", None, {"hit": None, "base_year": base_year, "setsu_no": setsu_no}

# ========= 日干支 =========
def get_day_kanshi_from_table(birth_date: datetime):
    y, m, d = birth_date.year, birth_date.month, birth_date.day

    def _norm(v):
        try:
            v = int(v)
            return v if 1 <= v <= 60 else None
        except: return None

    base_index = _norm(kanshi_index_table.get(y, {}).get(m))
    if base_index is not None:
        day_index = ((base_index - 1) + (d - 1)) % 60 + 1
        return kanshi_list[day_index], day_index, {"hit": (y, m), "base_index": base_index}

    # 前月に遡って補完
    yy, mm = y, m
    for _ in range(36):
        yy, mm = _prev_month(yy, mm)
        base_index = _norm(kanshi_index_table.get(yy, {}).get(mm))
        if base_index is not None:
            anchor = datetime(yy, mm, 1)
            delta = (birth_date - anchor).days
            day_index = ((base_index - 1) + delta) % 60 + 1
            return kanshi_list[day_index], day_index, {"hit": (yy, mm), "base_index": base_index, "delta_days": delta}

    return "該当なし", None, {"hit": None}

# ========= Streamlit UI =========
st.title("天中殺診断アプリ（簡易版）")

birth_date = st.date_input("生年月日を入力してください", value=datetime(2000,1,1))

if st.button("診断する"):
    # 年干支
    year_name, year_idx, year_info = get_year_kanshi_from_table(birth_date)
    # 月干支
    month_name, month_idx, month_info = get_month_kanshi_from_table(birth_date)
    # 日干支
    day_name, day_idx, day_info = get_day_kanshi_from_table(birth_date)

    st.subheader("算出結果")
    st.write("年干支:", year_name, year_idx)
    st.write("月干支:", month_name, month_idx)
    st.write("日干支:", day_name, day_idx)

    st.subheader("天中殺メッセージ")
    if year_idx:
        tensatsu = tentyuusatsu_messages.get(year_idx % 6)  # 仮ロジック、必要なら修正
        st.write(tensatsu if tensatsu else "該当メッセージなし")
