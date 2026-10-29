# 列出證交所、櫃買 OpenAPI 所有端點，找：公開收購、全額交割/變更交易方法、停止交易、終止上市
import requests, json, re
H = {'User-Agent': 'Mozilla/5.0'}
KEY = re.compile(r'收購|全額|變更交易|停止|暫停|終止|下市|處置|注意')
res = {}
for nm, url in (('twse', 'https://openapi.twse.com.tw/v1/swagger.json'), ('tpex', 'https://www.tpex.org.tw/openapi/swagger.json')):
    try:
        j = requests.get(url, headers=H, timeout=60).json(); res[nm] = j
        for p, v in j.get('paths', {}).items():
            for m, d in v.items():
                s = (d.get('summary') or '') + ' ' + (d.get('description') or '')
                if KEY.search(s): print(nm, p, '|', s.strip()[:80])
        print(nm, '端點數', len(j.get('paths', {})))
    except Exception as e: print(nm, '錯誤', e)
# 實際抓幾個看內容
for nm, p in res.items():
    base = 'https://openapi.twse.com.tw/v1' if nm == 'twse' else 'https://www.tpex.org.tw/openapi/v1'
    for path, v in p.get('paths', {}).items():
        d = list(v.values())[0]; s = (d.get('summary') or '') + ' ' + (d.get('description') or '')
        if KEY.search(s):
            try:
                x = requests.get(base + path, headers=H, timeout=60).json()
                print('\n###', nm, path, s.strip()[:60], '筆數', len(x) if isinstance(x, list) else type(x).__name__)
                print(json.dumps(x[:2] if isinstance(x, list) else x, ensure_ascii=False)[:600])
            except Exception as e: print('###', nm, path, '錯誤', e)
json.dump({k: list(v.get('paths', {}).keys()) for k, v in res.items()}, open('openapi_paths.json', 'w'), ensure_ascii=False)
