# 下載 2013 起證交所（TWT49U）與櫃買（exDailyQ）除權息計算結果
import requests, time, pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}; rows = []
for Y in range(2013, 2027):
    for k in range(3):
        try:
            j = requests.get(f'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate={Y}0101&endDate={Y}1231&response=json', headers=H, timeout=60).json(); break
        except Exception as e: print('重試', e); time.sleep(20)
    f = j.get('fields', []); n1 = 0
    for r in j.get('data') or []:
        d = r[0].replace('年', '/').replace('月', '/').replace('日', ''); y, m, dd = d.split('/')
        rows.append(dict(date=f'{int(y)+1911}-{int(m):02d}-{int(dd):02d}', stock_id=r[1].strip(), market='twse', prev_close=r[3], ref=r[4], value=r[5], kind=r[6])); n1 += 1
    time.sleep(4)
    for k in range(3):
        try:
            t = requests.get(f'https://www.tpex.org.tw/www/zh-tw/bulletin/exDailyQ?startDate={Y}/01/01&endDate={Y}/12/31&response=json', headers=H, timeout=60).json(); break
        except Exception as e: print('重試', e); time.sleep(20)
    n2 = 0
    for tb in t.get('tables') or []:
        for r in tb.get('data') or []:
            y, m, dd = r[0].split('/')
            rows.append(dict(date=f'{int(y)+1911}-{int(m):02d}-{int(dd):02d}', stock_id=r[1].strip(), market='tpex', prev_close=r[3], ref=r[4], value=r[7], kind=r[8])); n2 += 1
    print(Y, '上市', n1, '上櫃', n2, flush=True); time.sleep(4)
df = pd.DataFrame(rows)
for c in ('prev_close', 'ref', 'value'): df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce')
df.to_csv('dividends.csv.gz', index=False); print('完成', len(df))
print(df[df.stock_id == '00719B'].to_string())
