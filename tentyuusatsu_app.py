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

# ===== 天中殺グラフ（バイオリズム）画像の設定 =====
# 1) GitHub の raw ベースURL（例）を設定
#    例: https://raw.githubusercontent.com/<user>/<repo>/<branch>
GRAPH_BASE_URL = "https://raw.githubusercontent.com/<ユーザー名>/<リポジトリ名>/main"

# 2) あなたのファイル名（相対パス）のマッピング
TENCHUSATSU_GRAPH_PATHS = {
    "子丑": "sanmeigaku_images/neushi.png",
    "寅卯": "sanmeigaku_images/torau.png",
    "辰巳": "sanmeigaku_images/tatsumi.png",
    "午未": "sanmeigaku_images/umahitsujiI.png",
    "申酉": "sanmeigaku_images/sarutori.png",
    "戌亥": "sanmeigaku_images/inui.png",
}

def _graph_url_for(ts_group: str) -> str | None:
    """GitHub raw かローカルを解決して返す。GRAPH_BASE_URLが未設定ならそのままパスを返す。"""
    rel = TENCHUSATSU_GRAPH_PATHS.get(ts_group)
    if not rel:
        return None
    if GRAPH_BASE_URL and "<ユーザー名>" not in GRAPH_BASE_URL:
        return f"{GRAPH_BASE_URL.rstrip('/')}/{rel.lstrip('/')}"
    # ベース未設定なら相対パスのまま（ローカル同梱運用）
    return rel

def show_tenchusatsu_graph(ts_group: str):
    url = _graph_url_for(ts_group)
    if not url:
        st.caption("（グラフ画像のURLが未設定です）")
        return
    # ① 非推奨の use_column_width → use_container_width に変更
    st.image(url, caption=f"{ts_group}天中殺の運気グラフ（バイオリズム）", use_container_width=True)
    # ② Markdown の強制改行（行末に半角スペース2つ + \n）
    st.markdown("※ 一番低迷している2ヶ月が天中殺期間となります。  \n　 年単位で見たい方は「5月＝2025年」と置き換えてください（12年周期）")



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

# --- 月干支テーブル読み取り（idx/start_day/prev_idx を柔軟に取得） ---
def _mk_int(v):
    try:
        i = int(v)
        return i
    except Exception:
        return None

def _read_month_entry(y: int, m: int):
    """
    month_kanshi_index_dict の (y,m) を取得。
    返り値: (this_idx, start_day, prev_idx)
    受理する形式:
      - int/str               -> this_idx
      - dict                  -> keys: idx/index/value/this, start_day/start/boundary, prev_idx/prev/before
      - キー形: (y,m) / {y:{m:...}} / "YYYY-MM" / "YYYYMM"
    """
    src = None
    if (y, m) in month_kanshi_index_dict:
        src = month_kanshi_index_dict[(y, m)]
    elif isinstance(month_kanshi_index_dict.get(y), dict) and m in month_kanshi_index_dict[y]:
        src = month_kanshi_index_dict[y][m]
    else:
        src = (month_kanshi_index_dict.get(f"{y}-{m:02d}")
               or month_kanshi_index_dict.get(f"{y}{m:02d}"))

    if src is None:
        return None, None, None

    # 単なる数値/文字列
    if not isinstance(src, dict):
        idx = _mk_int(src)
        return (idx if idx else None), None, None

    # dict 形式
    idx = _mk_int(src.get("idx") or src.get("index") or src.get("value") or src.get("this"))
    sd  = src.get("start_day") or src.get("start") or src.get("boundary")
    start_day = _mk_int(sd)
    prev_idx  = _mk_int(src.get("prev_idx") or src.get("prev") or src.get("before"))

    return (idx if idx else None), start_day, (prev_idx if prev_idx else None)

# 前月キー
def _prev_y_m(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)

# ---------------- 月干支：固定辞書A方式 ----------------
def get_month_kanshi(birth_date):
    """
    二十四節気：各月の start_day（節入り）で切り替え。
    - 当月 (y,m) のエントリに start_day があれば、
        d >= start_day で this_idx、d < start_day で prev_idx（無ければ前月idx）。
    - start_day が無い月は、
        2月のみ立春（risshun_dict）で切替、それ以外は this_idx をそのまま採用。
    - idx/prev_idx は 0→60、文字列→int に丸める。
    """
    d = _as_date(birth_date)
    y, m, day = d.year, d.month, d.day

    this_idx, start_day, prev_idx = _read_month_entry(y, m)

    # 1) start_day が定義されている月（推奨データ）
    if start_day is not None:
        if day >= start_day:
            if this_idx:
                idx = ((this_idx - 1) % 60) + 1
                return _kanshi_name(idx), idx, {"hit": (y, m), "rule": f"start_day≥{start_day}"}
        else:
            if prev_idx:
                idx = ((prev_idx - 1) % 60) + 1
                return _kanshi_name(idx), idx, {"hit": (y, m), "rule": f"before start_day({start_day})"}
            # prev_idx 未設定 → 前月の this_idx を参照
            py, pm = _prev_y_m(y, m)
            p_idx, _, _ = _read_month_entry(py, pm)
            if p_idx:
                idx = ((p_idx - 1) % 60) + 1
                return _kanshi_name(idx), idx, {"hit": (py, pm), "rule": "fallback prev month"}

            # さらに無ければ this_idx を保険採用
            if this_idx:
                idx = ((this_idx - 1) % 60) + 1
                return _kanshi_name(idx), idx, {"hit": (y, m), "rule": "fallback this_idx"}

    # 2) start_day が無い月
    if this_idx:
        if m == 2:
            # 2月だけは立春基準で前後を分ける
            rs = risshun_dict.get(y)
            if rs and d < rs:
                py, pm = (y - 1, 12)
                p_idx, _, _ = _read_month_entry(py, pm)
                if p_idx:
                    idx = ((p_idx - 1) % 60) + 1
                    return _kanshi_name(idx), idx, {"hit": (py, pm), "rule": "risshun prev-month"}
        idx = ((this_idx - 1) % 60) + 1
        return _kanshi_name(idx), idx, {"hit": (y, m), "rule": "no start_day"}

    # 3) データ未整備 → day_kanshi_dict で前月推定の保険（任意）
    #    前月のエントリがあればその idx を返す（ここで day_kanshi_dict を使う必然は薄いが温存）
    py, pm = _prev_y_m(y, m)
    p_idx, _, _ = _read_month_entry(py, pm)
    if p_idx:
        idx = ((p_idx - 1) % 60) + 1
        return _kanshi_name(idx), idx, {"hit": (py, pm), "rule": "no data: use prev"}
    return "該当なし", None, {"hit": None, "rule": "no data"}

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

def _read_month_idx_by_key(y: int, m: int):
    """month_kanshi_index_dict から (y,m) の index を 1..60 で取得。0→60, 文字列→int。"""
    v = month_kanshi_index_dict.get((y, m))
    if v is None:
        try:
            v = month_kanshi_index_dict[y][m]  # {年:{月:idx}} フォールバック
        except Exception:
            return None
    try:
        v = int(v)
    except Exception:
        return None
    if v == 0:
        v = 60
    return _wrap_1_60(v)

def get_prev_calendar_month_kanshi(birth_date):
    """
    暦月ベースの『前月』の月干支（注意表示用）。
    例）8/3 → (年, 7) をそのまま引く。1月は (年-1, 12)。
    """
    d = _as_date(birth_date)
    y, m = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    idx = _read_month_idx_by_key(y, m)
    return (kanshi_name(idx), idx, {"key": (y, m)}) if idx else ("該当なし", None, {"key": (y, m)})


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
    # 先に初期化（未定義防止）
    year_k = month_k = day_k = None
    month_idx = day_idx = None
    month_dbg = day_dbg = {}

    try:
        # 年・月・日
        year_k = get_year_kanshi(birth_date)
        month_k, month_idx, month_dbg = get_month_kanshi(birth_date)
        day_k, day_idx, day_dbg = get_day_kanshi(birth_date)
    except Exception as e:
        st.error(f"計算中にエラーが発生しました: {e}")
        # 続行（day_idx は None のまま）

    # --- 表示 ---
    if year_k is not None:
        st.markdown(f"### 年干支（立春基準）: {year_k}")

    st.markdown(f"### 月干支（固定表A方式）: {month_k if month_k else '・'}（index: {month_idx if month_idx else '・'}）")

    # 月初の参考表示（あなたの条件のまま）
    if birth_date.day <= 7 or (birth_date.month == 2 and _as_date(birth_date) < risshun_dict.get(birth_date.year, date(birth_date.year, 2, 4))):
        prev_m_name, prev_m_idx, prev_m_dbg = get_prev_calendar_month_kanshi(birth_date)
        st.caption(f"【参考】節入り前生まれの方の月干支: {prev_m_name}（index: {prev_m_idx if prev_m_idx else '・'}）")

    st.info("※ 月干支は二十四節気（節入り）で切り替わります。月初（節入り前）生まれの方は結果が異なる場合があります。厳密な節入り日は各年の節入りカレンダーで確認してください → https://keisan.site/exec/system/1186111877")

    st.markdown(f"### 日干支＆天中殺用数値: {day_k if day_k else '・'}（インデックス: {day_idx if day_idx else '・'}）")

    st.markdown(" ")
    st.markdown(" ")

    # 天中殺（day_idx が取れているときだけ）
    if day_idx:
        ts_group = tenchusatsu_from_index(day_idx)
        st.markdown(f"### 天中殺: {ts_group}")
        msg = tentyuusatsu_messages.get(ts_group) if isinstance(tentyuusatsu_messages, dict) else None
        if msg:
            for line in msg:
                st.markdown(f"- {line}")
        else:
            st.caption("該当メッセージなし")

            # 改行を2行追加（メッセージとグラフの間に余白）
            st.markdown("<br><br>", unsafe_allow_html=True)

        # グラフ（設定していれば表示）
        try:
            show_tenchusatsu_graph(ts_group)
        except Exception:
            pass
    else:
        st.warning("この年の干支データは未登録のため、天中殺の診断ができません。")

