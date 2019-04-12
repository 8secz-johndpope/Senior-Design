import pandas as pd
import os

# df = pd.read_csv('SummaryFile.csv')
df = pd.read_excel('SummaryFile.xlsx')

result_dir = '/home/troy/Desktop/CYCLES/results/'

df['Single Layer'] = 'N/A'
df['Double Layer'] = 'N/A'


# two file sources now
def analyze(filename, filetype):
    df = ''
    name_col = ''
    if filetype == 'excel':
        df = pd.read_excel(filename)
        name_col = 'ICO_Name_ib'
    if filetype == 'csv':
        df = pd.read_csv(filename)
        name_col = 'STARTUP NAME'
    
    found = 0
    for index, row in df.iterrows():
        name = row[name_col] 
        target_file = result_dir + name +'/' + 'cycles.txt'
        lines = []
        try:
            with open(target_file, 'r') as f:
                lines = f.readlines()
            found += 1
            
            single = 0
            double = 0
            for line in lines:
                if 'SINGLE LAYER CYCLES: ' in line:
                    single = int(line.replace('SINGLE LAYER CYCLES: ', ''))
                if 'DOUBLE LAYER CYCLES: ' in line:
                    double = int(line.replace('DOUBLE LAYER CYCLES: ', ''))
                    break
            df.at[index, 'Single Layer'] = single 
            df.at[index, 'Double Layer'] = double
        except:
            df.at[index, 'Single Layer'] = 0
            df.at[index, 'Double Layer'] = 0
    print(found)
    return df

sumfile1 = analyze('SummaryFile.csv', 'csv')
sumfile2 = analyze('SummaryFile.xlsx', 'excel')

sumfile1.to_csv('SumFile1.csv', index=False)
sumfile2.to_csv('SumFile2.csv', index=False)

def check_duplicate(name, data):
    for row in data:
        if name in row:
            return True
    return False

def count(filename, filenum, data):
    name_col = ''
    if filenum == 1:
        name_col = 'STARTUP NAME'
    else:
        name_col = 'ICO_Name_ib'

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

data = count('SumFile1.csv', 1, [])
data = count('SumFile2.csv', 2, data)

df = pd.DataFrame(data)
df.to_csv('results.csv', index=False)

df = pd.read_csv('results.csv')

suspicious = 0
for index, row in df.iterrows():
    if row['Double Layer'] > 50 or row['Single Layer'] > 50:
        suspicious += 1
print(suspicious)
    