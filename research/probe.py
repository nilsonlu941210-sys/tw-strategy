# 探測 2005–2013 舊資料來源：證交所/櫃買每日行情、公開資訊觀測站月營收彙總
import requests, time, re
H = {'User-Agent': 'Mozilla/5.0'}
def show(name, url, enc=None):
    try:
        r = requests.get(url, headers=H, timeout=40); print(f'\n### {name}\n{url}\nHTTP {r.status_code} len={len(r.content)} final={r.url}', flush=True)
        if enc: r.encoding = enc
        try:
            j = r.json()
        except Exception:
            t = r.text; print('非JSON；前 300 字：', re.sub(r'\s+', ' ', t[:300]))
            txt = re.sub(r'<[^>]+>', ' ', t); txt = re.sub(r'\s+', ' ', txt); i = txt.find('2330'); i = i if i >= 0 else txt.find('1101')
            print('含 1101/2330 片段：', txt[max(0, i - 200):i + 400]); return
        print('keys', list(j)[:12], 'stat', j.get('stat'))
        for t in (j.get('tables') or [])[:12]:
            if t.get('data'): print(' table', t.get('title'), t.get('fields'), 'n', len(t['data']), t['data'][:2])
        if 'aaData' in j: print(' aaData', len(j['aaData']), j['aaData'][:2], j.get('iTotalRecords'))
        if isinstance(j.get('data'), list): print(' data', len(j['data']), j['data'][:2], j.get('fields'))
    except Exception as e: print(name, '錯誤', repr(e))
    time.sleep(4)
for d in ('2005/07/01', '2006/03/01', '2006/12/01', '2007/01/03', '2007/03/01', '2007/04/02', '2007/06/01', '2007/07/02', '2007/10/01'):
    show(f'櫃買新版 {d}', f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={d}&type=EW&response=json')
show('櫃買新版 AL 2007/01/03', 'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date=2007/01/03&type=AL&response=json')
show('櫃買 個股日成交 2006', 'https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?code=5483&date=2006/03/01&response=json')
show('櫃買 dailyQ 舊', 'https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQ?date=2006/03/01&response=json')
