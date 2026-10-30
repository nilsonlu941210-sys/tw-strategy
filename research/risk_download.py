# 風險模組歷史資料：python risk_download.py mkt | day 2008 | us | fut
import requests, time, sys, re, datetime as dt, json
import pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}
def num(x):
    try: return float(re.sub(r'[,\s+]', '', str(x)))
    except Exception: return float('nan')
def get(url, **kw):
    for k in range(4):
        try: return requests.get(url, headers=H, timeout=60, **kw).json()
        except Exception as e: print('  重試', k + 1, url, e, flush=True); time.sleep(20 * (k + 1))
    return {}
def roc(s):
    y, m, d = re.findall(r'\d+', s)[:3]; return dt.date(int(y) + 1911, int(m), int(d))
kind = sys.argv[1]; today = dt.date.today()
if kind == 'mkt':   # 加權指數 OHLC + 成交量值（每月一次請求）
    rows = {}
    m = dt.date(2005, 1, 1)
    while m <= today:
        j = get(f'https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={m:%Y%m%d}&response=json'); time.sleep(3)
        for r in j.get('data') or []: rows.setdefault(roc(r[0]), {}).update(open=num(r[1]), high=num(r[2]), low=num(r[3]), close=num(r[4]))
        j = get(f'https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={m:%Y%m%d}&response=json'); time.sleep(3)
        for r in j.get('data') or []: rows.setdefault(roc(r[0]), {}).update(vol=num(r[1]), value=num(r[2]))
        if m.month == 1: print(m, len(rows), flush=True)
        m = (m.replace(day=28) + dt.timedelta(days=5)).replace(day=1)
    pd.DataFrame.from_dict(rows, orient='index').sort_index().rename_axis('date').to_csv('risk_taiex.csv.gz'); print('完成 加權指數', len(rows))
elif kind == 'day':  # 三大法人買賣金額 + 融資融券（每日）
    Y = int(sys.argv[2]); rows = []; d = dt.date(Y, 1, 1)
    while d.year == Y and d <= today:
        if d.weekday() < 5:
            j = get(f'https://www.twse.com.tw/rwd/zh/fund/BFI82U?type=day&dayDate={d:%Y%m%d}&response=json'); time.sleep(3)
            rec = {'date': d}
            for r in j.get('data') or []:
                nm = r[0].strip()
                if '外資' in nm and '自營' not in nm: rec['foreign_net'] = rec.get('foreign_net', 0) + num(r[3])
                elif '外資自營' in nm: rec['foreign_dealer_net'] = num(r[3])
                elif nm.startswith('投信'): rec['trust_net'] = num(r[3])
                elif nm.startswith('自營商'): rec['dealer_net'] = rec.get('dealer_net', 0) + num(r[3])
                elif '合計' in nm: rec['total_net'] = num(r[3])
            if len(rec) > 1:
                k = get(f'https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={d:%Y%m%d}&selectType=MS&response=json'); time.sleep(3)
                for t in k.get('tables') or []:
                    for r in t.get('data') or []:
                        if str(r[0]).startswith('融資金額'): rec['margin_amt'] = num(r[5])
                        elif str(r[0]).startswith('融資('): rec['margin_units'] = num(r[5])
                        elif str(r[0]).startswith('融券('): rec['short_units'] = num(r[5])
                rows.append(rec)
                if len(rows) % 50 == 0: print(d, len(rows), rec, flush=True)
        d += dt.timedelta(days=1)
    pd.DataFrame(rows).to_csv(f'risk_day_{Y}.csv.gz', index=False); print('完成', Y, len(rows))
elif kind == 'us':  # Yahoo 美股
    out = {}
    for sym, nm in (('^SOX', 'SOX'), ('^IXIC', 'NASDAQ'), ('^GSPC', 'SP500'), ('^VIX', 'VIX'), ('NQ=F', 'NQ_FUT'), ('^TNX', 'UST10Y')):
        j = get(f'https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}?period1=1104537600&period2={int(time.time())}&interval=1d')
        try:
            res = j['chart']['result'][0]; q = res['indicators']['quote'][0]
            s = pd.Series(q['close'], index=pd.to_datetime(res['timestamp'], unit='s').tz_localize('UTC').tz_convert('America/New_York').date)
            out[nm] = s[~s.index.duplicated(keep='last')]; print(nm, len(s), s.index[0], s.index[-1], flush=True)
        except Exception as e: print(nm, '失敗', e)
        time.sleep(3)
    pd.DataFrame(out).rename_axis('date').sort_index().to_csv('risk_us.csv.gz'); print('完成 美股')
elif kind == 'fut':  # 期交所三大法人台指期（近 3 年）
    rows = []; d = today - dt.timedelta(days=3 * 365 - 5)
    while d <= today:
        e = min(d + dt.timedelta(days=27), today)
        r = requests.post('https://www.taifex.com.tw/cht/3/futContractsDateDown', data={'queryStartDate': f'{d:%Y/%m/%d}', 'queryEndDate': f'{e:%Y/%m/%d}', 'commodityId': 'TXF'}, headers=H, timeout=60)
        r.encoding = 'big5'
        for line in r.text.splitlines()[1:]:
            c = line.split(',')
            if len(c) > 14 and '外資' in c[2]: rows.append(dict(date=c[0], foreign_oi_net=num(c[13]), foreign_oi_net_amt=num(c[14]), foreign_trade_net=num(c[5])))
        print(d, len(rows), flush=True); d = e + dt.timedelta(days=1); time.sleep(4)
    pd.DataFrame(rows).to_csv('risk_fut.csv.gz', index=False); print('完成 期貨', len(rows))
