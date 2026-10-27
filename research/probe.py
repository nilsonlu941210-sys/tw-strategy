# 探測 00719B 歷史漲跌（含除息參考價）與配息資料的來源
import requests, time
H = {'User-Agent': 'Mozilla/5.0'}
def show(name, url):
    try:
        r = requests.get(url, headers=H, timeout=30); print(f'\n### {name}\n{url}\nHTTP {r.status_code} len={len(r.text)}', flush=True)
        try: j = r.json()
        except Exception: print('非JSON', r.text[:300]); return
        print('keys', list(j)[:12], 'stat', j.get('stat'))
        for t in (j.get('tables') or [])[:2]: print(' table', t.get('title'), t.get('fields'), 'n', len(t.get('data') or []), (t.get('data') or [None])[:4])
        if 'aaData' in j: print(' aaData', len(j['aaData']), j['aaData'][:3])
        if isinstance(j.get('data'), list): print(' data', len(j['data']), j['data'][:4], j.get('fields'))
    except Exception as e: print(name, '錯誤', e)
    time.sleep(4)
show('櫃買個股月成交 2023-01', 'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?code=00719B&date=2023/01/01&response=json')
show('櫃買個股月成交 2025-05', 'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?code=00719B&date=2025/05/01&response=json')
show('櫃買除權息計算結果（新）', 'https://www.tpex.org.tw/www/zh-tw/bulletin/exDailyQ?startDate=2023/01/01&endDate=2023/12/31&response=json')
show('櫃買除權息計算結果（舊）', 'https://www.tpex.org.tw/web/stock/exright/dailyquo/exDailyQ_result.php?l=zh-tw&d=112/01/01&ed=112/12/31&o=json')
show('證交所除權息計算結果 TWT49U', 'https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate=20230101&endDate=20231231&response=json')
