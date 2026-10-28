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
for d in ('20050701', '20080102', '20121228'):
    show(f'證交所 MI_INDEX {d}', f'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d}&type=ALLBUT0999&response=json')
for d in ('2007/01/02', '2008/01/02', '2012/12/28'):
    show(f'櫃買新版 {d}', f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={d}&type=EW&response=json')
show('櫃買舊版 96/01/02', 'https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d=96/01/02&o=json')
show('櫃買舊版 94/07/01', 'https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d=94/07/01&o=json')
for host in ('mops.twse.com.tw', 'mopsov.twse.com.tw'):
    for mk in ('sii', 'otc'):
        for f in ('t21sc03_96_1.html', 't21sc03_96_1_0.html', 't21sc03_101_12.html', 't21sc03_102_1_0.html'):
            show(f'月營收 {host} {mk} {f}', f'https://{host}/nas/t21/{mk}/{f}', enc='big5')
