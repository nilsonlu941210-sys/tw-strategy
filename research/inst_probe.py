# 探測櫃買三大法人資料的起始年份
import requests, time
H = {'User-Agent': 'Mozilla/5.0'}
for d in ('2013/03/05', '2014/03/05', '2014/06/04', '2014/12/03', '2015/03/04', '2015/06/03', '2016/03/02', '2017/03/01', '2019/03/06', '2020/03/04', '2021/03/03', '2022/03/02'):
    try:
        j = requests.get(f'https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={d}&response=json', headers=H, timeout=30).json()
        t = [x for x in j.get('tables', []) if x.get('data')]
        print(d, 'stat', j.get('stat'), 'rows', len(t[0]['data']) if t else 0, 'ncol', len(t[0]['fields']) if t else None, 'row', t[0]['data'][5] if t else None)
    except Exception as e: print(d, '錯誤', e)
    time.sleep(4)
