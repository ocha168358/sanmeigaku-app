
"""kanshi_calc.py

このモジュールでは、干支や天中殺の計算に関するロジックをまとめています。
年干支・月干支のインデックス計算を行い、その結果から干支名や天中殺グループを取得するための
関数群を提供します。日付から直接天中殺グループを求める補助関数も用意しています。

従来の `kanshi_month_start_index` を用いた方式は一部の年にしか対応しておらず、
算命学で一般的に用いられる月干支計算には「年ごとの揺らぎ」を考慮する必要があります。
ここでは `day_kanshi_dict.py` に定義されている `kanshi_index_table` を利用して、
年・節月ごとに正確な干支インデックスを取得できるようにしています。

注意: 月干支インデックスの計算では、立春前の場合に前年の12月節として扱うため、
`get_setsuge_month()` と `get_year_kanshi_index()` の結果を組み合わせて計算します。
"""

from __future__ import annotations

from datetime import date
from risshun_data import risshun_dict
from hayami import kanshi_data
from .kanshi_index_table import kanshi_index_table
from month_kanshi_index_dict import month_kanshi_index_dict  # 追加

month_kanshi = get_kanshi_name(month_kanshi_index_dict.get((birth_date.year, birth_date.month)))

# day_kanshi_dict が存在する場合、各年・節月の月干支インデックスを提供するテーブルを利用する。
try:
    # `kanshi_index_table[year][month]` は、その年の節月の「0日目」の干支インデックスを表す。
    # 1日目の干支インデックスはこの値に1を足したものとなる。
    from day_kanshi_dict import kanshi_index_table  # type: ignore
except ImportError:
    kanshi_index_table: dict[int, dict[int, int]] = {}


def get_setsuge_month(birth_date: date) -> int:
    """立春基準で節月番号（1〜12）を返す。

    立春前の日付は前年の12月節とするため 12 を返し、立春以降はその月の番号を返す。
    """
    year = birth_date.year
    risshun = risshun_dict.get(year)
    # 立春データが無い場合は暦月を返す
    if risshun is None:
        return birth_date.month
    if birth_date < risshun:
        return 12
    return birth_date.month


def get_year_kanshi_index(birth_date: date) -> int:
    """年干支のインデックス（1〜60）を返します。

    立春より前の場合は前年の干支とし、1984年（甲子）をサイクルの起点として
    60干支の番号を計算します。
    """
    year = birth_date.year
    risshun = risshun_dict.get(year)
    if risshun is not None and birth_date < risshun:
        year -= 1
    # 1984年=甲子を1とした60干支サイクル
    return ((year - 1984) % 60) + 1


def get_year_kanshi_from_risshun(birth_date: date) -> dict[str, str] | None:
    """生年月日から年干支の辞書（干支名と天中殺グループ）を返す。

    辞書には `kanshi`（干支名）と `tensatsu`（天中殺グループ）が含まれます。
    データが存在しない場合は None を返します。
    """
    index = get_year_kanshi_index(birth_date)
    return kanshi_data.get(index)


def get_month_kanshi_index(birth_date: date) -> int | None:
    """節月基準の月干支インデックス（1〜60）を返します。

    `day_kanshi_dict.py` に定義された `kanshi_index_table` を参照して、
    その年と節月における月の1日目の干支インデックスを計算します。
    立春前の日付は前年のデータを利用し、節月番号は 12 とします。

    データが存在しない場合は None を返します。
    """
    year = birth_date.year
    # 立春データの有無に関わらず、節月番号は get_setsuge_month で算出
    month_no = get_setsuge_month(birth_date)
    # 立春前の場合は前年のデータを参照
    risshun = risshun_dict.get(year)
    year_for_table = year
    if risshun is not None and birth_date < risshun:
        year_for_table = year - 1
    # 対応する年のテーブルを取得
    try:
        base_index = kanshi_index_table[year_for_table][month_no]
    except Exception:
        return None
    # 月の1日目の干支インデックスは base_index + 1
    month_index = base_index + 1
    if month_index > 60:
        month_index -= 60
    return month_index

def get_year_kanshi_index(date):
    year = date.year
    risshun = risshun_dict[year]
    if date < risshun:
        year -= 1
    return kanshi_index_table[year]


def month_kanshi_index_dict(date):
    year = date.year
    month = date.month
    day = date.day
    risshun = risshun_dict[year]
    if date < risshun:
        year -= 1
    # 修正ポイント：年と月から直接インデックス取得（1月〜12月）
    return month_kanshi_index_dict[year][month]


def get_kanshi_name(index):
    for data in kanshi_data.values():
        if data["index"] == index:
            return data["kanshi"]
    return None


def get_tensatsu_group(index):
    for data in kanshi_data.values():
        if data["index"] == index:
            return data["tensatsu"]
    return None


def get_month_kanshi(birth_date: date) -> dict[str, str] | None:
    """生年月日から月干支の辞書（干支名と天中殺グループ）を返す。"""
    index = month_kanshi_index_dict(birth_date)
    if index is None:
        return None
    return kanshi_data.get(index)


def get_kanshi_name(index: int) -> str | None:
    """干支インデックスから干支名を取得する。存在しない場合は None。"""
    data = kanshi_data.get(index)
    return data.get("kanshi") if data else None


def get_tensatsu_group(index: int) -> str | None:
    """干支インデックスから天中殺グループ（子丑・寅卯…）を取得する。"""
    data = kanshi_data.get(index)
    return data.get("tensatsu") if data else None


def get_tenchusatsu_group_by_indices(birth_date: date) -> str:
    """年干支インデックスと節月番号・日を用いて天中殺を判定する関数。

    判定手順：
      1. 年干支インデックス（1〜60）を求める。
      2. 節月番号（get_setsuge_monthで得られる1〜12）を加算。
      3. 誕生日の日（birth_date.day）を加算。
      4. 合計値を60で割った余り（0は60とする）を天中殺インデックスとする。
      5. インデックスの範囲に応じてグループを決定する。

    返り値例："あなたの天中殺は寅卯天中殺です"
    """
    year_index = get_year_kanshi_index(birth_date)
    month_no = get_setsuge_month(birth_date)
    day_no = birth_date.day
    total = (year_index + month_no + day_no) % 60
    if total == 0:
        total = 60
    # 6つのグループに割り当て
    if 1 <= total <= 10:
        group = "子丑"
    elif 11 <= total <= 20:
        group = "寅卯"
    elif 21 <= total <= 30:
        group = "辰巳"
    elif 31 <= total <= 40:
        group = "午未"
    elif 41 <= total <= 50:
        group = "申酉"
    else:  # 51〜60
        group = "戌亥"
    return f"あなたの天中殺は{group}天中殺です"


