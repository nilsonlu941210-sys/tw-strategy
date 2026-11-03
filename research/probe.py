import requests, time, json, re
H = {'User-Agent': 'Mozilla/5.0'}
out = {}
def get(name, url, enc=None):
    try:
        r = requests.get(url, headers=H, timeout=60)
        if enc: r.encoding = enc
        t = r.text
        try:
            j = r.json(); s = {k: (v if not isinstance(v, list) else f'list[{len(v)}] ' + json.dumps(v[:2], ensure_ascii=False)[:400]) for k, v in j.items() if k in ('stat', 'date', 'title', 'fields', 'data', 'tables')}
            if 'tables' in j: s['tables'] = [(tb.get('title'), len(tb.get('data', []) or []), json.dumps((tb.get('data') or [])[:2], ensure_ascii=False)[:300]) for tb in j['tables']]
        except Exception:
            s = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))[:600]
        out[name] = dict(http=r.status_code, len=len(r.content), body=s)
    except Exception as e:
        out[name] = str(e)
    print(name, json.dumps(out[name], ensure_ascii=False)[:900], flush=True); time.sleep(3)
T = 'https://www.twse.com.tw/rwd/zh'
get('指數OHLC 2000-02', f'{T}/TAIEX/MI_5MINS_HIST?date=20000201&response=json')
get('指數OHLC 1999-01', f'{T}/TAIEX/MI_5MINS_HIST?date=19990101&response=json')
get('全市場個股 2000-01-05', f'{T}/afterTrading/MI_INDEX?date=20000105&type=ALLBUT0999&response=json')
get('全市場個股 2004-02-11', f'{T}/afterTrading/MI_INDEX?date=20040211&type=ALLBUT0999&response=json')
get('全市場個股 2004-02-10', f'{T}/afterTrading/MI_INDEX?date=20040210&type=ALLBUT0999&response=json')
get('個股月資料 2330 2000-01', f'{T}/afterTrading/STOCK_DAY?date=20000101&stockNo=2330&response=json')
get('個股月資料 2330 1999-01', f'{T}/afterTrading/STOCK_DAY?date=19990101&stockNo=2330&response=json')
get('個股月資料 下市股 2491 2000-01', f'{T}/afterTrading/STOCK_DAY?date=20000101&stockNo=2491&response=json')
get('大盤成交 2000-01', f'{T}/afterTrading/FMTQIK?date=20000101&response=json')
get('三大法人 2000-01-05', f'{T}/fund/BFI82U?dayDate=20000105&type=day&response=json')
get('融資 2001-01-05', f'{T}/marginTrading/MI_MARGN?date=20010105&selectType=MS&response=json')
get('每日收盤行情 BWIBBU 2000', f'{T}/afterTrading/BWIBBU_d?date=20000105&selectType=ALL&response=json')
get('終止上市', 'https://www.twse.com.tw/rwd/zh/company/suspendListingCsvAndHtml?type=html', None)
get('MOPS 營收 2000-01 上市', 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_89_1_0.html', 'big5')
get('MOPS 營收 2001-06 上市', 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_90_6_0.html', 'big5')
get('MOPS 營收 2002-01 上市', 'https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_91_1_0.html', 'big5')
get('櫃買 2000 個股', 'https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d=89/01/05&o=json')
json.dump(out, open('probe_2000.json', 'w'), ensure_ascii=False, indent=1)
