import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 2015/01 ~ 2024/12
START_YEAR, START_MONTH = 2015, 1
END_YEAR, END_MONTH = 2024, 12

# 데이터 수집 url 및 api key 설정
BASE_URL = 'http://openapi.seoul.go.kr:8088/{api_key}/json/energyUseDataSummaryInfo/1/5/{year}/{month:02d}'
api_key = 'API_KEY'

total_rows = []

# 데이터 수집
for year in range(START_YEAR, END_YEAR + 1):
    for month in range(START_MONTH, END_MONTH + 1):
        url = BASE_URL.format(api_key=api_key, year=year, month=month)
        res = requests.get(url)

        if res.status_code == 200:
            data = res.json()
            rows = [
                r for r in (data.get('energyUseDataSummaryInfo') or {}).get('row') or []
                if str(r.get('MM_TYPE', '')).strip() == '개인'
            ]
            total_rows.extend(rows)
        else:
            print('API 요청 실패', res.status_code)

# DataFrame
df = pd.DataFrame(total_rows)

# 계절 컬럼 추가
df['MON'] = pd.to_numeric(df['MON']).astype('Int64')
m = df['MON']
df['SEASON'] = np.select(
    [m.isin([3,4,5]), m.isin([6,7,8]), m.isin([9,10,11])],
    ['봄', '여름', '가을'],
    default=' 겨울'
)

# 특정 열만 가져오기
# selected_col = df[['YEAR', 'MON', 'SEASON', 'EUS', 'GUS', 'WUS', 'HUS']]

# 선그래프 그리기
# 연도별 에너지 사용 총 사용량(전기+가스+수도+지역난방)
df_line_chart = df.copy()

num_cols = ['EUS', 'GUS', 'WUS', 'HUS']
df_line_chart[num_cols] = df_line_chart[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
df_line_chart['YEAR'] = pd.to_numeric(df_line_chart['YEAR'], errors='coerce').astype('Int64')

yearly = (
    df_line_chart.dropna(subset=['YEAR'])
        .groupby('YEAR', as_index=False)[num_cols]
        .sum()
        .sort_values('YEAR')
)
yearly['TOTAL_USE'] = yearly[num_cols].sum(axis=1)

plt.figure(figsize=(12, 6))
plt.plot(yearly['YEAR'], yearly['TOTAL_USE'], marker='o')
plt.title('Total Energy Usage by Year')
plt.xlabel('Year')
plt.ylabel('Total Usage')
plt.grid(True)
plt.show()

# 막대그래프
# 계절별 가스 사용량 평균
df_bar_chart = df.copy()
df_bar_chart['GUS'] = pd.to_numeric(df_bar_chart['GUS'], errors='coerce')
df_bar_chart['SEASON'] = df_bar_chart['SEASON'].astype(str).str.strip()

season_order = ['봄', '여름', '가을', '겨울']
category = pd.CategoricalDtype(categories=season_order, ordered=True)

season_avg = (
    df_bar_chart.dropna(subset=['SEASON', 'GUS'])
        .assign(SEASON=lambda x: x['SEASON'].astype(category))
        .groupby('SEASON', as_index=False)['GUS']
        .mean()
        .sort_values('SEASON')
)

plt.figure()
bars = plt.bar(season_avg['SEASON'], season_avg['GUS'])
plt.title('Seasonal gas usage')
plt.xlabel('Season')
plt.ylabel('Average gas usage')

for b in bars:
    h = b.get_height()
    plt.text(b.get_x() + b.get_width()/2, h, f'{h:,.0f}', ha='center', va='bottom')

plt.tight_layout()
plt.show()