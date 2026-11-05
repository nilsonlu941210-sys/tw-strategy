# ORB 研究：用永豐 Shioaji 下載個股 1 分 K（2020-03 起）
# 股票範圍：每季成交金額前 100 名（orb_universe.json，時點正確），只抓該檔在名單內那一季（含前 1 個月暖身）
# 進度存在 orb-data 分支，每天自動接續；用量快滿就停，隔天再跑
import os, sys, json, time, subprocess, datetime as dt
import pandas as pd, shioaji as sj

OUT = 'out'; K = f'{OUT}/k'; os.makedirs(K, exist_ok=True)
LOG = open(f'{OUT}/log.txt', 'a')
def log(*a):
    s = dt.datetime.now().strftime('%m-%d %H:%M ') + ' '.join(map(str, a)); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()
def push(msg):
    for c in ('git add -A', f'git commit -qm "{msg}"', 'git push -q origin HEAD:orb-data'): subprocess.run(c, shell=True, cwd=OUT)

U = json.load(open('research/orb_universe.json'))
qs = sorted(U['quarters']); tasks = []
for j, q in enumerate(qs):
    a = (pd.Timestamp(q) - pd.DateOffset(months=1)).date()
    z = (pd.Timestamp(qs[j + 1]) - pd.Timedelta(days=1)).date() if j + 1 < len(qs) else dt.date.today()
    tasks += [(r, s, q, str(a), str(z)) for r, s in enumerate(U['quarters'][q])]
tasks = [t[1:] for t in sorted(tasks)]   # 先抓每季成交金額前段的股票，幾天內就有完整 2020–2026 可先回測
prog_f = f'{OUT}/prog.json'
prog = json.load(open(prog_f)) if os.path.exists(prog_f) else dict(done=[], miss=[], empty=[])
done = set(prog['done']) | set(prog['miss']) | set(prog['empty'])
todo = [t for t in tasks if f'{t[0]}_{t[1]}' not in done]
log('總工作', len(tasks), '已完成', len(tasks) - len(todo))

api = sj.Shioaji()
A, B = os.environ['SJ_API_KEY'].strip(), os.environ['SJ_SECRET_KEY'].strip()
log('金鑰長度', len(A), len(B))
try: api.login(api_key=A, secret_key=B); log('登入成功（金鑰順序正確）')
except Exception as e:
    log('第一次登入失敗，改用相反順序再試：', str(e)[:200])
    api = sj.Shioaji(); api.login(api_key=B, secret_key=A); log('登入成功（兩個金鑰填反了，已自動對調）')
def usage():
    try: u = api.usage(); return u.bytes, u.limit_bytes, u.remaining_bytes
    except Exception as e: log('用量查詢失敗', e); return None
time.sleep(10)
try: api.fetch_contracts(contract_download=True)
except Exception as e: log('合約下載', e)
log('合約檢查 2330', api.Contracts.Stocks['2330'])
u0 = usage(); log('用量（已用, 上限, 剩餘 bytes）', u0)
if u0 and u0[1] and u0[2] < 0.05 * u0[1]: log('今日用量尚未重置，這次先不抓'); api.logout(); sys.exit(0)

# 加權指數 1 分 K（做空研究的大盤條件用），只抓一次
if not os.path.exists(f'{K}/TSE001_index.csv.gz'):
    try:
        ix = None
        for get in (lambda: api.Contracts.Indexs.TSE['TSE001'], lambda: api.Contracts.Indexs.TSE.TSE001, lambda: api.Contracts.Indexs['TSE']['001']):
            try:
                ix = get()
                if ix is not None and hasattr(ix, 'code'): break
                ix = None
            except Exception: pass
        if ix is None:
            try: ix = next((c for c in api.Contracts.Indexs.TSE if getattr(c, 'code', '') in ('001', 'TSE001') or '加權' in getattr(c, 'name', '')), None)
            except Exception as e: log('列舉指數失敗', e)
        log('加權指數合約', ix)
        if ix is None: log('找不到加權指數合約，可用代碼前幾個：', [c.code for c in list(api.Contracts.Indexs.TSE)[:10]])
        parts = []
        for y in range(2020, dt.date.today().year + 1):
            kb = api.kbars(ix, start=f'{y}-01-01' if y > 2020 else '2020-03-02', end=f'{y}-12-31' if y < dt.date.today().year else str(dt.date.today()))
            parts.append(pd.DataFrame({**kb})); time.sleep(1)
        d = pd.concat(parts); d['ts'] = pd.to_datetime(d.ts); d.to_csv(f'{K}/TSE001_index.csv.gz', index=False); log('加權指數 1 分 K', len(d), d.ts.min(), d.ts.max())
    except Exception as e: log('加權指數下載失敗', e)
T0 = time.time(); n = 0
for s, q, a, z in todo:
    if time.time() - T0 > 5 * 3600: log('達到時間上限'); break
    key = f'{s}_{q}'
    try: c = api.Contracts.Stocks[s]
    except Exception: c = None
    if c is None: prog['miss'].append(key); log('找不到合約（可能已下市）', s); continue
    for k in range(3):
        try: kb = api.kbars(c, start=a, end=z); break
        except Exception as e: log('錯誤', key, e); time.sleep(20 * (k + 1)); kb = None
    if kb is None: log('多次失敗，先停下', key); break
    df = pd.DataFrame({**kb})
    if df.empty: prog['empty'].append(key)
    else:
        df['ts'] = pd.to_datetime(df.ts)
        df.to_csv(f'{K}/{key}.csv.gz', index=False); prog['done'].append(key)
    n += 1; time.sleep(0.3)
    if n % 50 == 0:
        u = usage(); log(n, key, '用量', u)
        json.dump(prog, open(prog_f, 'w')); push(f'進度 {len(prog["done"])}/{len(tasks)}')
        if u and u[2] is not None and u[1] and u[2] < 0.05 * u[1]: log('今日用量快滿，明天繼續'); break
prog['total'] = len(tasks); prog['final'] = len(prog['done']) + len(prog['miss']) + len(prog['empty']) >= len(tasks)
json.dump(prog, open(prog_f, 'w')); log('本次完成', n, '累計', len(prog['done']), '/', len(tasks), '用量', usage())
push(f'進度 {len(prog["done"])}/{len(tasks)}')
api.logout()
