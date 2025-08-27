# tentyuusatsu_app.py  —— 最小UI＋安定ロジック（他ファイル名は変更しません）

import streamlit as st
import datetime as _dt
import re as _re
from typing import Optional, Tuple

# 既存ファイル（そのまま使用）
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict
try:
    from tenchusatsu_messages import tentyuusatsu_messages  # 使わない場合もあるのでtry
except Exception:
    tentyuusatsu_messages = None

# 干支リスト（index=1..60）
kanshi_list = [
    "",
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

# ============ 安定化ユーティリティ（内部のみ、他ファイルは変更なし） ============

def _wrap60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _build_kanshi_maps():
    return {name: idx for idx, name in enumerate(kanshi_list) if idx > 0 and isinstance(name, str) and name}

_KANSHI_TO_IDX = _build_kanshi_maps()

def _to_index(val) -> Optional[int]:
    """数値/干支名/混在文字列/None/0 を 1..60 に正規化"""
    if val in (None, "", 0, "0"):
        return None
    if isinstance(val, int):
        return _wrap60(val)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        if s in _KANSHI_TO_IDX:
            return _KANSHI_TO_IDX[s]
        m = _re.search(r"(\d+)", s)
        if m:
            return _wrap60(int(m.group(1)))
        for name, idx in _KANSHI_TO_IDX.items():
            if name in s:
                return idx
    return None

def _prev_month(y: int, m: int) -> Tuple[int, int]:
    return (y - 1, 12) if m == 1 else (y, m - 1)

def _ymd(y: int, m: int, d: int = 1) -> _dt.date:
    return _dt.date(y, m, d)

def _days_between(d1: _dt.date, d2: _dt.date) -> int:
    return (d2 - d1).days

def _get_risshun(y: int) -> _dt.date:
    try:
        return risshun_dict[y]
    except Exception:
        return _dt.date(y, 2, 4)  # 予備

# ---- 年干支（立春基準） ----
def get_year_kanshi_index(date_obj: _dt.date) -> int:
    y, m, d = date_obj.year, date_obj.month, date_obj.day
    r = _get_risshun(y)
    base_year = y - 1 if (m < r.month or (m == r.month and d < r.day)) else y
    return _wrap60((base_year - 1984) % 60 + 1)  # 1984=甲子をインデックス1のアンカー

# ---- 日干支：月初アンカーからの進み＋欠損フォールバック ----
def get_day_kanshi_index(y: int, m: int, d: int) -> int:
    # 当月アンカー
    anchor = _to_index(kanshi_index_table.get(y, {}).get(m))
    if anchor is not None:
        return _wrap60(anchor + (d - 1))
    # 最大120ヶ月遡って補完（2年の範囲を安全に超える）
    yy, mm = y, m
    for _ in range(120):
        v = _to_index(kanshi_index_table.get(yy, {}).get(mm))
        if v is not None:
            offset = _days_between(_ymd(yy, mm, 1), _ymd(y, m, d))
            return _wrap60(v + offset)
        yy, mm = _prev_month(yy, mm)
    # どうしても見つからない場合
    raise ValueError(f"day_kanshi_dict アンカー欠損（{y}-{m:02d}）。")

# ---- 月干支：立春境界＋欠損耐性 ----
def _read_month_entry(y: int, m: int):
    """戻り値: (this_idx, start_day, prev_idx) いずれも Optional[int]"""
    v = month_kanshi_index_dict.get(y, {}).get(m)
    if v is None:
        return None, None, None
    if isinstance(v, dict):
        start_day = v.get("start") or v.get("start_day") or v.get("startDay") or v.get("boundary") or v.get("boundary_day")
        try:
            start_day = int(start_day) if start_day not in (None, "", 0, "0") else None
        except Exception:
            start_day = None
        this_idx = _to_index(v.get("idx") or v.get("index") or v.get("kanshi") or v.get("value"))
        prev_idx = _to_index(v.get("prev_idx") or v.get("before") or v.get("prev") or v.get("pre"))
        return this_idx, start_day, prev_idx
    # int/str
    return _to_index(v), None, None

def get_month_kanshi_index(date_obj: _dt.date) -> int:
    y, m, d = date_obj.year, date_obj.month, date_obj.day
    this_idx, start_day, prev_idx = _read_month_entry(y, m)

    # 1) start_day がある場合はそれで切替
    if start_day is not None:
        if d >= start_day and this_idx is not None:
            return this_idx
        if d < start_day:
            if prev_idx is not None:
                return prev_idx
            # 前月を遡って探す（最大24ヶ月）
            py, pm = _prev_month(y, m)
            for _ in range(24):
                p_idx, p_start, p_prev = _read_month_entry(py, pm)
                if p_idx is not None:
                    return p_idx
                if p_prev is not None:
                    return p_prev
                py, pm = _prev_month(py, pm)

    # 2) 2月は立春日で切替（start_dayが無い場合の安全弁）
    if m == 2:
        r = _get_risshun(y)
        if d < r.day:
            py, pm = _prev_month(y, m)
            for _ in range(24):
                p_idx, p_start, p_prev = _read_month_entry(py, pm)
                if p_idx is not None:
                    return p_idx
                if p_prev is not None:
                    return p_prev
                py, pm = _prev_month(py, pm)

    # 3) そのほか：今月の値があれば採用。無ければ長めに遡ってとにかく拾う
    if this_idx is not None:
        return this_idx

    py, pm = _prev_month(y, m)
    for _ in range(120):  # データ薄い年向けに広めに探索
        p_idx, p_start, p_prev = _read_month_entry(py, pm)
        if p_idx is not None:
            return p_idx
        if p_prev is not None:
            return p_prev
        py, pm = _prev_month(py, pm)

    # 見つからない場合はエラー（UI側で握りつぶして「未設定」表示）
    raise ValueError(f"month_kanshi_index_dict データ不足: {y}-{m:02d}。")

# ============ ここから UI（最小） ============

st.set_page_config(page_title="天中殺 診断（簡易版）", layout="centered")

st.header("天中殺 診断（簡易版）")
with st.form("f"):
    birth = st.date_input("生年月日（西暦）", value=_dt.date(2000,1,1), min_value=_dt.date(1900,1,1), max_value=_dt.date(2033,12,31))
    ok = st.form_submit_button("診断する")

if ok:
    # 年・月・日 干支
    def _safe(fn, *a, **kw):
        try:
            return fn(*a, **kw), None
        except Exception as e:
            return None, str(e)

    y_idx, y_err = _safe(get_year_kanshi_index, birth)
    m_idx, m_err = _safe(get_month_kanshi_index, birth)
    d_idx, d_err = _safe(get_day_kanshi_index, birth.year, birth.month, birth.day)

    st.subheader("算出結果")
    rows = []
    if y_idx is not None:
        rows.append(("年干支", kanshi_list[y_idx], y_idx))
    else:
        rows.append(("年干支", "未設定", "-"))

    if m_idx is not None:
        rows.append(("月干支", kanshi_list[m_idx], m_idx))
    else:
        rows.append(("月干支", "未設定", "-"))

    if d_idx is not None:
        rows.append(("日干支", kanshi_list[d_idx], d_idx))
    else:
        rows.append(("日干支", "未設定", "-"))

    st.table({"区分":[r[0] for r in rows], "干支":[r[1] for r in rows], "Index":[r[2] for r in rows]})

    # 必要最小限のエラー表示（UIを汚さない）
    if any([y_err, m_err, d_err]):
        with st.expander("詳細（計算時の注意）", expanded=False):
            if y_err: st.write("年干支:", y_err)
            if m_err: st.write("月干支:", m_err)
            if d_err: st.write("日干支:", d_err)
