# 總體經濟資料：FRED 月資料＋S&P 500、加權指數長期日資料
import os, subprocess, io, time, requests, pandas as pd, yfinance as yf
os.makedirs('out', exist_ok=True)
for sid in ['BAA', 'GS10', 'TB3MS', 'UNRATE', 'USREC', 'BAMLH0A0HYM2', 'T10Y3M']:
    for k in range(5):
        try:
            r = requests.get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}', timeout=60); r.raise_for_status()
            open(f'out/fred_{sid}.csv', 'w').write(r.text); print(sid, len(r.text.splitlines())); break
        except Exception as e: print(sid, e); time.sleep(15)
def h(t):
    x = yf.Ticker(t).history(start='1950-01-01', auto_adjust=False)['Close']; x.index = x.index.tz_localize(None).normalize(); return x
px = pd.concat({t: h(t) for t in ('^GSPC', '^TWII')}, axis=1)
px.to_csv('out/idx.csv'); print(px.notna().sum().to_dict(), px.index.min())
for c in ('git init -q', 'git checkout -q -b macro-data', 'git config user.name gha', 'git config user.email gha@users.noreply.github.com', 'git add -A', 'git commit -qm data',
          f'git push -qf {os.environ["REPO_URL"]} HEAD:macro-data'):
    subprocess.run(c, shell=True, cwd='out')
