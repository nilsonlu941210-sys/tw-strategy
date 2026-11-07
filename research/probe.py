# 探測季報 EPS 資料來源：公開資訊觀測站彙總報表（綜合損益表）與 FinMind
import requests, time, json
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://mopsov.twse.com.tw/mops/web/t163sb04'}
for host in ('https://mopsov.twse.com.tw', 'https://mops.twse.com.tw'):
    for (yr, ss, typ) in ((112, '01', 'sii'), (102, '04', 'otc')):
        try:
            r = requests.post(f'{host}/mops/web/ajax_t163sb04', data=dict(encodeURIComponent=1, step=1, firstin=1, off=1, isQuery='Y', TYPEK=typ, year=yr, season=ss), headers=H, timeout=60)
            t = r.text; print(host, yr, ss, typ, 'HTTP', r.status_code, 'len', len(t), '有EPS欄' if '基本每股盈餘' in t else '無EPS欄', t[:200].replace('\n', ' '), flush=True)
        except Exception as e: print(host, yr, ss, typ, '失敗', e, flush=True)
        time.sleep(3)
try:
    j = requests.get('https://api.finmindtrade.com/api/v4/data', params=dict(dataset='TaiwanStockFinancialStatements', data_id='2317', start_date='2005-01-01'), timeout=60).json()
    d = j.get('data', []); eps = [x for x in d if x.get('type') == 'EPS']
    print('FinMind', j.get('msg'), '筆', len(d), 'EPS 筆', len(eps), eps[:2], eps[-1:] if eps else '', flush=True)
except Exception as e: print('FinMind 失敗', e)
