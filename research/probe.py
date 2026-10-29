# 抓臺灣指數公司新聞稿（找台灣50定期審核結果）
import requests, re, time, json
H = {'User-Agent': 'Mozilla/5.0'}
out = []
for i in range(1, 520):
    try:
        r = requests.get(f'https://taiwanindex.com.tw/news/{i}', headers=H, timeout=30)
        t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', r.text, flags=re.S)
        t = re.sub(r'<[^>]+>', ' ', t); t = re.sub(r'\s+', ' ', t)
        out.append(dict(id=i, status=r.status_code, text=t[:20000]))
        if i % 50 == 0: print(i, r.status_code, t[:120], flush=True)
    except Exception as e:
        out.append(dict(id=i, status=-1, text=str(e)))
    time.sleep(1.5)
json.dump(out, open('tip_news.json', 'w'), ensure_ascii=False)
print('完成', sum(o['status'] == 200 for o in out))
