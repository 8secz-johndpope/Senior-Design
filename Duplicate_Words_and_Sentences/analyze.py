import pandas as pd 
import os

df = pd.read_csv('RED_FLAG_LANGUAGE.csv')

total = 0
suspicious = 0
for index, row in df.iterrows():
    if row['Red Flag Words']:
        total += 1
    if row['Red Flag Words'] and row['Red Flag Words'] > 50:
        suspicious += 1

print(suspicious)
print(total)