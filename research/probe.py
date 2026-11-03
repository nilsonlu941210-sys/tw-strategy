import requests, time, json
U = 'https://api.finmindtrade.com/api/v4/data'
for i in range(3):
    for p in (dict(dataset='TaiwanStockInfo'), dict(dataset='TaiwanStockPrice', data_id='9932', start_date='1998-01-01', end_date='2005-12-31'), dict(dataset='TaiwanStockPrice', data_id='2330', start_date='1998-01-01', end_date='2005-12-31')):
        r = requests.get(U, params=p, timeout=90)
        try: j = r.json()
        except Exception: j = {'raw': r.text[:200]}
        d = j.get('data') or []
        print(i, p.get('data_id', p['dataset']), r.status_code, j.get('status'), j.get('msg'), len(d), d[:1], d[-1:], {k: v for k, v in r.headers.items() if 'limit' in k.lower() or 'retry' in k.lower()}, flush=True)
        time.sleep(3)
r = requests.get('https://api.web.finmindtrade.com/v2/user_info', timeout=30); print('user_info', r.status_code, r.text[:300])
