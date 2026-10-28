# 2005-07 ~ 2013-06 歷史資料（2007–2012 盲測用）
# 用法：python hist_download.py twse 2008 | tpex 2008 | rev | div
import requests, time, sys, re, datetime as dt
import pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}
START, END = dt.date(2005, 7, 1), dt.date(2013, 6, 30)
def num(x):
    try: return float(re.sub(r'[,\s+]', '', str(x)))
    except Exception: return float('nan')
def get(url, js=True, enc=None):
    for k in range(4):
        try:
            r = requests.get(url, headers=H, timeout=60)
            if enc: r.encoding = enc
            return r.json() if js else (r.status_code, r.text)
        except Exception as e: print('  重試', k + 1, url, e, flush=True); time.sleep(30 * (k + 1))
    return None
def pick(f, *keys):
    for i, x in enumerate(f):
        if all(k in x for k in keys): return i
    return None
def days(Y):
    d = max(dt.date(Y, 1, 1), START)
    while d.year == Y and d <= END:
        if d.weekday() < 5: yield d
        d += dt.timedelta(days=1)

def twse(Y):
    rows = []; nd = 0
    for d in days(Y):
        j = get(f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d:%Y%m%d}&type=ALLBUT0999&response=json'); time.sleep(3.5)
        tabs = [t for t in (j or {}).get('tables', []) if '證券代號' in [x.strip() for x in t.get('fields', [])] and t.get('data')]
        if not tabs: continue
        f = [x.strip() for x in tabs[0]['fields']]
        ix = [f.index(k) for k in ('證券代號', '開盤價', '最高價', '最低價', '收盤價', '成交股數', '成交金額')]; sg, df_ = f.index('漲跌(+/-)'), f.index('漲跌價差')
        for r in tabs[0]['data']:
            c = str(r[ix[0]]).strip()
            if not re.fullmatch(r'\d{4}|0050', c): continue
            s = re.sub('<[^>]+>', '', str(r[sg])).strip(); v = num(r[df_])
            chg = float('nan') if 'X' in s else (-v if '-' in s else v if '+' in s else 0.0)
            rows.append((d, c, 'twse', *[num(r[i]) for i in ix[1:]], chg, 'X' in s))
        nd += 1
        if nd % 50 == 0: print(d, nd, len(rows), flush=True)
    return rows

def tpex(Y):
    rows = []; nd = 0
    for d in days(Y):
        k = get(f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={d:%Y/%m/%d}&type=EW&response=json'); time.sleep(3.5)
        tt = [t for t in (k or {}).get('tables', []) if t.get('data') and '代號' in [re.sub(r'\s', '', x) for x in t.get('fields', [])]]
        if not tt: continue
        f = [re.sub(r'\s', '', x) for x in tt[0]['fields']]
        ix = [f.index('代號'), pick(f, '開盤'), pick(f, '最高'), pick(f, '最低'), pick(f, '收盤'), pick(f, '成交股數'), pick(f, '成交金額')]; ch = f.index('漲跌')
        for r in tt[0]['data']:
            c = str(r[ix[0]]).strip()
            if not re.fullmatch(r'\d{4}', c): continue
            chg = num(r[ch]); rows.append((d, c, 'tpex', *[num(r[i]) for i in ix[1:]], chg, chg != chg))
        nd += 1
        if nd % 50 == 0: print(d, nd, len(rows), flush=True)
    return rows

def rev():
    rows = []
    for mk in ('sii', 'otc'):
        y, m = 2004, 6
        while (y, m) <= (2013, 6):
            roc = y - 1911; fn = f't21sc03_{roc}_{m}' + ('_0' if y >= 2013 else '') + '.html'
            res = get(f'https://mopsov.twse.com.tw/nas/t21/{mk}/{fn}', js=False, enc='big5'); time.sleep(3)
            n0 = len(rows)
            if res and res[0] == 200:
                for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', res[1], flags=re.S | re.I):
                    cells = [re.sub(r'\s|&nbsp;', '', re.sub(r'<[^>]+>', '', c)) for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, flags=re.S | re.I)]
                    if len(cells) >= 5 and re.fullmatch(r'\d{4}', cells[0]):
                        rows.append((mk, cells[0], cells[1], y, m, num(cells[2]), num(cells[4])))   # 當月、去年當月（千元）
            print(mk, y, m, res[0] if res else None, '筆', len(rows) - n0, flush=True)
            m += 1
            if m == 13: y, m = y + 1, 1
    return pd.DataFrame(rows, columns=['market', 'stock_id', 'name', 'year', 'month', 'revenue_k', 'revenue_ly_k'])

def div():
    rows = []
    for Y in range(2005, 2014):
        j = get(f'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate={Y}0101&endDate={Y}1231&response=json') or {}
        for r in j.get('data') or []:
            y, m, dd = re.split('[年月日/]', r[0])[:3]
            rows.append(dict(date=f'{int(y)+1911}-{int(m):02d}-{int(dd):02d}', stock_id=r[1].strip(), market='twse', prev_close=num(r[3]), ref=num(r[4]), kind=r[6]))
        time.sleep(4)
        t = get(f'https://www.tpex.org.tw/www/zh-tw/bulletin/exDailyQ?startDate={Y}/01/01&endDate={Y}/12/31&response=json') or {}
        for tb in t.get('tables') or []:
            for r in tb.get('data') or []:
                y, m, dd = r[0].split('/')
                rows.append(dict(date=f'{int(y)+1911}-{int(m):02d}-{int(dd):02d}', stock_id=r[1].strip(), market='tpex', prev_close=num(r[3]), ref=num(r[4]), kind=r[8]))
        print(Y, len(rows), flush=True); time.sleep(4)
    return pd.DataFrame(rows)

kind = sys.argv[1]
if kind in ('twse', 'tpex'):
    Y = int(sys.argv[2]); rows = (twse if kind == 'twse' else tpex)(Y)
    df = pd.DataFrame(rows, columns=['date', 'stock_id', 'market', 'open', 'high', 'low', 'close', 'vol', 'money', 'chg', 'xflag'])
    df.to_csv(f'hist_{kind}_{Y}.csv.gz', index=False); print('完成', kind, Y, '交易日', df.date.nunique() if len(df) else 0, '筆', len(df))
elif kind == 'rev':
    df = rev(); df.to_csv('hist_rev.csv.gz', index=False); print('完成 營收', len(df), df.groupby('market').size().to_dict())
else:
    df = div(); df.to_csv('hist_div.csv.gz', index=False); print('完成 除權息', len(df))
