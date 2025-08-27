# tentyuusatsu_app.py
# UI は元の簡易版を踏襲しつつ、月干支・日干支の算出を安定化
# 立春前は「前年の前月（=12月節）」へずらす。日干支はカレンダー年・月で固定表を参照。

import streamlit as st
from datetime import datetime, date

from risshun_data import risshun_dict
from month_kanshi_index_dict import month_kanshi_index_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages

# 1〜60 に合わせた干支配列（index=1 が甲子）
KANSHI = [
    "",  # 0は使わない
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

def _wrap_1_60(n: int) -> int:
    """1..60 の範囲に正規化"""
    n = int(n)
    n = ((n - 1) % 60) + 1
    return n

def _get_month_index_from_any_key(y: int, m: int):
    """
    month_kanshi_index_dict が
    - {(year, month): idx} のタプルキー
    - {year: {month: idx}} の二重辞書
    - {"YYYY-MM": idx} / {"YYYYMM": idx} の文字列キー
    のどれでも拾えるように順に探す。
    戻り値: int or None
    """
    # 1) タプルキー
    k1 = (y, m)
    if k1 in month_kanshi_index_dict:
        try:
            return int(month_kanshi_index_dict[k1])
        except Exception:
            pass

    # 2) ネスト辞書
    if isinstance(month_kanshi_index_dict.get(y), dict) and m in month_kanshi_index_dict[y]:
        try:
            return int(month_kanshi_index_dict[y][m])
        except Exception:
            pass

    # 3) 文字列キー
    for key in (f"{y}-{m:02d}", f"{y}{m:02d}"):
        if key in month_kanshi_index_dict:
            try:
                return int(month_kanshi_index_dict[key])
            except Exception:
                pass

    return None

def get_year_kanshi(bd: date) -> str:
    """年干支（立春基準）。1984年=甲子を基準"""
    y = bd.year
    rs = risshun_dict.get(y)
    if rs and bd < rs:
        y -= 1
    idx = ((y - 1984) % 60) + 1
    return KANSHI[idx]

def get_month_kanshi(bd: date):
    """
    月干支（固定表＋立春処理）。
    立春前は「前年の前月（=12月節）」を参照する。
    例）1999/01/01 → 1998/12 の値を採用（= 甲子）
    戻り値: (干支名 or '該当なし', index or None, debug dict)
    """
    y, m = bd.year, bd.month
    rs = risshun_dict.get(y)
    if rs and bd < rs:
        # 立春前。前年の【前月】へずらす
        if m == 1:
            y -= 1
            m = 12
        else:
            y -= 1
            m -= 1

    idx = _get_month_index_from_any_key(y, m)
    if not idx:
        return "該当なし", None, {"hit": None, "year": y, "month": m}

    idx = _wrap_1_60(idx)
    return KANSHI[idx], idx, {"hit": (y, m)}

def get_day_kanshi(bd: date):
    """
    日干支。**カレンダー年・月**の固定表をそのまま使い、日にちを加算。
    ・テーブル値が 0 の場合は 60 とみなす（表の表現揺れに対応）
    戻り値: (干支名 or '該当なし', index or None, debug dict)
    """
    y, m, d = bd.year, bd.month, bd.day
    try:
        base = int(kanshi_index_table[y][m])
    except Exception:
        return "該当なし", None, {"hit": None}

    if base == 0:
        base = 60
    idx = base + d
    idx = _wrap_1_60(idx)
    return KANSHI[idx], idx, {"hit": (y, m), "base": base, "day": d, "calc_index": idx}

def tenchusatsu_from_index(idx: int) -> str:
    if idx is None:
        return "該当なし"
    if 51 <= idx <= 60 or idx == 0:
        return "子丑"
    elif 41 <= idx <= 50:
        return "寅卯"
    elif 31 <= idx <= 40:
        return "辰巳"
    elif 21 <= idx <= 30:
        return "午未"
    elif 11 <= idx <= 20:
        return "申酉"
    elif 1 <= idx <= 10:
        return "戌亥"
    return "不明"

# ---------------- UI（元の簡易版） ----------------
st.title("天中殺診断アプリ【簡易版】")

birth_date = st.date_input(
    "生年月日を入力してください（範囲：1900年〜2033年）",
    value=datetime(2000, 1, 1),
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2033, 12, 31),
)

if st.button("診断する"):
    year_k = get_year_kanshi(birth_date)
    month_k, month_idx, month_dbg = get_month_kanshi(birth_date)
    day_k, day_idx, day_dbg = get_day_kanshi(birth_date)

    st.markdown(f"### 年干支（立春基準）: {year_k}")
    st.markdown(f"### 月干支（固定表＋立春処理）: {month_k}（index: {month_idx if month_idx else '・'}）")
    st.markdown(f"### 日干支＆天中殺用数値: {day_k}（インデックス: {day_idx if day_idx else '・'}）")

    with st.expander("デバッグ情報"):
        st.write({"month": month_dbg, "day": day_dbg})

    if day_idx:
        ts = tenchusatsu_from_index(day_idx)
        st.markdown(f"### 天中殺: {ts}")
        msg = tentyuusatsu_messages.get(ts)
        if msg:
            for line in msg:
                st.markdown(f"- {line}")
        else:
            st.caption("該当メッセージなし")
    else:
        st.warning("この年の干支データは未登録のため、天中殺の診断ができません。")
