# 風險模組資料來源探測
import requests, json, re, time
H = {'User-Agent': 'Mozilla/5.0'}
def show(name, url, method='get', data=None, enc=None, n=600):
    try:
        r = requests.post(url, data=data, headers=H, timeout=60) if method == 'post' else requests.get(url, headers=H, timeout=60)
        if enc: r.encoding = enc
        print(f'\n### {name}\nHTTP {r.status_code} len={len(r.content)} type={r.headers.get("content-type")}', flush=True)
        try:
            j = r.json(); print('keys', list(j)[:10] if isinstance(j, dict) else type(j).__name__, 'stat', j.get('stat') if isinstance(j, dict) else '')
            if isinstance(j, dict):
                for t in (j.get('tables') or [])[:8]:
                    if t.get('data'): print(' table', t.get('title'), t.get('fields'), len(t['data']), t['data'][:2])
                if j.get('data'): print(' data', j.get('fields'), len(j['data']), j['data'][:2])
                if 'chart' in j: res = j['chart']['result'][0]; print(' yahoo n', len(res['timestamp']), res['timestamp'][:2], res['indicators']['quote'][0]['close'][:2])
        except Exception:
            t = re.sub(r'\s+', ' ', r.text); print(t[:n])
    except Exception as e: print(name, '錯誤', repr(e))
    time.sleep(3)
show('加權指數 OHLC 2006-01', 'https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date=20060101&response=json')
show('大盤成交量值 2006-01', 'https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date=20060101&response=json')
show('三大法人買賣金額 2006-01-03', 'https://www.twse.com.tw/rwd/zh/fund/BFI82U?type=day&dayDate=20060103&response=json')
show('融資融券 2006-01-03', 'https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date=20060103&selectType=MS&response=json')
show('類股指數 MI_INDEX IND 2006-01-03', 'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20060103&type=IND&response=json')
show('類股指數 MI_INDEX 2008-06-02 預設', 'https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20080602&type=MS&response=json')
show('類股指數歷史 BFIAMU?', 'https://www.twse.com.tw/rwd/zh/afterTrading/BFIAMU?date=20060103&response=json')
for d in ('2007/07/02', '2010/01/04', '2001/01/02'):
    show(f'期交所 三大法人期貨 CSV {d}', 'https://www.taifex.com.tw/cht/3/futContractsDateDown', 'post', {'queryStartDate': d, 'queryEndDate': d, 'commodityId': 'TXF'}, enc='big5', n=900)
show('期交所 三大法人期貨 區間 CSV 2008-01', 'https://www.taifex.com.tw/cht/3/futContractsDateDown', 'post', {'queryStartDate': '2008/01/02', 'queryEndDate': '2008/01/31', 'commodityId': 'TXF'}, enc='big5', n=600)
show('期交所 期貨總未平倉 TXF 2008-01-02', 'https://www.taifex.com.tw/cht/3/futDataDown', 'post', {'down_type': '1', 'commodity_id': 'TX', 'queryStartDate': '2008/01/02', 'queryEndDate': '2008/01/03'}, enc='big5', n=600)
show('Yahoo ^SOX', 'https://query1.finance.yahoo.com/v8/finance/chart/%5ESOX?period1=1136073600&period2=1767225600&interval=1d')
show('Yahoo ^VIX', 'https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5d&interval=1d')
show('stooq ^SPX', 'https://stooq.com/q/d/l/?s=%5Espx&i=d', n=300)
show('stooq ^SOX', 'https://stooq.com/q/d/l/?s=%5Esox&i=d', n=300)
show('FRED VIXCLS', 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS', n=200)
show('FRED NASDAQCOM', 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM', n=200)
show('FRED SP500', 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500', n=200)
