# tentyuusatsu_app.py  ——  簡易版・安定重視（ファイル名/他モジュールは変更しません）
# -----------------------------------------------------------
# 目的：
# - 年干支：立春基準での年跨ぎに対応（安定）
# - 月干支：立春境界＆欠損/表記ゆれに強い算出（最優先修正点）
# - 日干支：月初アンカーからの進み ＋ 欠損時フォールバック（最優先修正点）
# - UI：最小限の入力と検証出力、デバッグ展開パネル付き
#
# 既存モジュール（そのまま利用）：
#   risshun_data.risshun_dict（1900〜2033の立春日）
#   day_kanshi_dict.kanshi_index_table（各年・各月の「月初の干支インデックス」）
#   month_kanshi_index_dict.month_kanshi_index_dict（各年・各月の月干支データ）
#   tenchusatsu_messages.tentyuusatsu_messages（任意：天中殺メッセージ）
#
# 注意：
# - ファイル名・関数名は一切変更していません（要望順守）
# - 2月の立春境界（2/4 または 2/5）を確実に吸収
# - 文字列/数値/None/0 の混在、表記ゆれ（乙卯/己卯など）を許容して正規化
# - 欠損時は最大24ヶ月遡って補完
# -----------------------------------------------------------

import streamlit as st
import datetime as _dt
import calendar as _cal
import re as _re
from typing import Optional, Tuple

# === 既存ファイルのインポート（ファイル名は変更しません） ===
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict
try:
    # 任意（あれば使う）
    from tenchusatsu_messages import tentyuusatsu_messages
except Exception:
    tentyuusatsu_messages = None

# === 1〜60 の干支リスト（index=1..60 を保証） ===
# 先頭をダミー空文字にして、[1]が「甲子」になるようにしています。
kanshi_list = [
    "",  # index=0 を空に
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
]

# -----------------------------------------------------------
# 安定化ユーティリティ（他ファイル名・構造は変更しません）
# -----------------------------------------------------------

def _wrap60(n: int) -> int:
    """1..60 に正規化"""
    return ((int(n) - 1) % 60) + 1

def _build_kanshi_maps():
    """kanshi_list（1-based）から 名前→index の辞書を作成"""
    return {name: idx for idx, name in enumerate(kanshi_list) if idx > 0 and isinstance(name, str) and name}

_KANSHI_TO_IDX = _build_kanshi_maps()

def _to_index(val) -> Optional[int]:
    """
    値を 1..60 の index に正規化。
    - 数字（int/str）/ 干支名（例: '乙卯'）/ '乙卯(52)'様式 / None / 0 を吸収
    """
    if val in (None, "", 0, "0"):
        return None
    if isinstance(val, int):
        return _wrap60(val)
    if isinstance(val, str):
        s = val.strip()
        if s == "":
            return None
        # 干支名そのもの
        if s in _KANSHI_TO_IDX:
            return _KANSHI_TO_IDX[s]
        # “52” や “idx: 52” など
        m = _re.search(r"(\d+)", s)
        if m:
            return _wrap60(int(m.group(1)))
        # “乙卯(52)” のような形式
        for name, idx in _KANSHI_TO_IDX.items():
            if name in s:
                return idx
    return None

def _ymd(y: int, m: int, d: int = 1) -> _dt.date:
    return _dt.date(y, m, d)

def _prev_month(y: int, m: int) -> Tuple[int, int]:
    return (y - 1, 12) if m == 1 else (y, m - 1)

def _days_between(d1: _dt.date, d2: _dt.date) -> int:
    return (d2 - d1).days

def _get_risshun(y: int) -> _dt.date:
    """立春日を取得。欠損時は 2/4 をデフォルトに."""
    try:
        return risshun_dict[y]
    except Exception:
        return _dt.date(y, 2, 4)

# ---------- 日干支：堅牢化 ----------
def get_day_kanshi_index(y: int, m: int, d: int) -> int:
    """
    day_kanshi_dict のアンカー（各月1日の index）から日干支 index を算出。
    欠損/0/文字列でも動く。アンカー欠損時は、最大24か月遡って補完。
    """
    # 当月アンカー
    base = None
    try:
        base = kanshi_index_table.get(y, {}).get(m)
    except Exception:
        base = None
    anchor = _to_index(base)

    if anchor is not None:
        return _wrap60(anchor + (d - 1))

    # フォールバック：過去24か月で最初に見つかったアンカーから日数差で進める
    yy, mm = y, m
    for _ in range(24):
        b = None
        try:
            b = kanshi_index_table.get(yy, {}).get(mm)
        except Exception:
            b = None
        a = _to_index(b)
        if a is not None:
            anchor_date = _ymd(yy, mm, 1)
            target_date = _ymd(y, m, d)
            offset = _days_between(anchor_date, target_date)
            return _wrap60(a + offset)
        yy, mm = _prev_month(yy, mm)

    # データ欠損
    raise ValueError(f"day_kanshi_dict のアンカーが見つかりません（{y}-{m:02d}）。")

# ---------- 月干支：立春境界と欠損耐性 ----------
def _read_month_entry(y: int, m: int) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    month_kanshi_index_dict[y][m] の形状に寛容に対応する。
    戻り値: (この"月の"index, start_day, start_dayより前のindex)
    例:
      - 値が int/str なら (idx, None, None)
      - 値が dict なら { 'idx' or 'index' or 'kanshi', 'start' or 'start_day', 'prev_idx' or 'before' } を読む
    """
    try:
        v = month_kanshi_index_dict.get(y, {}).get(m)
    except Exception:
        v = None

    if v is None:
        return None, None, None

    if isinstance(v, dict):
        start_day = v.get("start") or v.get("start_day") or v.get("startDay") or v.get("boundary") or v.get("boundary_day")
        try:
            start_day = int(start_day) if start_day not in (None, "", 0, "0") else None
        except Exception:
            start_day = None
        idx = _to_index(v.get("idx") or v.get("index") or v.get("kanshi") or v.get("value"))
        prev_idx = _to_index(v.get("prev_idx") or v.get("before") or v.get("prev") or v.get("pre"))
        return idx, start_day, prev_idx

    # int/str の場合
    return _to_index(v), None, None

def get_month_kanshi_index(date_obj: _dt.date) -> int:
    """
    月干支 index を返す。2月の立春境界も安全に吸収。
    - データに 'start_day' がある月は、その日付で切替
    - 無い月でも 2月は risshun_dict[y] の日で前月/当月を切替
    - 前月 index が必要になった場合は再帰的に前月を参照（欠損時は更に遡る）
    """
    y, m, d = date_obj.year, date_obj.month, date_obj.day
    idx, start_day, prev_idx = _read_month_entry(y, m)

    # まず "start_day" で切り替えできる場合
    if start_day is not None:
        if d >= start_day:
            if idx is not None:
                return idx
        else:
            if prev_idx is not None:
                return prev_idx
            # 前月の index へフォールバック（必要なら更に遡る）
            py, pm = _prev_month(y, m)
            for _ in range(24):
                p_idx, p_start, p_prev = _read_month_entry(py, pm)
                if p_idx is not None:
                    return p_idx
                if p_prev is not None:
                    return p_prev
                py, pm = _prev_month(py, pm)

    # 2月の立春境界（start_day が未提供でも確実に吸収）
    if m == 2:
        r = _get_risshun(y)
        # 例：r.day が 4 または 5。未満なら前月
        if d < r.day:
            py, pm = _prev_month(y, m)
            for _ in range(24):
                p_idx, p_start, p_prev = _read_month_entry(py, pm)
                if p_idx is not None:
                    return p_idx
                if p_prev is not None:
                    return p_prev
                py, pm = _prev_month(py, pm)

    # 単純に今月の idx を返す（None ならエラー）
    if idx is not None:
        return idx

    raise ValueError(f"month_kanshi_index_dict のデータ不足: {y}-{m:02d}（start_day/前月含めて見つからず）。")

# ---------- 年干支（立春基準） ----------
def get_year_kanshi_index(date_obj: _dt.date) -> int:
    """
    1984年＝甲子（index=1）を基準に、立春で年を切替。
    """
    y, m, d = date_obj.year, date_obj.month, date_obj.day
    # 立春前は前年扱い
    r = _get_risshun(y)
    base_year = y - 1 if (m < r.month or (m == r.month and d < r.day)) else y
    # 1984年を index=1 のアンカーに
    return _wrap60((base_year - 1984) % 60 + 1)

# -----------------------------------------------------------
# UI（Streamlit）
# -----------------------------------------------------------

st.set_page_config(page_title="天中殺 診断 簡易版（立春・月日干支 安定算出）", page_icon="🀄", layout="centered")
st.title("天中殺 診断 簡易版")
st.caption("立春基準での年・月・日干支を安定算出（簡易版）。ファイル名/関数名は既存のまま。")

with st.form("input"):
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("生年月日（西暦）", value=_dt.date(2000, 1, 1), min_value=_dt.date(1900, 1, 1), max_value=_dt.date(2033, 12, 31))
    with col2:
        st.markdown("※ 立春前（2/4または2/5の前）は前年扱いになります。")
    submitted = st.form_submit_button("診断する")

if submitted:
    # 基本計算
    try:
        y_idx = get_year_kanshi_index(birth_date)
        y_name = kanshi_list[y_idx]
    except Exception as e:
        y_idx, y_name = None, None
        st.error(f"年干支の算出に失敗しました: {e}")

    try:
        m_idx = get_month_kanshi_index(birth_date)
        m_name = kanshi_list[m_idx]
    except Exception as e:
        m_idx, m_name = None, None
        st.error(f"月干支の算出に失敗しました: {e}")

    try:
        d_idx = get_day_kanshi_index(birth_date.year, birth_date.month, birth_date.day)
        d_name = kanshi_list[d_idx]
    except Exception as e:
        d_idx, d_name = None, None
        st.error(f"日干支の算出に失敗しました: {e}")

    # 表示
    st.subheader("算出結果")
    res = []
    if y_idx is not None:
        res.append(("年干支", y_name, y_idx))
    if m_idx is not None:
        res.append(("月干支", m_name, m_idx))
    if d_idx is not None:
        res.append(("日干支", d_name, d_idx))

    if res:
        st.table(
            {"区分": [r[0] for r in res], "干支": [r[1] for r in res], "インデックス(1-60)": [r[2] for r in res]}
        )

    # （任意）天中殺メッセージ表示：プロジェクト内のロジックに合わせてお使いください
    with st.expander("天中殺メッセージ（任意・簡易表示）", expanded=False):
        if tentyuusatsu_messages is None:
            st.info("`tenchusatsu_messages.py` が見つかれば、ここに表示できます。")
        else:
            # ここでは「年干支 index」等からのグループ判定ロジックが
            # プロジェクトに依存するため、例外安全に軽く試行のみ。
            try:
                # 例：tentyuusatsu_messages が dict で、キーに6グループ（'子丑','寅卯',...）がある前提
                # 実運用では、既存の “グループ判定” 関数を呼び出してください。
                # ここではプレースホルダ（何も表示できない場合はそっと案内）
                st.write("※ 既存の『天中殺グループ判定関数』をここで呼び出してください。")
                st.write("　例）group = detect_tenchusatsu_group(y_idx, m_idx, d_idx)")
                st.write("　　→ message = tentyuusatsu_messages[group]")
            except Exception as e:
                st.warning(f"天中殺メッセージの表示準備に失敗: {e}")

# -----------------------------------------------------------
# 検証用デバッグ（必要に応じて展開）
# -----------------------------------------------------------
with st.expander("デバッグ: 立春前後セルフチェック（2月境界）", expanded=False):
    samples = [
        _dt.date(2025, 2, 3),  # 立春前 → 前月想定
        _dt.date(2025, 2, 4),  # 立春当日（年により2/5の場合も）
        _dt.date(2021, 2, 3),
        _dt.date(2021, 2, 4),
    ]
    for d in samples:
        try:
            mi = get_month_kanshi_index(d)
            st.write(d.isoformat(), "→ 月干支:", kanshi_list[mi])
        except Exception as e:
            st.error(f"{d}: 月干支エラー: {e}")

    for d in samples:
        try:
            di = get_day_kanshi_index(d.year, d.month, d.day)
            st.write(d.isoformat(), "→ 日干支:", kanshi_list[di])
        except Exception as e:
            st.error(f"{d}: 日干支エラー: {e}")
