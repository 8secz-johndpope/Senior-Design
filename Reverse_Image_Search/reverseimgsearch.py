from bs4 import BeautifulSoup as bs
from GyazoObject import GyazoObj
import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import shutil
import time
from urllib.request import urlopen, Request

icos = pd.read_csv('whitepapers_original.csv')

def get_df(root_dir, d):
    target = root_dir + d
    if os.path.isdir(target):
        os.chdir(target)
        print(d)
        if os.path.exists(d + '.csv'):
            df = pd.read_csv(d + '.csv')
            return df
    temp_df = pd.DataFrame()
    return temp_df

def useSelenium(geckodrv_path, url):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options, executable_path=geckodrv_path)
    driver.get(url)
    target = driver.find_element_by_id('cnt')
    html = target.get_attribute('innerHTML')
    driver.quit()
    return html

def uploadToGyazo(gyazo_client, img_file):
    if img_file != 'N\A':
        img_obj = gyazo_client.upload(img_file)
        url = img_obj.url
        return url
    return False

def reverseImageSearch(geckodrv_path, gyazo_url):
    google_path = 'https://images.google.com/searchbyimage?image_url='
    full_path = google_path + gyazo_url
    html = useSelenium(geckodrv_path, full_path)
    soup = bs(html, 'lxml')
    targets = soup.find_all('div', {'class':'g'})

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
        self.gyazo_client = GyazoObj()
        self.root_dir = '/home/troy/Documents/Senior-Design/Reverse_Image_Search/data/'
        self.geckodrv = '/home/troy/Documents/Senior-Design/Reverse_Image_Search/geckodriver'

    def verifyAll(self):
        dirs = sorted(os.listdir(self.root_dir), key=lambda x: str.lower(x))
        for d in dirs:
            # TODO
            # add support for when the directory exists but no csv exists
            df = get_df(d)
            if df.empty:
                print('RED FLAG')
            else:
                for index, row in df.iterrows():
                    name = row['Name']
                    img_file = row['Image File']
                    url = uploadToGyazo(self.gyazo_client, img_file)
                    if url:
                        self.reverseImageSearch(self.geckodrv, url)
                        break
                    else:
                        print(f'NO IMAGE FILE FOR {name}... MIGHT BE RED FLAG')
                break
                os.chdir('..')

    def verifyICO(self, ico_name):
        # verify the legitamacy of an individual ico
        pass

client = Google()
client.verifyAll()

