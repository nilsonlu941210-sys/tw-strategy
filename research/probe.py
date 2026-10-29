# 看每日重大訊息的欄位，以及「公開收購」相關公告長什麼樣
import requests, json
H = {'User-Agent': 'Mozilla/5.0'}
for url in ('https://openapi.twse.com.tw/v1/opendata/t187ap04_L', 'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O'):
    x = requests.get(url, headers=H, timeout=60).json()
    print('\n###', url, '筆數', len(x)); print(json.dumps(x[:2], ensure_ascii=False)[:1200])
    for r in x:
        s = json.dumps(r, ensure_ascii=False)
        if '收購' in s: print('  收購 →', s[:700])
