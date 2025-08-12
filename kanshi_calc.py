import datetime

from risshun_data import risshun_dict
from month_kanshi_index_dict import month_kanshi_index_dict
from day_kanshi_dict import kanshi_index_table as day_kanshi_index_table
from hayami import kanshi_data  # index: 1..60 -> {"kanshi": "甲子", "tensatsu": "子丑" など}

# 既存にある前提の年干支関連が別DB/関数で用意されている場合はそれを使用する想定。
# ここでは get_year_kanshi_index / get_year_kanshi_name は既存実装がある前提で残し、
# 必要最小限の月干支取得系と簡易天中殺計算のみ追加しています。

# --- 既存前提の年干支 ---
def get_year_kanshi_index(d: datetime.date) -> int:
    """
    立春判定の年干支インデックス（1..60）を返す。
    既存のロジック／DBを利用している前提（関数名は変更しない）。
    """
    # 立春基準で年を決定
    year = d.year
    rs = risshun_dict.get(year)
    if rs is None:
        raise ValueError(f"risshun_dict に {year} 年の立春がありません。")
    if d < rs:
        year -= 1

    # ここは既存の年干支インデックス取得の仕組みに接続してください。
    # 例：year_kanshi_index_dict[year] を使う等（本ファイルでは関数シグネチャのみ維持）。
    from year_kanshi_index_dict import year_kanshi_index_dict  # 既存DB想定
    return int(year_kanshi_index_dict[year])


def get_year_kanshi_name(index_1to60: int) -> str:
    return kanshi_data[int(index_1to60)]["kanshi"]


# --- 追加：節月番号（1..12、寅=1） ---
def get_setsuge tsu_number(d: datetime.date) -> int:
    """
    立春（寅月の始まり）を起点とした節月番号（1..12）を返す。
    寅=1, 卯=2, ... 丑=12
    """
    y = d.year
    rs = risshun_dict.get(y)
    if rs is None:
        raise ValueError(f"risshun_dict に {y} 年の立春がありません。")

    if d >= rs:
        base_year = y
        base_rs = rs  # その年の立春
    else:
        base_year = y - 1
        base_rs = risshun_dict.get(base_year)
        if base_rs is None:
            raise ValueError(f"risshun_dict に {base_year} 年の立春がありません。")

    # 立春月（通常2月）からの月差で節月を求める
    months_since = (d.year - base_year) * 12 + (d.month - base_rs.month)
    # days は base_rs 当日以降でしか base_year にならないため、ここで日による微調整は不要
    setsu_no = (months_since % 12) + 1  # 0基点→1..12
    return setsu_no


# --- 追加：月干支（固定表 × 節月番号） ---
def get_month_kanshi_index(d: datetime.date) -> int:
    """
    month_kanshi_index_dict の固定値を使って月干支インデックス（1..60）を取得。
    キー構造は {年（立春年）: {節月番号(1-12): index}} を想定。
    """
    y = d.year
    rs = risshun_dict.get(y)
    if rs is None:
        raise ValueError(f"risshun_dict に {y} 年の立春がありません。")

    if d >= rs:
        base_year = y
    else:
        base_year = y - 1

    setsu_no = get_setsuge tsu_number(d)
    try:
        idx = int(month_kanshi_index_dict[base_year][setsu_no])
    except KeyError:
        raise KeyError(f"month_kanshi_index_dict に {base_year} 年・節月 {setsu_no} のデータがありません。")
    return idx


def get_month_kanshi_name(index_1to60: int) -> str:
    return kanshi_data[int(index_1to60)]["kanshi"]


# --- 日干支（固定表＋日） ---
def get_day_kanshi_index(d: datetime.date) -> int:
    """
    day_kanshi_dict の固定値（その月の1日インデックス等）＋日で求める。
    60を超えたら-60。
    期待キー：day_kanshi_index_table[(year, month)] -> その月の「1日」の干支インデックス
    """
    key = (d.year, d.month)
    if key not in day_kanshi_index_table:
        raise KeyError(f"day_kanshi_index_table に {key} のデータがありません。")

    base_idx = int(day_kanshi_index_table[key])  # その月1日のインデックス
    idx = base_idx + (d.day - 1)
    while idx > 60:
        idx -= 60
    return idx


def get_day_kanshi_name(index_1to60: int) -> str:
    return kanshi_data[int(index_1to60)]["kanshi"]


# --- 追加：簡易方式の天中殺（年Idx＋節月番号＋日） ---
def calc_tenchusatsu_simple(year_index: int, setsu_month_number: int, day: int) -> str:
    """
    年干支インデックス＋節月番号＋日 を 60制に折り返し、
    そのインデックスに紐づく天中殺グループを返す（kanshi_data の "tensatsu" を使用）。
    """
    s = int(year_index) + int(setsu_month_number) + int(day)
    while s > 60:
        s -= 60
    return kanshi_data[s]["tensatsu"]
