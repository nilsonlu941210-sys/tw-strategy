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
    tasks += [(s, q, str(a), str(z)) for s in U['quarters'][q]]
prog_f = f'{OUT}/prog.json'
prog = json.load(open(prog_f)) if os.path.exists(prog_f) else dict(done=[], miss=[], empty=[])
done = set(prog['done']) | set(prog['miss']) | set(prog['empty'])
todo = [t for t in tasks if f'{t[0]}_{t[1]}' not in done]
log('總工作', len(tasks), '已完成', len(tasks) - len(todo))

api = sj.Shioaji()
api.login(api_key=os.environ['SJ_API_KEY'], secret_key=os.environ['SJ_SECRET_KEY'], contracts_timeout=300000)
def usage():
    try: u = api.usage(); return u.bytes, u.limit_bytes, u.remaining_bytes
    except Exception as e: log('用量查詢失敗', e); return None
log('用量（已用, 上限, 剩餘 bytes）', usage())

T0 = time.time(); n = 0
for s, q, a, z in todo:
    if time.time() - T0 > 5 * 3600: log('達到時間上限'); break
    key = f'{s}_{q}'
    c = api.Contracts.Stocks.get(s)
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
