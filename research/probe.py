# 探測證交所／櫃買「產業價值鏈資訊平台」能否從 GitHub 抓取，存原始 HTML 供解析
import requests, re, os
H = {'User-Agent': 'Mozilla/5.0'}
os.makedirs('pr', exist_ok=True)
for name, url in (('index', 'https://ic.tpex.org.tw/index.php'), ('d000', 'https://ic.tpex.org.tw/introduce.php?ic=D000'), ('stk2327', 'https://ic.tpex.org.tw/company_chain.php?stk_code=2327')):
    try:
        r = requests.get(url, headers=H, timeout=60); r.encoding = r.apparent_encoding
        open(f'pr/{name}.html', 'w').write(r.text); print(name, r.status_code, len(r.text), r.text[:200].replace('\n', ' '), flush=True)
        if name == 'index': print('ic codes', sorted(set(re.findall(r'ic=([A-Z0-9]+)', r.text)))[:80])
    except Exception as e: print(name, '失敗', e)
