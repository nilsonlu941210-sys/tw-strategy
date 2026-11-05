# 每天盤後產生「明日當沖觀察名單」：成交金額前 15 名（65 元以下、排除金控）的重要價位與方向傾向
# 只整理資料給人判斷，這些傾向沒有經過回測驗證（v50–v52 的機械式做空/突破都沒通過）
import os, sys, json, pickle, math, datetime as dt
import numpy as np, pandas as pd

ap = __import__('argparse').ArgumentParser(); ap.add_argument('--state', required=True); ap.add_argument('--signals', required=True)
args = ap.parse_args()
FIN = {'2880', '2881', '2882', '2883', '2884', '2885', '2886', '2887', '2888', '2889', '2890', '2891', '2892', '5880'}
MAXPX, N, FEE = 65, 15, 0.000399 * 2 + 0.0015
def tick(p): return 0.01 if p < 10 else 0.05 if p < 50 else 0.1 if p < 100 else 0.5
def rt(x, p): t = tick(p); return round(round(x / t) * t, 2)

st = pickle.load(open(args.state, 'rb'))
money, close = st['money'], st['close']
m60 = money.iloc[-60:]; avg = m60.mean().where(m60.notna().sum() >= 48)
last = close.ffill().iloc[-1]
ok = [c for c in avg.dropna().index if len(c) == 4 and c[0] != '0' and c not in FIN and last.get(c, 1e9) <= MAXPX]
cands = avg[ok].sort_values(ascending=False).index[:N].tolist()
print('觀察名單', cands)

items = []; err = None
try:
    import shioaji as sj
    api = sj.Shioaji(); A, B = os.environ['SJ_API_KEY'].strip(), os.environ['SJ_SECRET_KEY'].strip()
    try: api.login(api_key=A, secret_key=B)
    except Exception: api = sj.Shioaji(); api.login(api_key=B, secret_key=A)
    end = dt.date.today(); start = end - dt.timedelta(days=25)
    for c in cands:
        try:
            k = api.Contracts.Stocks[c]
            x = pd.DataFrame({**api.kbars(k, start=str(start), end=str(end))})
            if x.empty: continue
            x['ts'] = pd.to_datetime(x.ts); x['d'] = x.ts.dt.date; x['hr'] = x.ts.dt.hour - (x.ts.dt.minute == 0)
            D = x.groupby('d').agg(O=('Open', 'first'), H=('High', 'max'), L=('Low', 'min'), C=('Close', 'last'))
            if len(D) < 6: continue
            C, Hh, Ll = D.C.iloc[-1], D.H.iloc[-1], D.L.iloc[-1]
            rng = ((D.H - D.L) / D.C.shift()).dropna().iloc[-10:].mean()
            # 前 5 日 60 分 K 波段高低點
            b = x[x.d.isin(D.index[-5:])].groupby(['d', 'hr']).agg(H=('High', 'max'), L=('Low', 'min')).reset_index()
            ph = [b.H[i] for i in range(2, len(b) - 2) if b.H[i] > max(b.H[i - 2:i].max(), b.H[i + 1:i + 3].max())]
            pl = [b.L[i] for i in range(2, len(b) - 2) if b.L[i] < min(b.L[i - 2:i].min(), b.L[i + 1:i + 3].min())]
            lv = set([Hh, Ll, D.H.iloc[-5:].max(), D.L.iloc[-5:].min()] + ph + pl)
            res = sorted({rt(v, C) for v in lv if v > C * 1.001})[:3]; sup = sorted({rt(v, C) for v in lv if v < C * 0.999}, reverse=True)[:3]
            s = close[c].dropna(); ma20, ma60 = s.rolling(20).mean(), s.rolling(60).mean()
            up = ma20.iloc[-1] > ma20.iloc[-6]; cc = s.iloc[-1]
            trend = ('多頭排列' if cc > ma20.iloc[-1] > ma60.iloc[-1] and up else '空頭排列' if cc < ma20.iloc[-1] < ma60.iloc[-1] and not up
                     else '均線之上' if cc > ma20.iloc[-1] else '均線之下')
            pos = (C - Ll) / (Hh - Ll) if Hh > Ll else 0.5
            bias = '偏空' if (trend == '空頭排列' or (trend == '均線之下' and pos < 0.3)) else '偏多' if (trend == '多頭排列' or (trend == '均線之上' and pos > 0.7)) else '觀望'
            dtd = getattr(k, 'day_trade', None); dtd = str(getattr(dtd, 'value', dtd) or '')
            items.append(dict(c=c, n=st['names'].get(c, '') or getattr(k, 'name', ''), close=float(C), chg=float(C / D.C.iloc[-2] - 1), rng=float(rng),
                              trend=trend, pos=float(pos), bias=bias, res=[float(v) for v in res], sup=[float(v) for v in sup],
                              ticks=int(math.floor(C * FEE / tick(C))) + 1, tick=tick(C), r5=float(C / D.C.iloc[-6] - 1),
                              short_ok={'Yes': '可先賣', 'OnlyBuy': '只能先買', 'No': '不可當沖'}.get(dtd, dtd)))
        except Exception as e: print('  ', c, '失敗', e)
    api.logout()
except Exception as e:
    err = str(e)[:200]; print('永豐資料取得失敗：', err)

items.sort(key=lambda r: -r['rng'])
S = json.load(open(args.signals, encoding='utf-8'))
S['dt'] = dict(date=S.get('date'), items=items, err=err, rule=f'前 60 日平均成交金額前 {N} 名、收盤 ≤ {MAXPX} 元、排除金控')
json.dump(S, open(args.signals, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('完成', len(items), '檔')
