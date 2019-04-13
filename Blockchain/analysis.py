import pandas as pd
import os

def check_duplicate(name, data):
    for row in data:
        if name in row:
            return True
    return False

def count(filename):
    data = []
    name_col = 'STARTUP NAME'
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        temp = {}
        if row['Single Layer'] > 1 or row['Double Layer'] > 1:
            temp['Name'] = row[name_col]
            temp['Single Layer'] = row['Single Layer']
            temp['Double Layer'] = row['Double Layer']
            if not check_duplicate(row[name_col], data):
                print(row[name_col])
                data.append(temp)
    return data


df = pd.DataFrame(count('BLOCKCHAIN_RESULTS.csv'))
df.to_csv('PROJECTS_WITH_CYCLES.csv', index=False)

df = pd.read_csv('BLOCKCHAIN_RESULTS.csv')

suspicious = 0
total = 0
for index, row in df.iterrows():
    if row['Status'] == 'OK' and row['DistributorAddress'] and row['DistributorAddress'] != '0x0000000000000000000000000000000000000000':
        total += 1
    if row['Double Layer'] > 100 or row['Single Layer'] > 100:
        suspicious += 1
print(suspicious)
print(total)