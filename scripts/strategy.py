# 策略核心：計算、抓資料（證交所、櫃買中心公開資料）。參數已驗證，請勿修改。
import os, sys, json, time, pickle, re, datetime as dt
import numpy as np, pandas as pd, requests, warnings
warnings.filterwarnings('ignore')

# ---------------- 策略參數（已驗證，請勿修改） ----------------
POOL_N, SAT_N, SAT_W, CORE, CORE_W, CORE_K = 500, 7, 0.10, '00881', 0.30, 20   # 2026-10-28 使用者改為 7 檔＋核心 30%
BRK_LB, HOLD_H250, HOLD_RNH = 60, 0.85, -0.20
EXCLUDE = {'2330'}
KEEP_ROWS = 320
SWAP_K = 3   # 2026-10-28 使用者決定：位子滿時，最近 5 個交易日有 3 天是候選第 1 名 → 換掉分數最低的持股

# ---------------- 計算（不需要網路，可單獨測試） ----------------
def zrow(x):
    s = x.std()
    return ((x - x.mean()) / s).clip(-3, 3) if s and s == s else x * 0

def rnh_asof(rev, day):
    """每檔股票：截至 day 可用的最新月營收 ÷ 前 12 個月最高 − 1（月營收於次月 11 日起可用）"""
    r = rev.copy()
    r['avail'] = pd.to_datetime(dict(year=r.revenue_year, month=r.revenue_month, day=1)) + pd.offsets.MonthBegin(1) + pd.Timedelta(days=10)
    r = r[r.avail <= day]
    out = {}
    for s, g in r.groupby('stock_id'):
        ser = g.assign(p=pd.PeriodIndex.from_fields(year=g.revenue_year, month=g.revenue_month, freq='M')).drop_duplicates('p', keep='last').set_index('p').revenue.astype(float)
        ser = ser.reindex(pd.period_range(ser.index.min(), ser.index.max(), freq='M'))
        prev = ser.shift(1).rolling(12, min_periods=12).max()
        x = (ser / prev - 1).where(prev > 0).dropna()
        if len(x): out[s] = x.iloc[-1]
    return pd.Series(out, dtype=float)

def compute_pool(st, i):
    """第 i 列（新季第一天）之前的資料決定本季 500 檔"""
    adj, money = st['adj'], st['money']
    v = money.notna() & adj.notna()
    w = money.iloc[i - 60:i].where(v.iloc[i - 60:i]); avg = w.mean()
    cum = st['cum_days'].reindex(adj.columns).fillna(0) + v.iloc[:i].sum()
    ok = (cum >= 120) & (w.notna().sum() >= 48) & v.iloc[i - 5:i].any() & (avg >= 1e7)
    ok &= pd.Series([bool(re.fullmatch(r'[1-9]\d{3}', c)) and not c.startswith('91') for c in adj.columns], index=adj.columns)
    return list(avg[ok].sort_values(ascending=False).index[:POOL_N])

def signals(st, day=None):
    adj, money = st['adj'], st['money']
    i = len(adj) - 1 if day is None else int(adj.index.get_loc(day)); d = adj.index[i]
    a = adj.iloc[:i + 1]; v = (money.notna() & adj.notna()).iloc[:i + 1]
    pool = pd.Index(st['pool']).intersection(adj.columns)
    today_ok = v.iloc[-1]; cnt5 = v.iloc[-5:].sum() >= 3; r120 = a.iloc[-1] / a.iloc[-121] - 1 if len(a) > 120 else a.iloc[-1] * np.nan
    E = pd.Series(False, index=adj.columns); E[pool] = True; E &= today_ok & cnt5 & r120.notna()
    h250 = a.iloc[-1] / a.iloc[-250:].max().where(a.iloc[-250:].notna().sum() >= 200)
    hi = a.iloc[-61:-1]; hi60 = hi.max().where(hi.notna().sum() >= 54)
    brk = (a.iloc[-1] > hi60) & today_ok
    rnh = rnh_asof(st['revenue'], d).reindex(adj.columns)
    m = E & rnh.notna() & h250.notna()
    sc = pd.Series(np.nan, index=adj.columns)
    zz = (zrow(rnh[E]).fillna(0) + zrow(h250[E]).fillna(0)) / 2
    sc[m] = zrow(zz[m[E].values]) if m.any() else np.nan
    SIG = E & (rnh > 0) & brk; HOLD = E & (rnh > HOLD_RNH) & (h250 >= HOLD_H250)
    SIG[list(EXCLUDE & set(SIG.index))] = False
    return dict(date=d, SIG=SIG, HOLD=HOLD, score=sc, rnh=rnh, h250=h250, E=E)

# ---------------- 抓資料（證交所、櫃買中心公開資料） ----------------
H = {'User-Agent': 'Mozilla/5.0'}
def _num(x):
    try: return float(str(x).replace(',', '').strip())
    except Exception: return np.nan

def fetch_twse(day):
    url = f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={day:%Y%m%d}&type=ALLBUT0999&response=json'
    resp = requests.get(url, headers=H, timeout=30)
    try:
        j = resp.json()
    except Exception:
        raise RuntimeError(f'證交所回應不是 JSON（HTTP {resp.status_code}）：{resp.text[:300]!r}')
    if not j.get('tables'): print(f"  證交所 {day.date()} stat={j.get('stat')!r} keys={list(j)[:8]}")
    for t in j.get('tables', []):
        f = [x.strip() for x in t.get('fields', [])]
        if '證券代號' in f and '收盤價' in f:
            rows = []
            for r in t['data']:
                sgn = re.sub('<[^>]+>', '', str(r[f.index('漲跌(+/-)')])).strip()
                diff = _num(r[f.index('漲跌價差')])
                chg = np.nan if 'X' in sgn else (-diff if '-' in sgn else diff if '+' in sgn else 0.0)
                rows.append((str(r[f.index('證券代號')]).strip(), _num(r[f.index('收盤價')]), chg, _num(r[f.index('成交金額')]), _num(r[f.index('成交股數')]), 'X' in sgn))
            return pd.DataFrame(rows, columns=['code', 'close', 'chg', 'money', 'vol', 'exdiv'])
    return None   # 非交易日

def fetch_tpex(day):
    roc = f'{day.year - 1911}/{day:%m/%d}'
    try:
        j = requests.get(f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={day:%Y/%m/%d}&type=EW&response=json', headers=H, timeout=30).json()
        for t in j.get('tables', []):
            f = [re.sub(r'\s', '', x) for x in t.get('fields', [])]
            if '代號' in f and any('收盤' in x for x in f) and t.get('data'):
                ci = f.index('代號'); cl = [k for k, x in enumerate(f) if '收盤' in x][0]; ch = f.index('漲跌')
                mo = [k for k, x in enumerate(f) if '成交金額' in x][0]; vo = [k for k, x in enumerate(f) if '成交股數' in x][0]
                return pd.DataFrame([(str(r[ci]).strip(), _num(r[cl]), _num(r[ch]), _num(r[mo]), _num(r[vo]), not np.isfinite(_num(r[ch]))) for r in t['data']],
                                    columns=['code', 'close', 'chg', 'money', 'vol', 'exdiv'])
    except Exception as e:
        print('  櫃買新版網址失敗，改用舊版：', e)
    j = requests.get(f'https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={roc}&o=json', headers=H, timeout=30).json()
    data = j.get('aaData') or (j.get('tables') or [{}])[0].get('data') or []
    if not data: return None
    return pd.DataFrame([(str(r[0]).strip(), _num(r[2]), _num(r[3]), _num(r[9]), _num(r[8]), not np.isfinite(_num(r[3]))) for r in data],
                        columns=['code', 'close', 'chg', 'money', 'vol', 'exdiv'])

def append_day(st, day, df):
    adj, money, close = st['adj'], st['money'], st['close']
    df = df[df.close > 0].drop_duplicates('code').set_index('code')
    df = df[[bool(re.fullmatch(r'[1-9]\d{3}', c)) or c == CORE for c in df.index]]
    new_cols = list(df.index.difference(adj.columns))
    if new_cols:
        cols = list(adj.columns) + new_cols
        adj, money, close = adj.reindex(columns=cols), money.reindex(columns=cols), close.reindex(columns=cols)
        st['cum_days'] = st['cum_days'].reindex(cols).fillna(0)
        for c in new_cols: st['names'].setdefault(c, '')
    last_adj = adj.ffill().iloc[-1]; last_close = close.ffill().iloc[-1]
    prev = df.close - df.chg
    r = (df.close / prev - 1).where(prev > 0)
    r = r.where(r.abs() < 0.25, df.close / last_close.reindex(df.index) - 1)
    r = r.where(~df.exdiv, 0.0).where(lambda x: x.abs() < 0.25, 0.0).fillna(0.0)
    new_adj = (last_adj.reindex(df.index) * (1 + r)).fillna(df.close)
    traded = df.vol > 0
    row_adj = pd.Series(np.nan, index=adj.columns); row_adj[df.index] = new_adj.where(traded)
    row_m = pd.Series(np.nan, index=adj.columns); row_m[df.index] = df.money.where(traded)
    row_c = pd.Series(np.nan, index=adj.columns); row_c[df.index] = df.close
    st['adj'] = pd.concat([adj, row_adj.to_frame(day).T]); st['money'] = pd.concat([money, row_m.to_frame(day).T]); st['close'] = pd.concat([close, row_c.to_frame(day).T])
    if len(st['adj']) > KEEP_ROWS:
        drop = st['adj'].iloc[:-KEEP_ROWS]; st['cum_days'] = st['cum_days'].reindex(st['adj'].columns).fillna(0) + (drop.notna() & st['money'].iloc[:-KEEP_ROWS].notna()).sum()
        for k in ('adj', 'money', 'close'): st[k] = st[k].iloc[-KEEP_ROWS:]

def quarter_of(d): return f'{d.year}Q{(d.month - 1) // 3 + 1}'

def update_revenue(st, today):
    got = []
    for url in ('https://openapi.twse.com.tw/v1/opendata/t187ap05_L', 'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O'):
        try:
            j = requests.get(url, headers=H, timeout=60).json(); df = pd.DataFrame(j)
            ym = [c for c in df.columns if '資料年月' in c][0]; code = [c for c in df.columns if '公司代號' in c][0]
            rev = [c for c in df.columns if '當月營收' in c and '去年' not in c and '上月' not in c and '增減' not in c][0]
            y = df[ym].astype(str).str.strip()
            got.append(pd.DataFrame({'stock_id': df[code].astype(str).str.strip(), 'revenue_year': y.str[:-2].astype(int) + 1911,
                                     'revenue_month': y.str[-2:].astype(int), 'revenue': df[rev].map(_num) * 1000}))
        except Exception as e:
            print('  營收抓取失敗：', url, e)
    if not got: return
    new = pd.concat(got).dropna()
    old = st['revenue']
    chk = new.merge(old.assign(revenue_month=old.revenue_month + 1).rename(columns={'revenue': 'prev'}), on=['stock_id', 'revenue_year', 'revenue_month'])
    if len(chk) > 50:
        ratio = (chk.revenue / chk.prev).median()
        if ratio > 100: new['revenue'] /= 1000; print('  營收單位自動修正（÷1000）')
        elif ratio < 0.01: new['revenue'] *= 1000; print('  營收單位自動修正（×1000）')
    st['revenue'] = pd.concat([old, new]).drop_duplicates(['stock_id', 'revenue_year', 'revenue_month'], keep='last').reset_index(drop=True)
    print(f"  營收：最新月份 {new.revenue_year.max()}-{new[new.revenue_year == new.revenue_year.max()].revenue_month.max():02d}，{new.stock_id.nunique()} 家")

# ---------------- 主程式 ----------------

# ---------------- 硬事件自動不買（2026-10-29 使用者決定：只自動排除，不自動賣） ----------------
def _roc(s):
    s = re.sub(r'\D', '', str(s))
    if len(s) == 7: return pd.Timestamp(int(s[:3]) + 1911, int(s[3:5]), int(s[5:7]))
    if len(s) == 8: return pd.Timestamp(s)
    return None

def update_hard_events(st, today):
    """公開收購對象、全額交割/變更交易、暫停或停止交易、即將終止上市 → 自動不買名單。
    公開收購從每日重大訊息累積（保留 90 天）；其餘每天依官方清單重建。任何來源失敗都只略過。"""
    tw, tp = 'https://openapi.twse.com.tw/v1', 'https://www.tpex.org.tw/openapi/v1'
    get = lambda u: requests.get(u, headers=H, timeout=60).json()
    cur = {}
    def add(code, why):
        code = str(code).strip()
        if re.fullmatch(r'[1-9]\d{3}', code): cur.setdefault(code, why)
    jobs = [
        (tw + '/exchangeReport/TWT85U', lambda x: [add(r.get('Code'), '變更交易（全額交割）') for r in x]),
        (tw + '/exchangeReport/TWTAWU', lambda x: [add(r.get('Code'), '暫停交易') for r in x if not (_roc(r.get('TradingResumptionDate')) and _roc(r.get('TradingResumptionDate')) <= today)]),
        (tw + '/opendata/t187ap26_L', lambda x: [add(r.get('公司代號'), '停止買賣') for r in x]),
        (tw + '/company/suspendListingCsvAndHtml', lambda x: [add(r.get('Code'), '即將終止上市') for r in x if _roc(r.get('DelistingDate')) and _roc(r.get('DelistingDate')) >= today]),
        (tp + '/tpex_cmode', lambda x: [add(r.get('SecuritiesCompanyCode'), '變更交易（全額交割）' if r.get('AlteredTrading', '').strip() else ('管理股票' if r.get('ManagedStock', '').strip() else '停止交易'))
                                         for r in x if any(str(r.get(k, '')).strip() for k in ('AlteredTrading', 'ManagedStock', 'SuspensionOfTrading'))]),
        (tp + '/tpex_spendi_today', lambda x: [add(r.get('SecuritiesCompanyCode'), '暫停交易') for r in x if str(r.get('暫停交易', '')).strip()]),
        (tp + '/mopsfin_t187ap26_O', lambda x: [add(r.get('SecuritiesCompanyCode'), '停止買賣') for r in x]),
    ]
    for url, fn in jobs:
        try: fn(get(url))
        except Exception as e: print('  硬事件來源失敗：', url, e)
    # 公開收購：被收購公司自己發的重大訊息（主旨含「公開收購本公司」）
    to = st.get('tender', {})
    for url, ck in ((tw + '/opendata/t187ap04_L', '公司代號'), (tp + '/mopsfin_t187ap04_O', 'SecuritiesCompanyCode')):
        try:
            for r in get(url):
                subj = re.sub(r'\s', '', str(r.get('主旨 ', r.get('主旨', ''))))
                if '公開收購' in subj and ('收購本公司' in subj or '本公司股份' in subj or '本公司普通股' in subj):
                    c = str(r.get(ck, '')).strip(); d = _roc(r.get('發言日期')) or today
                    if re.fullmatch(r'[1-9]\d{3}', c): to[c] = str(d.date()); print('  公開收購對象：', c, r.get('公司名稱', r.get('CompanyName')), subj[:40])
        except Exception as e: print('  重大訊息來源失敗：', url, e)
    to = {c: d for c, d in to.items() if pd.Timestamp(d) >= today - pd.Timedelta(days=90)}
    st['tender'] = to
    for c, d in to.items(): cur.setdefault(c, f'公開收購中，{d} 公告')
    st['hard_events'] = cur
    print(f'  自動不買：{len(cur)} 檔', dict(list(cur.items())[:10]))
    return cur
