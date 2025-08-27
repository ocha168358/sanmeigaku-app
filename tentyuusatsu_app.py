import streamlit as st
from datetime import datetime, date, timedelta
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict
from tenchusatsu_messages import tentyuusatsu_messages

# 干支リスト（index=1..60、先頭はダミー）
kanshi_list = [
    "",
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

# ================= 基本ユーティリティ =================

def _wrap60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _get_risshun(y: int) -> date:
    # 立春が未収録の年は 2/4 を既定
    return risshun_dict.get(y, date(y, 2, 4))

def _prev_month(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)

def _as_date(x) -> date:
    """
    入力を必ず datetime.date に正規化。
    - datetime/date: そのまま date に
    - str: 'YYYY-MM-DD' / 'YYYY/MM/DD' / 'YYYY.MM.DD' などをゆるく対応
    """
    if isinstance(x, date):
        return x
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, str):
        s = x.strip()
        s = s.replace("年", "-").replace("月", "-").replace("日", "")
        s = s.replace("/", "-").replace(".", "-")
        # 例: 1972-11-20
        return datetime.fromisoformat(s).date()
    raise TypeError(f"date型に変換できません: {type(x)}")

# ================= 年干支 =================

def get_year_kanshi_from_table(birth_date) -> tuple[str, int | None, dict]:
    d: date = _as_date(birth_date)
    r = _get_risshun(d.year)
    base_year = d.year if (d >= r) else (d.year - 1)
    idx = _wrap60((base_year - 1984) % 60 + 1)  # 1984=甲子をアンカー
    return kanshi_list[idx], idx, {"base_year": base_year}

# ================= 月干支（節月優先＋立春補正） =================

def get_setsuge_month(birth_date) -> int:
    d: date = _as_date(birth_date)
    r = _get_risshun(d.year)
    if d.month == 1:
        return 12
    if d.month == 2 and d < r:
        return 12
    return d.month

def _coerce_idx(idx):
    if idx is None:
        return None
    if isinstance(idx, int):
        return idx if 1 <= idx <= 60 else None
    if isinstance(idx, str):
        try:
            v = int(idx)
            return v if 1 <= v <= 60 else None
        except Exception:
            return None
    return None

def get_month_kanshi_from_table(birth_date) -> tuple[str, int | None, dict]:
    d: date = _as_date(birth_date)
    r = _get_risshun(d.year)
    base_year = d.year if (d >= r) else (d.year - 1)
    setsu_no = get_setsuge_month(d)

    # 1) 節月キー最優先 → (base_year, setsu_no)
    for key in [(base_year, setsu_no), (d.year, d.month), (base_year, d.month)]:
        idx = _coerce_idx(month_kanshi_index_dict.get(key))
        if idx:
            return kanshi_list[idx], idx, {"hit": key, "base_year": base_year, "setsu_no": setsu_no}

    # 2) 文字列キー（"YYYY-MM" / "YYYYMM"）
    for k in [f"{base_year}-{setsu_no:02d}", f"{d.year}-{d.month:02d}",
              f"{base_year}{setsu_no:02d}", f"{d.year}{d.month:02d}"]:
        idx = _coerce_idx(month_kanshi_index_dict.get(k))
        if idx:
            return kanshi_list[idx], idx, {"hit": k, "base_year": base_year, "setsu_no": setsu_no}

    # 3) 見つからない（未設定）
    return "該当なし", None, {"hit": None, "base_year": base_year, "setsu_no": setsu_no}

# ================= 日干支（暦年・暦月アンカー＋欠損補完） =================

def _norm_1to60(v):
    try:
        v = int(v)
        return v if 1 <= v <= 60 else None
    except Exception:
        return None

def get_day_kanshi_from_table(birth_date) -> tuple[str, int | None, dict]:
    d: date = _as_date(birth_date)
    y, m = d.year, d.month

    # 1) 暦年・暦月の1日インデックスを素直に参照
    base_index = _norm_1to60(kanshi_index_table.get(y, {}).get(m))
    if base_index is not None:
        day_index = _wrap60(base_index + (d.day - 1))
        return kanshi_list[day_index], day_index, {"hit": (y, m), "base_index": base_index}

    # 2) 欠損/0なら前月に遡って補完（最大36ヶ月）
    yy, mm = y, m
    for _ in range(36):
        yy, mm = _prev_month(yy, mm)
        base_index = _norm_1to60(kanshi_index_table.get(yy, {}).get(mm))
        if base_index is not None:
            anchor = date(yy, mm, 1)
            delta = (d - anchor).days  # アンカーからの経過日数（1日なら0）
            day_index = _wrap60(base_index + delta)
            return kanshi_list[day_index], day_index, {"hit": (yy, mm), "base_index": base_index, "delta_days": delta}

    # 3) 見つからない（未設定）
    return "該当なし", None, {"hit": None}

# ===================== Streamlit UI（元のまま最小修正） =====================

st.title("天中殺診断アプリ（簡易版）")

# 既定値：2000/01/01（環境差吸収のため date 指定）
birth_date = st.date_input("生年月日を入力してください", value=date(2000, 1, 1))

if st.button("診断する"):
    # 年干支
    year_name, year_idx, year_info = get_year_kanshi_from_table(birth_date)
    # 月干支
    month_name, month_idx, month_info = get_month_kanshi_from_table(birth_date)
    # 日干支
    day_name, day_idx, day_info = get_day_kanshi_from_table(birth_date)

    st.subheader("算出結果")
    st.write("年干支:", year_name, year_idx if year_idx else "—")
    st.write("月干支:", month_name, month_idx if month_idx else "—")
    st.write("日干支:", day_name, day_idx if day_idx else "—")

    st.subheader("天中殺メッセージ")
    # ※ ここは各自のロジックに合わせてください（仮に年干支indexのmodなど）
    try:
        if year_idx is not None and isinstance(tentyuusatsu_messages, dict):
            group_key = year_idx % 6  # 仮
            msg = tentyuusatsu_messages.get(group_key)
            st.write(msg if msg else "該当メッセージなし")
        else:
            st.write("該当メッセージなし")
    except Exception:
        st.write("該当メッセージなし")
