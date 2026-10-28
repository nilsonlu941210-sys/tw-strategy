# 每個交易日收盤後由 GitHub Actions 執行：補抓行情與營收 → 更新狀態 → 產生 signals.json 給網頁
import os, sys, json, pickle, time, argparse, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from strategy import *   # noqa

ap = argparse.ArgumentParser(); ap.add_argument('--state', required=True); ap.add_argument('--out', required=True)
args = ap.parse_args()
TZ = dt.timezone(dt.timedelta(hours=8))
now = dt.datetime.now(TZ); today = pd.Timestamp(now.date())
st = pickle.load(open(args.state, 'rb'))
last = st['adj'].index[-1]
print(f'資料最後日期 {last.date()}，今天 {today.date()} {now:%H:%M}')

day = last + pd.Timedelta(days=1); added = 0; log = []
while day <= today and added < 30:
    if day.weekday() < 5 and not (day == today and now.hour < 14):
        try:
            tw = fetch_twse(day); time.sleep(4)
        except Exception as e:
            print(f'  {day.date()} 證交所抓取失敗：{e}'); break
        if tw is not None and len(tw):
            try:
                tp = fetch_tpex(day); time.sleep(4)
            except Exception as e:
                print(f'  {day.date()} 櫃買抓取失敗：{e}'); break
            if tp is None or not len(tp):
                print(f'  {day.date()} 櫃買還沒有資料，下次再補'); break
            both = pd.concat([tw, tp])
            if quarter_of(day) != st['pool_quarter']:
                append_day(st, day, both); st['pool'] = compute_pool(st, len(st['adj']) - 1); st['pool_quarter'] = quarter_of(day)
                print(f'  {day.date()} 新的一季，重新計算 500 檔股票池')
            else:
                append_day(st, day, both)
            print(f'  {day.date()} 上市 {len(tw)} 筆、上櫃 {len(tp)} 筆'); added += 1; log.append(str(day.date()))
        else:
            print(f'  {day.date()} 休市')
    day += pd.Timedelta(days=1)
if added == 0:   # 檢查資料來源是否正常：用最後一個已知交易日再抓一次
    try:
        chk_tw = fetch_twse(last); time.sleep(4); chk_tp = fetch_tpex(last)
        print(f'  檢查：{last.date()} 證交所 {0 if chk_tw is None else len(chk_tw)} 筆、櫃買 {0 if chk_tp is None else len(chk_tp)} 筆')
        both = pd.concat([chk_tw, chk_tp]).drop_duplicates('code').set_index('code')
        cl = st['close'].iloc[-1]; m = both.index.intersection(cl.dropna().index)
        diff = (both.loc[m, 'close'] - cl[m]).abs()
        print(f'  檢查：收盤價與已存資料相符 {int((diff < 1e-6).sum())}/{len(m)} 檔')
        if CORE in both.index and (CORE not in st['close'].columns or pd.isna(st['close'][CORE].iloc[-1])):
            st['close'].loc[st['close'].index[-1], CORE] = both.loc[CORE, 'close']; st['names'][CORE] = '國泰台灣科技龍頭'
            print(f"  補上 {CORE} 價格 {both.loc[CORE, 'close']}")
        for c in ('2330', '2454', '6214', '3081', '00881'):
            if c in both.index: print(f"    {c} 收盤 {both.loc[c, 'close']} 漲跌 {both.loc[c, 'chg']} 成交金額 {both.loc[c, 'money']:,.0f} 已存收盤 {cl.get(c)}")
    except Exception as e:
        print(f'  檢查失敗：{e}')
update_revenue(st, today)

# ---- 產生網頁資料 ----
s = signals(st); d = s['date']; px = st['close'].ffill().iloc[-1]
idx = st['adj'].index
if st.get('core_anchor') is None: st['core_anchor'] = d
n_since = int((idx > st['core_anchor']).sum())
nm = lambda c: st['names'].get(c, '')
f = lambda x, k=4: None if x is None or not np.isfinite(x) else round(float(x), k)
buys = s['score'][s['SIG']].dropna().sort_values(ascending=False)
pool_info = {}
for c in st['pool']:
    if c not in st['adj'].columns: continue
    ok = bool(s['HOLD'].get(c, False))
    why = '' if ok else ('營收轉弱' if not (s['rnh'].get(c, np.nan) > HOLD_RNH) else ('股價離一年高點超過 15%' if not (s['h250'].get(c, np.nan) >= HOLD_H250) else '當天無成交或資料不足'))
    pool_info[c] = dict(n=nm(c), hold=ok, why=why, rnh=f(s['rnh'].get(c)), h250=f(s['h250'].get(c)), sc=f(s['score'].get(c), 3))
hist = st.get('history', [])
today_rec = dict(date=str(d.date()), buys=[dict(c=c, n=nm(c)) for c in buys.index[:12]])
hist = [h for h in hist if h['date'] != today_rec['date']] + [today_rec]; st['history'] = hist[-30:]
out = dict(
    date=str(d.date()), generated=now.strftime('%Y-%m-%d %H:%M'), pool_quarter=st['pool_quarter'], pool_size=len(st['pool']),
    params=dict(sat_n=SAT_N, sat_w=SAT_W, core=CORE, core_w=CORE_W, core_k=CORE_K, hold_h250=HOLD_H250, hold_rnh=HOLD_RNH, brk=BRK_LB, swap_k=SWAP_K),
    core=dict(code=CORE, name=nm(CORE) or '國泰台灣科技龍頭', price=f(px.get(CORE), 2), days_since=n_since % CORE_K, rebalance_today=(n_since % CORE_K == 0)),
    buys=[dict(c=c, n=nm(c), price=f(px[c], 2), rnh=f(s['rnh'][c]), h250=f(s['h250'][c]), score=f(buys[c], 3)) for c in buys.index],
    pool=pool_info,
    prices={c: f(v, 2) for c, v in px.dropna().items()},
    names={c: nm(c) for c in px.dropna().index},
    history=st['history'], added_days=log,
    latest_revenue=str(st['revenue'].assign(k=st['revenue'].revenue_year * 100 + st['revenue'].revenue_month).k.max()),
)
os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(out, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pickle.dump(st, open(args.state + '.tmp', 'wb'), protocol=4); os.replace(args.state + '.tmp', args.state)
print(f'完成：{d.date()} 買進候選 {len(buys)} 檔，新增 {added} 天')
