import pandas as pd 
import numpy as np

df = pd.read_csv('intermediate_results/SumFile1.csv')
df = df.sort_values(by=['STARTUP NAME'])
df = df.drop(columns=['DH_Number', 'nl_TL', 'START', 'END', 'Success', 'EtherscanAddress', 'ContractAddress', 'ListofWrongBuyers', 'TokenDistributionBeforeICOend', 'Explanation', 'ICObench_STARTUPNAME', 'CentralizedDistributor?' ])
df.to_csv('intermediate_results/SumFile3.csv', index=False)

df = pd.read_csv('intermediate_results/SumFile2.csv')
df = df.sort_values(by=['ICO_Name_ib'])
df = df.drop(columns=['Etherscan Address','ICO_Name_rt','ico_address','no_tl','Success (Y/N)','Platform_ib','Type_ib','ICO start_ib','ICO end_ib','ICO_start_rt','ICO_end_rt'])
# add distributor address 2
zeros = [np.nan for i in range(df.shape[0])]
df.insert(loc=3, column='DistributorAddress2', value=zeros)
# rename first column
df = df.rename(index=str, columns={'ICO_Name_ib': 'STARTUP NAME', 'Status(donghwa)':'Status'})
df.to_csv('intermediate_results/SumFile4.csv', index=False)

df1 = pd.read_csv('intermediate_results/SumFile3.csv')
df2 = pd.read_csv('intermediate_results/SumFile4.csv')
df = pd.concat([df1, df2])
# drop duplicates
df = df.drop_duplicates(subset=['STARTUP NAME'])
# uppercase first letter of ico_name for cleaner sorting
df['STARTUP NAME'] = df['STARTUP NAME'].str.capitalize()
# final sort
df = df.sort_values(by=['STARTUP NAME'])
df.to_csv('BLOCKCHAIN_RESULTS.csv', index=False)