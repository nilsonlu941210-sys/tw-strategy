# 下載某一年的每日開高低收（證交所 MI_INDEX、櫃買每日收盤行情），輸出 ohlc_<year>.csv.gz
import requests, time, sys, re, datetime as dt
import pandas as pd
Y = int(sys.argv[1]); H = {'User-Agent': 'Mozilla/5.0'}
def num(x):
    try: return float(str(x).replace(',', '').strip())
    except Exception: return float('nan')
def get(url):
    for k in range(3):
        try: return requests.get(url, headers=H, timeout=40).json()
        except Exception as e: print('  重試', k + 1, e, flush=True); time.sleep(30 * (k + 1))
    return None
def pick(f, *keys):
    for i, x in enumerate(f):
        if all(k in x for k in keys): return i
    return None
rows = []; today = dt.date.today(); d = dt.date(Y, 1, 1); nday = 0; shown = set()
while d.year == Y and d <= today:
    if d.weekday() < 5:
        j = get(f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d:%Y%m%d}&type=ALLBUT0999&response=json'); time.sleep(3.5)
        tabs = [t for t in (j or {}).get('tables', []) if '證券代號' in [x.strip() for x in t.get('fields', [])] and t.get('data')]
        if tabs:
            f = [x.strip() for x in tabs[0]['fields']]
            if 'twse' not in shown: print('上市欄位', f, flush=True); shown.add('twse')
            ix = [f.index('證券代號'), f.index('開盤價'), f.index('最高價'), f.index('最低價'), f.index('收盤價'), f.index('成交股數'), f.index('成交金額')]
            for r in tabs[0]['data']:
                c = str(r[ix[0]]).strip()
                if re.fullmatch(r'\d{4}|00\d{2,4}[A-Z]?', c): rows.append((d, c, 'twse', *[num(r[i]) for i in ix[1:]]))
            k = get(f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={d:%Y/%m/%d}&type=EW&response=json'); time.sleep(3.5)
            tt = [t for t in (k or {}).get('tables', []) if t.get('data') and '代號' in [re.sub(r'\s', '', x) for x in t.get('fields', [])]]
            if tt:
                f = [re.sub(r'\s', '', x) for x in tt[0]['fields']]
                if 'tpex' not in shown: print('上櫃欄位', f, flush=True); shown.add('tpex')
                ix = [f.index('代號'), pick(f, '開盤'), pick(f, '最高'), pick(f, '最低'), pick(f, '收盤'), pick(f, '成交股數'), pick(f, '成交金額')]
                if None in ix: print('  上櫃欄位找不到', d, f, flush=True)
                else:
                    for r in tt[0]['data']:
                        c = str(r[ix[0]]).strip()
                        if re.fullmatch(r'\d{4}|00\d{2,4}[A-Z]?', c): rows.append((d, c, 'tpex', *[num(r[i]) for i in ix[1:]]))
            nday += 1
            if nday % 40 == 0: print(d, '累計', len(rows), flush=True)
    d += dt.timedelta(days=1)
df = pd.DataFrame(rows, columns=['date', 'stock_id', 'market', 'open', 'high', 'low', 'close', 'vol', 'money'])
df.to_csv(f'ohlc_{Y}.csv.gz', index=False)
print('完成', Y, '交易日', nday, '筆數', len(df), '上櫃筆數', int((df.market == 'tpex').sum()) if len(df) else 0)
