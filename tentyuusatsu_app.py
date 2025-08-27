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

# --- 追加: 辞書読み取りのユーティリティ（tentyuusatsu_app.py 内） ---
def _wrap60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _setsuge_key(birth_date):
    """節月（立春基準）で参照する (year, month) を返す。"""
    y, m = birth_date.year, birth_date.month
    rs = risshun_dict.get(y)
    return (y - 1, 12) if (rs and birth_date < rs) else (y, m)

def get_month_kanshi_index_fixed(birth_date):
    """固定辞書から月干支インデックス(1..60)を取得。計算しない。"""
    y, m = _setsuge_key(birth_date)

    # まず (年, 月) を見る
    v = month_kanshi_index_dict.get((y, m))
    if v is None:
        # フォールバック：{年:{月:idx}} 形式
        try:
            v = month_kanshi_index_dict[y][m]
        except Exception:
            return None

    try:
        v = int(v)   # 文字列なら int に
    except Exception:
        return None

    if v == 0:       # 0 は 60 に丸め
        v = 60
    return _wrap60(v)  # 念のため 1..60 へ

def get_month_kanshi_name_fixed(birth_date):
    idx = get_month_kanshi_index_fixed(birth_date)
    return kanshi_list[idx] if idx else "該当なし"

# 既存コードが get_month_kanshi(...) を呼んでいる場合のラッパー
def get_month_kanshi(birth_date):
    idx = get_month_kanshi_index_fixed(birth_date)
    return (_kanshi_name(idx), idx, {"key": _setsuge_key(birth_date)}) if idx else ("該当なし", None, {"key": None})

def _anchor_idx(y: int, m: int):
    try:
        v = kanshi_index_table.get(y, {}).get(m)
        if v in (None, "", 0, "0"):   # 0/None は欠損扱い
            return None
        return _wrap60(int(v))
    except Exception:
        return None

def kanshi_name(idx):
    try:
        i = int(idx)
    except Exception:
        return "該当なし"
    for name in ("kanshi_list", "KANSHI", "kanshi_data"):
        arr = globals().get(name)
        if isinstance(arr, list) and 1 <= i < len(arr):
            return arr[i]
    return "該当なし"

# ---- 日干支（固定表A：day_kanshi_dict をそのまま使う） ----
def _day_anchor_from_table(year: int, month: int):
    """day_kanshi_dict の '月数値'(1..60, 0は60扱い) を取り出す。
    形式ゆらぎに合わせて、[年][月] → [(年, 月)] → "YYYY-MM"/"YYYYMM" の順で見る。
    """
    # 1) ネスト辞書: dict[年][月]
    try:
        v = kanshi_index_table[year][month]
        v = int(v)
        return 60 if v == 0 else v
    except Exception:
        pass

    # 2) タプルキー: dict[(年, 月)]
    try:
        v = kanshi_index_table[(year, month)]
        v = int(v)
        return 60 if v == 0 else v
    except Exception:
        pass

    # 3) 文字列キー
    for k in (f"{year}-{month:02d}", f"{year}{month:02d}"):
        v = kanshi_index_table.get(k)
        if v is not None:
            v = int(v)
            return 60 if v == 0 else v

    return None

def get_day_kanshi_from_table(birth_date):
    """固定表Aの『月数値』＋『日』で日干支を出す（計算は最小限、立春補正なし）"""
    y, m, d = birth_date.year, birth_date.month, birth_date.day
    base = _day_anchor_from_table(y, m)
    dbg = {"hit": (y, m), "base": base, "day": d}

    if base is None:
        # データ未整備時
        return "該当なし", None, dbg

    idx = base + d
    while idx > 60:
        idx -= 60
    return kanshi_list[idx], idx, dbg

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
