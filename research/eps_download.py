# 季報 EPS（FinMind TaiwanStockFinancialStatements，逐檔，2004 起）；每 100 檔推一次進度到 eps-data-<part> 分支（v73）
import sys, os, time, json, subprocess, requests, pandas as pd
U = 'https://api.finmindtrade.com/api/v4/data'
part, nparts = map(int, sys.argv[1].split('/'))
os.makedirs('out', exist_ok=True)
LOG = open('out/log.txt', 'a')
def log(*a):
    s = ' '.join(map(str, a)); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()
def q(**p):
    t0 = time.time()
    while time.time() - t0 < 7200:
        try:
            r = requests.get(U, params=p, timeout=90); j = r.json()
            if j.get('status') == 200: return j.get('data') or []
            log('非 200', r.status_code, j.get('status'), str(j.get('msg'))[:120], p.get('data_id')); time.sleep(300)
        except Exception as e: log('錯誤', e); time.sleep(30)
    return None
def push(final=False):
    pd.DataFrame(out).to_csv(f'out/eps_{part}.csv.gz', index=False)
    json.dump(dict(done=i + 1, total=len(mine), rows=len(out), empty=empty, miss=miss, final=final), open(f'out/prog_{part}.json', 'w'), ensure_ascii=False)
    for c in ('git add -A', f'git commit -qm "進度 {i+1}/{len(mine)}"', f'git push -qf origin HEAD:eps-data-{part}'): subprocess.run(c, shell=True, cwd='out')
subprocess.run('git init -q && git checkout -q -b w && git config user.name gha && git config user.email gha@users.noreply.github.com && git remote add origin ' + os.environ['REPO_URL'], shell=True, cwd='out')
info = q(dataset='TaiwanStockInfo'); dl = q(dataset='TaiwanStockDelisting', start_date='1990-01-01')
ids = sorted({d['stock_id'] for d in info + dl if len(d['stock_id']) == 4 and d['stock_id'].isdigit() and not d['stock_id'].startswith('0') and not d['stock_id'].startswith('91')})
mine = ids[part::nparts]; log('總檔數', len(ids), '本工作', len(mine))

out = []; empty = []; miss = []; i = -1
for i, s in enumerate(mine):
    d = q(dataset='TaiwanStockFinancialStatements', data_id=s, start_date='2004-01-01')
    if d is None: miss.append(s)
    elif not d: empty.append(s)
    else: out += [{k: x[k] for k in ('date', 'stock_id', 'type', 'value', 'origin_name')} for x in d if x.get('type') in ('EPS', 'Revenue', 'GrossProfit', 'IncomeAfterTaxes', 'EquityAttributableToOwnersOfParent')]
    time.sleep(4)
    if (i + 1) % 100 == 0: log(i + 1, s, '筆數', len(out), '空', len(empty), '失敗', len(miss)); push()
push(True); log('完成', len(out), '空', len(empty), '失敗', miss)
