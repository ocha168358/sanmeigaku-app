import datetime
from risshun_data import risshun_dict
from day_kanshi_dict import kanshi_index_table           # 日：{年:{月:idx}} または {(年,月):idx}
from month_kanshi_index_dict import month_kanshi_index_dict  # 月：同上（固定表）
from hayami import kanshi_data                           # {1..60: {"kanshi": "甲子", "tensatsu": "子丑"}}

# ===== 基本ユーティリティ =====

def _adjust_base_year_by_risshun(d: datetime.date) -> int:
    """立春前は前年を返す（年干支・月表参照の基準年）。"""
    y = d.year
    rs = risshun_dict.get(y)
    return y if (not rs or d >= rs) else (y - 1)

# ===== 年干支 =====

def get_year_kanshi_index(d: datetime.date) -> int:
    """立春基準の年干支インデックス（1..60）"""
    y = _adjust_base_year_by_risshun(d)
    return ((y - 1984) % 60) + 1

def get_year_kanshi_name(index_1to60: int) -> str:
    return kanshi_data[int(index_1to60)]["kanshi"]

# ===== 月干支（固定表） =====

def get_month_kanshi_index(d: datetime.date) -> int | None:
    """
    month_kanshi_index_dict から月干支Idxを取得。
    まず (年, 月) のタプルキー、次に {年:{月:idx}} の順で参照（DBを壊さない最小差分）。
    月は“暦月”で参照し、基準年は立春補正済みの年を使う。
    """
    by = _adjust_base_year_by_risshun(d)
    m = d.month

    # ① タプルキー優先
    tkey = (by, m)
    if tkey in month_kanshi_index_dict:
        return int(month_kanshi_index_dict[tkey])

    # ② ネスト辞書にフォールバック
    try:
        return int(month_kanshi_index_dict[by][m])
    except Exception:
        return None

def get_month_kanshi_name(index_1to60: int | None) -> str:
    if index_1to60 is None:
        return "該当なし"
    return kanshi_data[int(index_1to60)]["kanshi"]

# ===== 日干支（その月の1日Idx＋日） =====

def get_day_kanshi_index(d: datetime.date) -> int | None:
    """
    kanshi_index_table から “その月の1日インデックス” を取得し +日（60超は-60）。
    まず {年:{月:idx}}、次に (年, 月) のタプルキーの順で参照（最小差分）。
    """
    by = _adjust_base_year_by_risshun(d)
    m = d.month

    base_idx = None
    # ① ネスト辞書優先
    try:
        base_idx = int(kanshi_index_table[by][m])
    except Exception:
        # ② タプルキー
        try:
            base_idx = int(kanshi_index_table[(by, m)])
        except Exception:
            return None

    idx = base_idx + d.day
    while idx > 60:
        idx -= 60
    return idx

def get_day_kanshi_name(index_1to60: int | None) -> str:
    if index_1to60 is None:
        return "該当なし"
    return kanshi_data[int(index_1to60)]["kanshi"]
