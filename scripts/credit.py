# 信用利差（市場溫度計）：FRED 月資料 BAA − GS10（研究 v68／v79 用的訊號）＋每日高收益債利差 HY OAS
# 只供觀察，回測證明不能當買賣訊號（v79）
import argparse, io, json, requests, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--signals', required=True); a = ap.parse_args()
def fred(sid):
    r = requests.get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}', timeout=60); r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text)); d.columns = ['date', 'v']
    d['date'] = pd.to_datetime(d.date); d['v'] = pd.to_numeric(d.v, errors='coerce'); return d.dropna().set_index('date').v
S = json.load(open(a.signals))
try:
    sp = (fred('BAA') - fred('GS10')).dropna(); d6 = sp - sp.shift(6)
    hy = fred('BAMLH0A0HYM2')
    S['credit'] = dict(
        month=str(sp.index[-1].strftime('%Y-%m')), spread=round(float(sp.iloc[-1]), 2), chg6=round(float(d6.iloc[-1]), 2), lit=bool(d6.iloc[-1] >= 0.5),
        hist=[[i.strftime('%Y-%m'), round(float(v), 2)] for i, v in sp[-36:].items()],
        hy_date=str(hy.index[-1].date()), hy=round(float(hy.iloc[-1]), 2), hy_6m=round(float(hy[:hy.index[-1] - pd.Timedelta(days=182)].iloc[-1]), 2),
        hy_hist=[[i.strftime('%Y-%m-%d'), round(float(v), 2)] for i, v in hy[-260:].items()])
    json.dump(S, open(a.signals, 'w'), ensure_ascii=False, separators=(',', ':'))
    print('信用利差', S['credit']['month'], S['credit']['spread'], '6 個月變化', S['credit']['chg6'], '｜HY', S['credit']['hy_date'], S['credit']['hy'])
except Exception as e: print('信用利差抓取失敗：', e)
