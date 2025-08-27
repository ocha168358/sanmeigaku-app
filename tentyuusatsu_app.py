import streamlit as st
from datetime import datetime, date, timedelta
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table
from tenchusatsu_messages import tentyuusatsu_messages
from month_kanshi_index_dict import month_kanshi_index_dict  # 月干支の固定表（タプルキー）

# 1番目を空欄にして index を 1..60 に合わせる
kanshi_list = [
    "",
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

# ---------------- 基本ユーティリティ ----------------
def _wrap60(n: int) -> int:
    return ((int(n) - 1) % 60) + 1

def _as_date(x) -> date:
    """入力を必ず date に正規化（str, datetime, pandas.Timestamp なども受ける）"""
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    # year/month/day 属性があれば使う
    if hasattr(x, "year") and hasattr(x, "month") and hasattr(x, "day"):
        return date(int(getattr(x, "year")), int(getattr(x, "month")), int(getattr(x, "day")))
    if isinstance(x, str):
        s = x.strip().replace("年", "-").replace("月", "-").replace("日", "")
        s = s.replace("/", "-").replace(".", "-")
        return datetime.fromisoformat(s).date()
    if isinstance(x, (list, tuple)) and len(x) >= 3:
        return date(int(x[0]), int(x[1]), int(x[2]))
    raise TypeError(f"date型に変換できません: {type(x)}")

def _get_risshun(y: int) -> date:
    return risshun_dict.get(y, date(y, 2, 4))

def _prev_month(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)

# ---------------- 年干支（立春基準） ----------------
def get_year_kanshi_from_risshun(birth_date):
    d = _as_date(birth_date)
    year = d.year
    rs = _get_risshun(year)
    if d < rs:
        year -= 1
    idx = _wrap60((year - 1984) % 60 + 1)  # 1984=甲子をアンカー
    return kanshi_list[idx]

# ---------------- 月干支（固定表をそのまま参照） ----------------
def get_month_kanshi_from_table(birth_date):
    """
    固定値ファイル（月干支表）は (年, 月) のタプルキー。
    そのまま lookup。なければフォールバックで文字列キーも試す。
    """
    d = _as_date(birth_date)
    y, m = d.year, d.month

    # 1) タプルキー最優先
    idx = month_kanshi_index_dict.get((y, m))
    if isinstance(idx, str):
        try: idx = int(idx)
        except: idx = None
    if isinstance(idx, int) and 1 <= idx <= 60:
        return kanshi_list[idx], idx, {"hit": ("tuple", y, m)}

    # 2) 文字列キーの保険（万一辞書に含まれている場合）
    for k in (f"{y}-{m:02d}", f"{y}{m:02d}"):
        v = month_kanshi_index_dict.get(k)
        if v is None:
            continue
        try:
            vv = int(v)
        except Exception:
            vv = None
        if isinstance(vv, int) and 1 <= vv <= 60:
            return kanshi_list[vv], vv, {"hit": ("str", k)}

    return "該当なし", None, {"hit": None}

# ---------------- 日干支（暦年・暦月アンカー + 欠損補完） ----------------
def get_day_kanshi_from_table(birth_date):
    """
    kanshi_index_table[年][月] は「その月1日の干支 index（=アンカー）」。
    そこから **日-1** を足して進める。欠損／0 は前月へ遡って補完。
    """
    d = _as_date(birth_date)
    y, m, day = d.year, d.month, d.day

    def _norm(x):
        try:
            v = int(x)
            return v if 1 <= v <= 60 else None
        except Exception:
            return None

    # 1) その月のアンカー
    base = _norm(kanshi_index_table.get(y, {}).get(m))
    if base is not None:
        idx = _wrap60(base + (day - 1))
        return kanshi_list[idx], idx, {"hit": (y, m), "base_index": base}

    # 2) 欠損／0 の場合は前月へ（最大36ヶ月）
    yy, mm = y, m
    for _ in range(36):
        yy, mm = _prev_month(yy, mm)
        base = _norm(kanshi_index_table.get(yy, {}).get(mm))
        if base is not None:
            anchor = date(yy, mm, 1)
            delta = (d - anchor).days  # 1日なら 0
            idx = _wrap60(base + delta)
            return kanshi_list[idx], idx, {"hit": (yy, mm), "base_index": base, "delta_days": delta}

    return "該当なし", None, {"hit": None}

# ---------------- 天中殺グループ（index→6分割） ----------------
def get_tenchusatsu_from_day_index(index: int | None) -> str:
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

# ---------------- UI（元のまま） ----------------
def main():
    st.title("天中殺診断アプリ【簡易版】")

    birth_date = st.date_input(
        "生年月日を入力してください（範囲：1900年～2033年）",
        value=datetime(2000, 1, 1),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2033, 12, 31)
    )

    if st.button("診断する"):
        # 診断ボタン内
        year_kanshi = get_year_kanshi_from_risshun(birth_date)
        month_kanshi, month_idx, month_dbg = get_month_kanshi_from_table(birth_date)
        day_kanshi, index, day_dbg = get_day_kanshi_from_table(birth_date)

        st.markdown(f"### 年干支（立春基準）: {year_kanshi}")
        st.markdown(f"### 月干支（固定表）: {month_kanshi}{'（index: ' + str(month_idx) + '）' if month_idx else ''}")
        st.markdown(f"### 日干支＆天中殺用数値： {day_kanshi}（インデックス: {index if index else '—'}）")

        with st.expander("デバッグ情報"):
            st.write({"month": month_dbg, "day": day_dbg})

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
