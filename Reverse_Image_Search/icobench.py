from bs4 import BeautifulSoup as bs
import os
import pandas as pd
import requests
import shutil
import time
from urllib.request import urlopen, Request

# DEFINE EXTERNAL METHODS
def createDirectoryAndChangeToIt(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    # change to new directory
    os.chdir(dir_name)

def projectFailed():
    team_df = pd.DataFrame(columns=cols)
    team_df.to_csv(project_name + '.csv', index=False)
    os.chdir('..')

def getLastProject():
    file_name = 'last_ico.txt'
    last_project = ''
    try:
        with open(file_name, 'r') as f:
            for line in f:
                last_project = line.strip()
    except:
        # file doesn't exist yet
        pass
    return last_project

def atCurrentProject(project_name, last_project):
    if project_name == last_project or last_project == '':
        return True
    return False

def getPageContents(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'})
    try:
        html = urlopen(req).read()
        soup = bs(html, 'lxml')
        return soup
    except:
        # icobench does not have a page for this project
        team_df = pd.DataFrame(columns=cols)
        team_df.to_csv(project_name + '.csv', index=False)
        os.chdir('..')
        return False

def getImage(member, save_name, base_url):
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
            image_save_name = 'N/A'
    else:
        image_save_name = 'N/A'
    return image_save_name

def getSocialMedia(member, save_name):
    social_medias = {} # store them in a dictionary ['Social media name'] = 'url'
    social_div = member.find('div', {'class':'socials'})
    if social_div:
        socials = social_div.find_all('a')
        for social in socials:
            social_media = social.text.strip()
            url = social['href']
            social_medias[social_media] = url

        '''
        Creating a seperate file to store social media profiles.
        They will take the form: name|url
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
    return social_save_name


class Icobench:
    def __init__(self):
        self.base_url = 'https://icobench.com'

    def getAllIcos(self):
        # retrieve all ICOs from the CSV file Professor Li provided
        os.chdir('/home/troy/Documents/Senior-Design/Reverse_Image_Search')
        df = pd.read_csv('whitepapers_original.csv')

        # create a new directory for the data 
        path_to_data = '/home/troy/Documents/Senior-Design/Reverse_Image_Search/data'
        createDirectoryAndChangeToIt(path_to_data)

        ''' if script fails or needs to be restarted last_ico.txt will be 
         a reference point to not waste time rescraping already scraped projects '''
        last_project = getLastProject()

        for index, row in df.iterrows():
            project_name = row['ICO_Name'].replace(' ', '_')
            if not atCurrentProject(project_name, last_project):
                continue
            # script will continue at the ICO before the last failed ICO
            project_url = row['ico_address']
            print(f'Currently gathering data for: {project_name}') # project currently being scraped

            # create a new directory within 'data' for this project
            createDirectoryAndChangeToIt(project_name)

            # request home url of the ico
            soup = getPageContents(project_url)
            if not soup:
                # page doesn't exist
                projectFailed()
                continue

            # look for team tab
            target = soup.find('a', {'class':'team'})
            if not target:
                # project has no team -- save empty dataframe and move on to next
                projectFailed()
                continue

            # webpage has a team tab
            href = target['href']

            # request team url of the ico
            team_url = self.base_url + href
            soup = getPageContents(team_url)
            if not soup:
                # page doesn't exist
                projectFailed()
                continue

            # find all team members
            base_div = soup.find('div', {'id':'team'})
            members = base_div.find_all('div', {'class':'col_3'})
            if not members:
                # project has team tab but no team members
                projectFailed()
                continue
            '''
            For every member of the team we want to get their name, image and social media links
            '''
            # create dataframe to save them to 
            cols = ['Name', 'Image File', 'Social Media File']
            team_df = pd.DataFrame(columns=cols)
            for member in members:
                # find the name of this member
                name = member.find('h3', {'class': 'notranslate'}).text

                # correcting for errors in the name
                if 'https://' in name:
                    name = 'NO_NAME'
                if '/' in name:
                    name = name.replace('/', '-')

                save_name = name.replace(' ', '_') # replace spaces with underscores

                # IMAGE
                image_save_name = getImage(member, save_name, self.base_url)
                # SOCIAL MEDIA
                social_save_name = getSocialMedia(member, save_name)

                # update dataframe
                info = [name, image_save_name, social_save_name]
                temp_df = pd.DataFrame([info], columns=cols)
                team_df = team_df.append(temp_df, ignore_index=True)
                # end for loop

            # save the team dataframe
            team_df.to_csv(project_name + '.csv', index=False)
            # move back to 'data' directory
            os.chdir('..')
            # record the last team completed
            with open('last_ico.txt', 'w') as f:
                f.write(project_name)

    ''' This method allows for the data on an individual ICO project to be downloaded '''
    def getIco(self, name, icobench_url):
        os.chdir('/home/troy/Documents/Senior-Design/Reverse_Image_Search')

        # create a new directory for the data 
        path_to_data = '/home/troy/Documents/Senior-Design/Reverse_Image_Search/data'
        createDirectoryAndChangeToIt(path_to_data)

        project_name = name
        project_url = icobench_url
        print(f'Currently gathering data for: {project_name}') # project currently being scraped

        # create a new directory within 'data' for this project
        createDirectoryAndChangeToIt(project_name)

        # request home url of the ico
        soup = getPageContents(project_url)
        if not soup:
            # page doesn't exist
            projectFailed()

        # look for team tab
        target = soup.find('a', {'class':'team'})
        if not target:
            # project has no team -- save empty dataframe and move on to next
            projectFailed()

        # webpage has a team tab
        href = target['href']

        # request team url of the ico
        team_url = self.base_url + href
        soup = getPageContents(team_url)
        if not soup:
            # page doesn't exist
            projectFailed()

        # find all team members
        base_div = soup.find('div', {'id':'team'})
        members = base_div.find_all('div', {'class':'col_3'})
        if not members:
            # project has team tab but no team members
            projectFailed()
        '''
        For every member of the team we want to get their name, image and social media links
        '''
        # create dataframe to save them to 
        cols = ['Name', 'Image File', 'Social Media File']
        team_df = pd.DataFrame(columns=cols)
        for member in members:
            # find the name of this member
            name = member.find('h3', {'class': 'notranslate'}).text

            # correcting for errors in the name
            if 'https://' in name:
                name = 'NO_NAME'
            if '/' in name:
                name = name.replace('/', '-')

            save_name = name.replace(' ', '_') # replace spaces with underscores

            # IMAGE
            image_save_name = getImage(member, save_name, self.base_url)
            # SOCIAL MEDIA
            social_save_name = getSocialMedia(member, save_name)

            # update dataframe
            info = [name, image_save_name, social_save_name]
            temp_df = pd.DataFrame([info], columns=cols)
            team_df = team_df.append(temp_df, ignore_index=True)

        # save the team dataframe
        team_df.to_csv(project_name + '.csv', index=False)
        # move back to 'data' directory
        os.chdir('..')

