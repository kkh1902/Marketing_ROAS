import pandas as pd

# train 데이터를 DataFrame으로 읽기 (처음 2줄)
df = pd.read_csv('data/train.gz', nrows=2)
print(df)
