from nltk.tokenize import RegexpTokenizer
import numpy as np
import os
import pandas as pd
import re
from stop_words import get_stop_words




df = pd.read_csv('whitepapers_original.csv')
df['Red Flag Words'] = np.nan

base_dir = os.getcwd()
white_papers_path = base_dir + '/whitepapers/'
os.chdir(white_papers_path)

white_papers = sorted(os.listdir(white_papers_path), key=lambda x: str.lower(x))

tokenizer = RegexpTokenizer(r'\w+')
for white_paper in white_papers:
    if not os.path.isfile(white_papers_path + white_paper):
        continue
    number = int(re.sub(r'[\D]+', '', str(white_paper)))
    document = ''
    with open(white_paper, 'r', errors='replace') as f:
        document += f.read()

    red_flag_words = ['profit', 'profits', 'return', 'returns', 'guaranteed profit', 'expected return', 'net gain', 'investor profit', 'nothing to lose', 'high return', 'funds profit', 'no risk', 'little risk', 'guaranteed profit', 'return on investment']

    red_flag_count = {}
    for red_flag_word in red_flag_words:
        if red_flag_word in document:
            if red_flag_word not in red_flag_count:
                red_flag_count[red_flag_word] = document.count(red_flag_word)

    total_red_flags = sum(red_flag_count.values())
    df.loc[df['no_tl'] == number, ['Red Flag Words']] = total_red_flags

df.to_csv('red_flags.csv', index=False)
