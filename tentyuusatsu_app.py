# tentyuusatsu_app.py
# UIは元の簡易版のまま。
# 月干支：固定辞書A方式（立春 前→(年-1,12) / 以後→(年,月) をそのまま引く。計算しない）
# 日干支：固定表A方式（kanshi_index_table[年][月] の月数値 + 日。0は60扱い。欠損は前月1日から+1補完）

import streamlit as st
from datetime import datetime, date, timedelta

from risshun_data import risshun_dict
from month_kanshi_index_dict import month_kanshi_index_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages

# ---------------- 干支テーブル（1..60） ----------------
# 配列名は既存互換のため kanshi_list も KANSHI も用意（同一オブジェクト）
kanshi_list = [
    "",  # 0は未使用
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]
KANSHI = kanshi_list  # 互換

# ---------------- 共通ユーティリティ ----------------
def _wrap_1_60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _kanshi_array():
    for name in ("kanshi_list", "KANSHI", "kanshi_data"):
        arr = globals().get(name)
        if isinstance(arr, list) and len(arr) >= 61:
            return arr
    return None

def _kanshi_name(idx):
    try:
        i = int(idx)
    except Exception:
        return "該当なし"
    arr = _kanshi_array()
    return arr[i] if arr and 1 <= i < len(arr) else "該当なし"

# どちらの呼称でも動くように
kanshi_name = _kanshi_name

def _as_date(x) -> date:
    """date_inputの戻り、str、datetime、pandas.Timestampなどをdateへ正規化"""
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    if hasattr(x, "year") and hasattr(x, "month") and hasattr(x, "day"):
        return date(int(getattr(x, "year")), int(getattr(x, "month")), int(getattr(x, "day")))
    if isinstance(x, str):
        s = x.strip().replace("年", "-").replace("月", "-").replace("日", "")
        s = s.replace("/", "-").replace(".", "-")
        return datetime.fromisoformat(s).date()
    raise TypeError(f"date型に変換できません: {type(x)}")

# ---------------- 年干支（立春基準） ----------------
def get_year_kanshi(birth_date) -> str:
    d = _as_date(birth_date)
    y = d.year
    rs = risshun_dict.get(y)
    if rs and d < rs:
        y -= 1
    idx = _wrap_1_60((y - 1984) % 60 + 1)  # 1984=甲子
    return kanshi_list[idx]

# ---------------- 月干支：固定辞書A方式 ----------------
def _setsuge_key(birth_date):
    """立春 前→(年-1,12)／以後→(年,月) を返す。"""
    d = _as_date(birth_date)
    y, m = d.year, d.month
    rs = risshun_dict.get(y)
    return (y - 1, 12) if (rs and d < rs) else (y, m)

def get_month_kanshi_index_fixed(birth_date):
    """month_kanshi_index_dict からそのまま取り出す（計算しない）。"""
    y, m = _setsuge_key(birth_date)
    v = month_kanshi_index_dict.get((y, m))
    if v is None:
        # 許可する唯一のフォールバック：{年:{月:idx}}
        try:
            v = month_kanshi_index_dict[y][m]
        except Exception:
            return None
    try:
        v = int(v)
    except Exception:
        return None
    if v == 0:
        v = 60
    return _wrap_1_60(v)

def get_month_kanshi(birth_date):
    """UIがこの名前で呼ぶのでラップして干支名も返す。"""
    idx = get_month_kanshi_index_fixed(birth_date)
    return (kanshi_name(idx), idx, {"key": _setsuge_key(birth_date)}) if idx else ("該当なし", None, {"key": None})

# ---------------- 日干支：固定表A方式 ----------------
def _day_anchor_from_table(year: int, month: int):
    """kanshi_index_table の '月数値'(1..60, 0は60扱い) を取得。"""
    # 1) 標準：dict[年][月]
    try:
        v = kanshi_index_table[year][month]
        v = int(v)
        return 60 if v == 0 else _wrap_1_60(v)
    except Exception:
        pass
    # 2) 互換：dict[(年,月)]
    try:
        v = kanshi_index_table[(year, month)]
        v = int(v)
        return 60 if v == 0 else _wrap_1_60(v)
    except Exception:
        pass
    # 3) 互換："YYYY-MM" / "YYYYMM"
    for k in (f"{year}-{month:02d}", f"{year}{month:02d}"):
        v = kanshi_index_table.get(k)
        if v is not None:
            v = int(v)
            return 60 if v == 0 else _wrap_1_60(v)
    return None

def _prev_month(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)

# ================= 日干支：1900-02-20(甲子)アンカーの60日周期 =================

def _jdn_ymd(y: int, m: int, d: int) -> int:
    """ユリウス通日（Fliegel–Van Flandern）。日付だけ使うのでタイムゾーンの影響なし。"""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045

def get_day_kanshi_from_table(birth_date):
    """
    固定表は使わず、1900-02-20 を 甲子(=index 1) として 60日周期で計算。
    ・閏年/各月の日数に依存せず、常にズレない。
    ・戻り値の形は既存どおり (干支名, index, debug)。
    """
    d = _as_date(birth_date)
    jdn = _jdn_ymd(d.year, d.month, d.day)
    jdn_ref = _jdn_ymd(1900, 2, 20)  # 甲子

    idx = ((jdn - jdn_ref) % 60) + 1  # 1..60
    return kanshi_name(idx), idx, {
        "method": "JDN60",
        "anchor": "1900-02-20(甲子)",
        "jdn": jdn,
        "delta_days": jdn - jdn_ref,
    }

# UI がこの名前で呼んでいる場合に合わせたラッパー（既存どおり）
def get_day_kanshi(birth_date):
    return get_day_kanshi_from_table(birth_date)

# ---------------- 天中殺グループ（6区分） ----------------
def tenchusatsu_from_index(idx: int | None) -> str:
    if idx is None:
        return "該当なし"
    if   1 <= idx <= 10: return "戌亥"
    elif 11 <= idx <= 20: return "申酉"
    elif 21 <= idx <= 30: return "午未"
    elif 31 <= idx <= 40: return "辰巳"
    elif 41 <= idx <= 50: return "寅卯"
    elif 51 <= idx <= 60: return "子丑"
    return "不明"

# ---------------- UI（簡易版そのまま） ----------------
st.title("天中殺診断アプリ【簡易版】")

birth_date = st.date_input(
    "生年月日を入力してください（範囲：1900年〜2033年）",
    value=datetime(2000, 1, 1),
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2033, 12, 31),
)

if st.button("診断する"):
    # 年・月・日
    year_k = get_year_kanshi(birth_date)
    month_k, month_idx, month_dbg = get_month_kanshi(birth_date)
    day_k, day_idx, day_dbg = get_day_kanshi(birth_date)

    st.markdown(f"### 年干支（立春基準）: {year_k}")
    st.markdown(f"### 月干支（固定表A方式）: {month_k}（index: {month_idx if month_idx else '・'}）")
    st.markdown(f"### 日干支＆天中殺用数値: {day_k}（インデックス: {day_idx if day_idx else '・'}）")

    with st.expander("デバッグ情報"):
        st.write({"month": month_dbg, "day": day_dbg})

    # 天中殺
    if day_idx:
        ts_group = tenchusatsu_from_index(day_idx)
        st.markdown(f"### 天中殺: {ts_group}")
        msg = tentyuusatsu_messages.get(ts_group) if isinstance(tentyuusatsu_messages, dict) else None
        if msg:
            for line in msg:
                st.markdown(f"- {line}")
        else:
            st.caption("該当メッセージなし")
    else:
        st.warning("この年の干支データは未登録のため、天中殺の診断ができません。")
