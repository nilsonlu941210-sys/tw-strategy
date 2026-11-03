# 1998–2005 個股股價（FinMind）與加權指數（TWSE），給 v48 樣本外檢驗
import sys, time, json, requests, pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}; U = 'https://api.finmindtrade.com/api/v4/data'
job = sys.argv[1]
if job == 'idx':
    rows = []
    for y in range(1998, 2006):
        for m in range(1, 13):
            for k in range(4):
                try:
                    j = requests.get(f'https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={y}{m:02d}01&response=json', headers=H, timeout=60).json(); break
                except Exception as e: print(e); time.sleep(10)
            for r in j.get('data', []):
                a, b, c = r[0].strip().split('/'); f = lambda x: float(x.replace(',', ''))
                rows.append(dict(date=f'{int(a)+1911}-{b}-{c}', open=f(r[1]), high=f(r[2]), low=f(r[3]), close=f(r[4])))
            time.sleep(2.5)
        print(y, len(rows), flush=True)
    pd.DataFrame(rows).to_csv('old_taiex.csv.gz', index=False); sys.exit()
part, nparts = map(int, job.split('/'))
def q(**p):
    for k in range(6):
        try:
            r = requests.get(U, params=p, timeout=90); j = r.json()
            if j.get('status') == 200: return j.get('data') or []
            print('msg', j.get('msg'), flush=True); time.sleep(120 if 'limit' in str(j.get('msg', '')).lower() or r.status_code in (402, 429) else 5)
        except Exception as e: print(e); time.sleep(15)
    return None
info = q(dataset='TaiwanStockInfo'); dl = q(dataset='TaiwanStockDelisting', start_date='1990-01-01')
ids = sorted({d['stock_id'] for d in info + dl if len(d['stock_id']) == 4 and d['stock_id'].isdigit() and not d['stock_id'].startswith('0') and not d['stock_id'].startswith('91')})
mine = ids[part::nparts]; print('總檔數', len(ids), '本工作', len(mine), flush=True)
out = []; miss = []
for i, s in enumerate(mine):
    d = q(dataset='TaiwanStockPrice', data_id=s, start_date='1998-01-01', end_date='2005-12-31')
    if d is None: miss.append(s)
    elif d: out += [{k: x[k] for k in ('date', 'stock_id', 'Trading_Volume', 'Trading_money', 'open', 'max', 'min', 'close')} for x in d]
    time.sleep(6.5)
    if i % 50 == 0: print(i, s, len(out), flush=True)
pd.DataFrame(out).to_csv(f'old_px_{part}.csv.gz', index=False)
if part == 0:
    pd.DataFrame(dl).to_csv('old_delisting.csv', index=False); pd.DataFrame(info).to_csv('old_info.csv', index=False)
print('完成', len(out), '失敗', miss)
