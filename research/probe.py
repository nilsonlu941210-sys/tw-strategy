import requests, re, time
H = {'User-Agent': 'Mozilla/5.0'}
def show(name, url, data):
    try:
        r = requests.post(url, data=data, headers=H, timeout=60); r.encoding = 'big5' if 'Down' in url else 'utf-8'
        t = re.sub(r'<[^>]+>', ' ', r.text); t = re.sub(r'\s+', ' ', t)
        i = t.find('外資'); print(f'\n### {name} HTTP {r.status_code} len={len(r.content)}\n', t[:300] if i < 0 else t[max(0, i - 300):i + 500], flush=True)
    except Exception as e: print(name, e)
    time.sleep(3)
U = 'https://www.taifex.com.tw/cht/3/futContractsDateDown'
show('CSV 近期 2026/10/29', U, {'queryStartDate': '2026/10/29', 'queryEndDate': '2026/10/29', 'commodityId': 'TXF'})
show('CSV 2024/01/02', U, {'queryStartDate': '2024/01/02', 'queryEndDate': '2024/01/02', 'commodityId': 'TXF'})
show('CSV 2020/01/02', U, {'queryStartDate': '2020/01/02', 'queryEndDate': '2020/01/02', 'commodityId': 'TXF'})
show('CSV 2016/01/04', U, {'queryStartDate': '2016/01/04', 'queryEndDate': '2016/01/04', 'commodityId': 'TXF'})
show('CSV 2023/11/01 無 commodity', U, {'queryStartDate': '2023/11/01', 'queryEndDate': '2023/11/01'})
V = 'https://www.taifex.com.tw/cht/3/futContractsDate'
for d in ('2008/01/02', '2012/01/02', '2018/01/02'):
    show(f'網頁 {d}', V, {'queryType': '1', 'goDay': '', 'doQuery': '1', 'dateaddcnt': '', 'queryDate': d, 'commodityId': 'TXF'})
