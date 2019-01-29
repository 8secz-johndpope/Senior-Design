from bs4 import BeautifulSoup as bs
from GyazoObject import GyazoObj
import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import shutil
import time
import urllib
from collections import namedtuple

icos = pd.read_csv('whitepapers_original.csv')

Flag = namedtuple("Flag", "type name boolean")
#types will be social or image, link will be the link, and boolean is the flag
#??? maintain csv?, real only need team to mainatain team_member objects so that we can 
class Team():
    #init team with team_members, csv
    def __init__(self, csv):
        self.Team_Members = []
        self.Team_csv = csv
        self.aggregate_legitimacy_rating = 0

    def set_team_members(self, team_members):
        pass
    
    #iterate through team members and find aggregate legitimacy of team
    def set_aggregate_legitimacy_rating(self):
        pass


class Team_Member():
    #maintain name, social media link, image file, boolean flag list
    def __init__(self, name, image_file):
        self.name = name
        self.image_file = image_file
        self.social_media_links = [] 
        self.flag_list = []
        pass

    #determine heuristic to assign legitimacy rating for team member
    def legitimacy_rating(self):
        pass


#TODO
'''
loop through every ico
if no images throw red flag
if no social media throw red flag
discuss what would constitute a red flag on a reverse image search
'''
class Google():
    def __init__(self):
        self.google_path = 'images.google.com/searchbyimage?image_url='
        self.gyazo = GyazoObj()
        self.root_dir = '/Users/noahquinones/Desktop/Senior_Project/Senior-Design/Reverse_Image_Search/data/'
        self.geckodrv = '/Users/noahquinones/Desktop/Senior_Project/Senior-Design/Reverse_Image_Search/geckodriver'
        self.team_list = []

    def get_df(self, d):
        target = self.root_dir + d
        if os.path.isdir(target):
            os.chdir(target)
            print(d)
            if os.path.exists(d + '.csv'):
                df = pd.read_csv(d + '.csv')
                return df
            else:
                temp_df = pd.DataFrame()

    def useSelenium(self, path):
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options, executable_path=self.geckodrv)
        driver.get(path)
        target = driver.find_element_by_id('cnt')
        html = target.get_attribute('innerHTML')
        driver.quit()
        return html

    def reverseImageSearch(self, gyazo_url):
        google_path = 'https://images.google.com/searchbyimage?image_url='
        full_path = google_path + gyazo_url
        html = self.useSelenium(full_path)
        soup = bs(html, 'lxml')
        targets = soup.find_all('div', {'class':'g'})

    def verifyAll(self):
        dirs = sorted(os.listdir(self.root_dir), key=lambda x: str.lower(x))
        for d in dirs:
            df = self.get_df(d)
            if df.empty:
                print('RED FLAG')
            else:
                for index, row in df.iterrows():
                    img_file = row['Image File']
                    if img_file != 'N\A':
                        img_obj = self.gyazo.upload(img_file)
                        url = img_obj.url
                        self.reverseImageSearch(url)
                        break
                    else:
                        print('MIGHT BE RED FLAG')
                break
                os.chdir('..')

    #Attempt #3134: this is getting annoying...
    def search_crypto_name_in_results(self, crypto_name, social_name, path):
        #Keeping this here for the sake of posterity -> Use LinkedIn APIs
        if social_name == 'linkedin':
            return 
        #can scrape
        else:
            try:
                #Method 1
                #create password manager
                pass_mngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                #should definitely secure this with a secret, or just use proxy accounts for now lets leave unsecure 
                pass_mngr.add_password(None, path, 'bobjohnson854', 'soccer01') #yes, this is bad but w/e for right now
                #create handler to deal with sites that send back 401
                auth_handler = urllib.request.HTTPBasicAuthHandler(pass_mngr)
                #OpenerDirector instance
                opener = urllib.request.build_opener(auth_handler)
                #Use opener for URL fetch
                opener.open(path)
                #install opener to tie urlopen to opener
                urllib.request.install_opener(opener)
                #create request, allow browser to identify itself through user-agent header 
                req = urllib.request.Request(path, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'})
                #make urlopen call on reques object and read raw html
                raw_html = urllib.request.urlopen(req).read()
            except:
                #flag team member here
                print('Page could not be accessed!')
                return 
            soup = bs(raw_html, 'lxml')
            return soup.find(string = crypto_name) != None

    #Note, possibly consider searching LinkedIn names using selenium 
    def verify_social_and_image(self):
        #return list of directories generated by icobench.py
        dirs = sorted(os.listdir(self.root_dir), key=lambda x: str.lower(x))
        #for every directory in the list grab corresponding csv file
        for d in dirs:
            df = self.get_df(d)
            #empty-> no social media (or images) -> throw RED FLAG 
            if df.empty:
                print('RED FLAG') #need to throw red flag (should be considered highly suspicious)
            else:
                #setup Team object
                TeamObj = Team(df)
                #else lets examine csv contents
                for index, row in df.iterrows():
                    social_media_file = row['Social Media File'] #grab social media file
                    image_file = row['Image File']
                    Team_MemberObj = Team_Member(row['Name'], image_file) #initialize team member object 
                    #no social media file-> throw red flag? (lower in severity then no csv)
                    
                    if social_media_file == 'N/A':
                        Team_MemberObj.flag_list.append(Flag("social", "N/A", False))
                        break
                    else:
                        social_media_links = []
                        with open(social_media_file, 'r') as s_m_f:
                            for line in s_m_f:
                                social_media_links.append(line[line.find('|')+1:line.rfind('\n')]) #ewwwwwww, nasty one liner
                                break
                        Team_MemberObj.social_media_links = social_media_links #set social media links attr
                        #iterate through social media-links
                        #TODO: need to create Team (or Person, however this would be heavy) object to maintain flags
                        for path in social_media_links:
                            #yeah... ill expand this later it looks pretty ugly
                            social_name = path[path.find('.')+1:path.find('.',13)]
                            Team_MemberObj.flag_list.append(Flag(social_name,"social", self.search_crypto_name_in_results(d, social_name, path)))
                            break
                    if image_file == 'N\A':
                        Team_MemberObj.flag_list.append(Flag("image", "N/A", False))
                        break
                    else:
                        img_obj = self.gyazo.upload(image_file)
                        url = img_obj.url
                        Team_MemberObj.flag_list.append(Flag("image", image_file, self.reverseImageSearch(url)))
                break
                os.chdir('..')

    def verifyICO(self, ico_name):
        # verify the legitamacy of an individual ico
        pass

client = Google()
#client.verifyAll()
client.verify_social_and_image()
