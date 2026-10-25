# 探測三大法人資料格式（證交所 T86、櫃買），只印結構
import requests, json, time
H = {'User-Agent': 'Mozilla/5.0'}
def show(name, url):
    try:
        r = requests.get(url, headers=H, timeout=30); print(f'\n### {name}\n{url}\nHTTP {r.status_code} len={len(r.text)}')
        try: j = r.json()
        except Exception: print('非 JSON：', r.text[:300]); return
        print('keys', list(j)[:15], 'stat', j.get('stat'))
        if 'fields' in j: print('fields', j['fields']); print('data0', (j.get('data') or [None])[0])
        for t in j.get('tables', [])[:3]: print('table', t.get('title'), 'fields', t.get('fields'), 'n', len(t.get('data') or []), 'row0', (t.get('data') or [None])[0])
        if 'aaData' in j: print('aaData n', len(j['aaData']), 'row0', j['aaData'][0] if j['aaData'] else None, 'iTotal', j.get('iTotalRecords'))
        for k in ('reportDate', 'date', 'title'): 
            if k in j: print(k, j[k])
    except Exception as e: print(name, '錯誤', e)
    time.sleep(4)
for d in ('20140107', '20180105', '20221012', '20261022'):
    show(f'TWSE T86 {d}', f'https://www.twse.com.tw/rwd/zh/fund/T86?date={d}&selectType=ALLBUT0999&response=json')
for d in ('2014/01/07', '2018/01/05', '2022/10/12', '2026/10/22'):
    y, m, dd = d.split('/'); roc = f'{int(y) - 1911}/{m}/{dd}'
    show(f'TPEx 新版 {d}', f'https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={d}&response=json')
    show(f'TPEx 舊版 {d}', f'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&se=EW&t=D&d={roc}&o=json')
