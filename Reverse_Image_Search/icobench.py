from bs4 import BeautifulSoup as bs
import os
import pandas as pd
import requests
import shutil
import time
from urllib.request import urlopen, Request

os.chdir('/home/troy/Documents/Senior-Design/Reverse_Image_Search')
#driver = webdriver.Firefox(executable_path='/home/troy/Desktop/geckodriver')

base_url = 'https://icobench.com'

df = pd.read_csv('whitepapers_original.csv')

os.chdir('/home/troy/Documents/Senior-Design/Reverse_Image_Search/data')

last_project = ''
with open('last_ico.txt', 'r') as f:
    for line in f:
        last_project = line.strip()


at_current = False
for index, row in df.iterrows():
    project_name = row['ICO_Name'].replace(' ', '_')
    if project_name == last_project or last_project == '':
        at_current = True
    if not at_current:
        continue
    project_url = row['ico_address']
    print(project_name)

    # create a new directory for this team
    if not os.path.isdir(project_name):
        os.mkdir(project_name)
    # cd to new directory
    os.chdir(project_name)

    # the home url of the ico
    req = Request(project_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'})
    try:
        html = urlopen(req).read()
    except:
        os.chdir('..')
        continue
    soup = bs(html, 'lxml')
    target = soup.find('a', {'class':'team'})
    if not target:
        print('no target acquired')
        # project has no team -- save empty dataframe and move on to next
        team_df = pd.DataFrame(columns=cols)
        team_df.to_csv(project_name + '.csv', index=False)
        os.chdir('..')
        continue
    # project has a team
    href = target['href']

    # the team url of the ico
    team_url = base_url + href
    req = Request(team_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'})
    html = urlopen(req).read()
    soup = bs(html, 'lxml')
    base_div = soup.find('div', {'id':'team'})
    members = base_div.find_all('div', {'class':'col_3'})
    '''
    For every member of the team we want to get their name, image and social media links
    '''
    # dataframe to save them to 
    cols = ['Name', 'Image File', 'Social Media File']
    team_df = pd.DataFrame(columns=cols)
    for member in members:
        # intialize variables
        image_save_name = ''
        social_save_name = ''
        # name
        name = member.find('h3', {'class': 'notranslate'}).text
        # correcting for strange error
        if 'https://' in name:
            name = 'NO_NAME'
        if '/' in name:
            name = name.replace('/', '-')

        save_name = name.replace(' ', '_')
        # image
        image_target = member.find('div', {'class':'image_background'})
        image_target = str(image_target['style'])
        '''
        image target is of the form background-image:url('/images/icos/team/image.jpg')
        need to clean it and extract just the url
        '''
        image_url = (image_target.replace('background-image:url(\'', '')).replace('\');', '')
        # Also check if url points to an actual image
        check_url = image_url.split('/')[4]
        if check_url != 'no-image.jpg':
            # need to attach image_url to base url for full image url
            full_image_url = base_url + image_url
            # download and save the image
            r = requests.get(full_image_url, stream=True)
            if r.status_code == 200:
                image_save_name = save_name + '_image.jpg'
                with open(image_save_name, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        else:
            image_save_name = 'N\A'
        # social media
        social_medias = {} # store them in a dictionary ['Social media name'] = 'url'
        social_div = member.find('div', {'class':'socials'})
        if social_div:
            socials = social_div.find_all('a')
            for social in socials:
                social_media = social.text.strip()
                url = social['href']
                social_medias[social_media] = url

            '''
            creating a seperate file to store social media profiles
            they will take the form: name|url
            '''
            social_save_name = save_name + '_social_media.txt'
            with open(social_save_name, 'w') as f:
                if social_medias:
                    for social_name, url in social_medias.items():
                        f.write(social_name + '|' + url + '\n')
                else:
                    f.write('N/A')
        else:
            social_save_name = 'N/A'

        # add the team member to the team dataframe
        info = [name, image_save_name, social_save_name]
        temp_df = pd.DataFrame([info], columns=cols)
        team_df = team_df.append(temp_df, ignore_index=True)
        # end for loop

    # save the team dataframe
    team_df.to_csv(project_name + '.csv', index=False)
    # move back a directory
    os.chdir('..')
    # record who was the last team
    with open('last_ico.txt', 'w') as f:
        print(os.getcwd())
        print('Finished:', project_name)
        f.write(project_name)

