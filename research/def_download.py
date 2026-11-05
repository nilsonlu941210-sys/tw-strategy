# 防禦型資產日資料：美股 ETF（yfinance，含息還原）＋台幣匯率＋台灣掛牌債券／黃金 ETF（FinMind）
import os, json, subprocess, time, requests, pandas as pd, yfinance as yf
os.makedirs('out', exist_ok=True)
tk = ['GLD', 'TLT', 'IEF', 'SHY', 'SPY', 'TWD=X']
px = yf.download(tk, start='2004-01-01', auto_adjust=True, progress=False)['Close']
px.to_csv('out/def_us.csv'); print(px.tail(2), px.notna().sum().to_dict())
rows = []
for s in ['00635U', '00679B', '00719B', '00646', '0050']:
    for k in range(5):
        try:
            j = requests.get('https://api.finmindtrade.com/api/v4/data', params=dict(dataset='TaiwanStockPrice', data_id=s, start_date='2010-01-01'), timeout=60).json(); break
        except Exception as e: print(e); time.sleep(20)
    d = j.get('data', []); print(s, len(d)); rows += [dict(date=x['date'], id=s, close=x['close']) for x in d]; time.sleep(3)
    for k in range(5):
        try:
            j = requests.get('https://api.finmindtrade.com/api/v4/data', params=dict(dataset='TaiwanStockDividendResult', data_id=s, start_date='2010-01-01'), timeout=60).json(); break
        except Exception as e: print(e); time.sleep(20)
    for x in j.get('data', []): rows.append(dict(date=x['date'], id=s + '_div', close=x.get('stock_and_cache_dividend')))
    time.sleep(3)
pd.DataFrame(rows).to_csv('out/def_tw.csv', index=False)
for c in ('git init -q', 'git checkout -q -b def-data', 'git config user.name gha', 'git config user.email gha@users.noreply.github.com', 'git add -A', 'git commit -qm data',
          f'git push -qf {os.environ["REPO_URL"]} HEAD:def-data'):
    subprocess.run(c, shell=True, cwd='out')
