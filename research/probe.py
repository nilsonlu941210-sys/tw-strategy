import requests, time, pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}; rows = []
for y in range(1998, 2006):
    for m in range(1, 13):
        for k in range(4):
            try: j = requests.get(f'https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={y}{m:02d}01&response=json', headers=H, timeout=60).json(); break
            except Exception as e: print(e); time.sleep(10)
        for r in j.get('data', []):
            a, b, c = r[0].strip().split('/'); f = lambda x: float(x.replace(',', ''))
            rows.append(dict(date=f'{int(a)+1911}-{b}-{c}', open=f(r[1]), high=f(r[2]), low=f(r[3]), close=f(r[4])))
        time.sleep(2.5)
    print(y, len(rows), flush=True)
pd.DataFrame(rows).to_json('old_taiex.json', orient='records')
