# 下載某一年的三大法人買賣超（證交所 T86 + 櫃買），輸出 inst_<year>.csv.gz
import requests, time, sys, re, datetime as dt
import pandas as pd
Y = int(sys.argv[1]); H = {'User-Agent': 'Mozilla/5.0'}
num = lambda x: float(str(x).replace(',', '').strip() or 0)
def get(url):
    for k in range(3):
        try: return requests.get(url, headers=H, timeout=40).json()
        except Exception as e: print('  重試', k + 1, e, flush=True); time.sleep(30 * (k + 1))
    return None
rows = []; today = dt.date.today(); d = dt.date(Y, 1, 1); nday = 0
while d.year == Y and d <= today:
    if d.weekday() < 5:
        j = get(f'https://www.twse.com.tw/rwd/zh/fund/T86?date={d:%Y%m%d}&selectType=ALLBUT0999&response=json'); time.sleep(3.5)
        if j and j.get('stat') == 'OK' and j.get('data'):
            f = [x.strip() for x in j['fields']]
            fi = [i for i, x in enumerate(f) if x.startswith('外') and '買賣超' in x and not x.startswith('外資自營商')][0]
            ti = f.index('投信買賣超股數'); di = f.index('自營商買賣超股數')
            n1 = 0
            for r in j['data']:
                c = str(r[0]).strip()
                if re.fullmatch(r'\d{4}', c): rows.append((d, c, 'twse', num(r[fi]), num(r[ti]), num(r[di]))); n1 += 1
            n2 = 0
            if Y >= 2014:
                k = get(f'https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={d:%Y/%m/%d}&response=json'); time.sleep(3.5)
                t = [x for x in (k or {}).get('tables', []) if x.get('data')]
                if t:
                    nc = len(t[0]['fields']); pos = {16: (4, 7, 8), 24: (4, 13, 22)}.get(nc)
                    if pos is None: print('  櫃買欄位數不明', d, nc, t[0]['fields'], flush=True)
                    else:
                        for r in t[0]['data']:
                            c = str(r[0]).strip()
                            if re.fullmatch(r'\d{4}', c): rows.append((d, c, 'tpex', num(r[pos[0]]), num(r[pos[1]]), num(r[pos[2]]))); n2 += 1
            nday += 1
            if nday % 20 == 0: print(d, '上市', n1, '上櫃', n2, flush=True)
    d += dt.timedelta(days=1)
df = pd.DataFrame(rows, columns=['date', 'stock_id', 'market', 'foreign', 'trust', 'dealer'])
df.to_csv(f'inst_{Y}.csv.gz', index=False)
print('完成', Y, '交易日', nday, '筆數', len(df), '上櫃筆數', int((df.market == 'tpex').sum()) if len(df) else 0)
