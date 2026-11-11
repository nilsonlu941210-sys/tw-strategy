# 下載證交所／櫃買「產業價值鏈資訊平台」全部產業鏈的子產業與公司對照（目前版本）
import requests, re, os, time, html, csv
H = {'User-Agent': 'Mozilla/5.0'}
os.makedirs('pr', exist_ok=True)
idx = requests.get('https://ic.tpex.org.tw/index.php', headers=H, timeout=60).text
codes = sorted(set(re.findall(r'ic=([A-Z0-9]{4})', idx)))
NM = dict(re.findall(r"<option value='(\w+)'[^>]*>([^<]+)</option>", requests.get('https://ic.tpex.org.tw/company_chain.php?stk_code=2327', headers=H, timeout=60).text))
rows = []
for ic in codes:
    t = ''
    for k in range(4):
        try: t = requests.get(f'https://ic.tpex.org.tw/introduce.php?ic={ic}', headers=H, timeout=90).text
        except Exception as e: print(ic, '失敗', e)
        if 'sc_company_' in t: break
        time.sleep(10 * (k + 1))
    open(f'pr/{ic}.html', 'w').write(t)
    chain = NM.get(ic) or (re.findall(r'<title>\s*產業價值鏈資訊平台\s*&gt;\s*(.*?)產業鏈簡介', t) or re.findall(r'產業價值鏈資訊平台 > (.*?)產業鏈簡介', t) or [ic])[0].strip()
    names = {k: html.unescape(re.sub(r'<[^>]+>', '', v)).replace('\xa0', ' ').strip() for k, v in re.findall(r'id="sc_link_(\w+)"[^>]*>(.*?)</div>', t, flags=re.S)}
    for sid, body in re.findall(r'id="sc_company_(\w+)"(.*?)</table>', t, flags=re.S):
        nm = re.sub(r'^\W*', '', names.get(sid, sid)); nm = re.sub(r'\s*\(\d+家\)\s*$', '', nm)
        for s in sorted(set(re.findall(r'stk_code=(\d{4})', body))): rows.append((ic, chain, sid, nm, s))
    print(ic, chain, len(names), '子產業', flush=True); time.sleep(4)
with open('pr/ic_chain.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['ic', 'chain', 'sub_id', 'sub_name', 'stock_id']); w.writerows(rows)
print('總列數', len(rows), '公司數', len({r[4] for r in rows}))
