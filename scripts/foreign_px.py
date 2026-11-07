# 複委託標的價格：美元收盤 × 美元兌台幣，寫進 signals.json 的 prices（每股台幣價）
import json, argparse, yfinance as yf, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument('--signals', required=True); a = ap.parse_args()
S = json.load(open(a.signals, encoding='utf-8'))
fx = yf.Ticker('TWD=X').history(period='1mo')['Close'].dropna()
fx = fx[(fx > 25) & (fx < 40)]          # Yahoo 匯率偶有異常值
rate = float(fx.iloc[-1])
OTH = S['params'].get('other', {})
for code in [c for c in list(S['params'].get('defs', {})) + list(OTH) if not c[0].isdigit()]:
    px = yf.Ticker(code).history(period='1mo')['Close'].dropna()
    S['prices'][code] = round(float(px.iloc[-1]) * rate, 2); S['names'][code] = S['params']['def_names'].get(code) or OTH.get(code, code)
    print(code, 'USD', round(float(px.iloc[-1]), 2), '× 匯率', round(rate, 3), '=', S['prices'][code], '元／股（', px.index[-1].date(), '）')
S['params']['usdtwd'] = round(rate, 3)
json.dump(S, open(a.signals, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
