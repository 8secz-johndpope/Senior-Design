import pandas as pd 

df = pd.read_csv('red_flags.csv')

df = df.drop(columns=['ico_address','Whitepaper_Address','Original Error','no_tl','_merge_old','To_check','whitepaper_downloaded(Y/N)','_merge','On the original ICO list','No'])
# uppercase first letter of every name for cleaner sorting
df['ICO_Name'] = df['ICO_Name'].str.capitalize()

# sort
df = df.sort_values(by=['ICO_Name'])

# save
df.to_csv('RED_FLAG_LANGUAGE.csv', index=False)
