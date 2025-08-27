# kanshi_calc.py
from __future__ import annotations

from datetime import date
from risshun_data import risshun_dict
from hayami import kanshi_data                     # {1..60: {"kanshi": "...", "tensatsu": "..."}}
from month_kanshi_index_dict import month_kanshi_index_dict  # {(year, month): index}

# =========================================================
# 共有ヘルパー
# =========================================================

def get_kanshi_name(index: int | None) -> str | None:
    """干支インデックス(1..60)から干支名を返す。Noneや未登録は None。"""
    if index is None:
        return None
    data = kanshi_data.get(int(index))
    return data.get("kanshi") if data else None


def _month_lookup_with_risshun(d: date) -> tuple[int, int]:
    """節月（立春基準）で参照すべき (year, month) を返す。
       立春前は前年の12月節、それ以外はその年の暦月。"""
    y, m = d.year, d.month
    rs = risshun_dict.get(y)
    if rs and d < rs:
        return (y - 1, 12)
    return (y, m)

# =========================================================
# 月干支（固定表 A 方式）
# =========================================================

def get_month_kanshi_index_fixed(birth_date: date) -> int | None:
    """固定表 month_kanshi_index_dict を節月基準で引いて月干支インデックス(1..60)を返す。"""
    y, m = _month_lookup_with_risshun(birth_date)
    return month_kanshi_index_dict.get((y, m))


def get_month_kanshi_name_fixed(birth_date: date) -> str | None:
    """固定表＋立春補正で求めた月干支名を返す。該当なしは None。"""
    idx = get_month_kanshi_index_fixed(birth_date)
    return get_kanshi_name(idx)

# =========================================================
# 日干支（表示用の干支名：甲子アンカー差分で算出）
#   ※ 天中殺用の「月値 + 日」計算はアプリ側の既存処理のまま利用
# =========================================================

# あなたの指定する甲子アンカー日
_KOUSHI_ANCHORS: tuple[date, ...] = (
    date(1900, 2, 20),   # 甲子
    date(2025, 12, 21),  # 甲子
    date(2026, 12, 16),  # 甲子
)

# 1始まりの干支名リスト（アプリと同じ順序）
_KANSHI = [
    "", "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
    "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
    "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
    "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
    "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥"
]

def get_day_kanshi_name_by_anchor(d: date) -> str:
    """甲子アンカー日の差分（60日周期）で日干支名（1始まり）を返す。"""
    anchor = min(_KOUSHI_ANCHORS, key=lambda a: abs((d - a).days))
    diff = (d - anchor).days % 60
    idx = 60 if diff == 0 else diff
    return _KANSHI[idx]
