import requests, time, json
U = 'https://api.finmindtrade.com/api/v4/data'; out = {}
def q(name, **p):
    try:
        r = requests.get(U, params=p, timeout=60); j = r.json(); d = j.get('data') or []
        out[name] = dict(http=r.status_code, msg=j.get('msg'), n=len(d), first=d[:1], last=d[-1:])
    except Exception as e: out[name] = str(e)
    print(name, json.dumps(out[name], ensure_ascii=False)[:600], flush=True); time.sleep(2)
q('台積電 2000 股價', dataset='TaiwanStockPrice', data_id='2330', start_date='1999-12-28', end_date='2000-01-10')
q('台積電 1994 股價', dataset='TaiwanStockPrice', data_id='2330', start_date='1994-01-01', end_date='1994-01-31')
q('全市場單日 2000-01-05', dataset='TaiwanStockPrice', start_date='2000-01-05', end_date='2000-01-05')
q('下市清單', dataset='TaiwanStockDelisting', start_date='1995-01-01')
q('台積電 營收 2000', dataset='TaiwanStockMonthRevenue', data_id='2330', start_date='1999-01-01', end_date='2003-12-31')
q('還原股價 2330 2000', dataset='TaiwanStockPriceAdj', data_id='2330', start_date='2000-01-01', end_date='2000-01-10')
q('除權息 2330', dataset='TaiwanStockDividendResult', data_id='2330', start_date='1998-01-01', end_date='2003-12-31')
q('股票清單', dataset='TaiwanStockInfo')
json.dump(out, open('probe_finmind.json', 'w'), ensure_ascii=False, indent=1, default=str)
