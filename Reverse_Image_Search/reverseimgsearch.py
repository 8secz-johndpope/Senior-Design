from bs4 import BeautifulSoup as bs
from GyazoObject import GyazoObj
from os import path, chdir, listdir
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import shutil
import time
import urllib
from collections import namedtuple, defaultdict
import logging 
from pprint import pprint
import re
from gensim import corpora, models, similarities

icos = pd.read_csv('whitepapers_original.csv')

Flag = namedtuple("Flag", "type name boolean_val")
#types will be social or image, link will be the link, and boolean is the flag
#??? maintain csv?, real only need team to mainatain team_member objects so that we can 
class Team():
    #init team with team_members, csv
    def __init__(self, csv):
        self.Team_Members = []
        self.Team_csv = csv
        self.aggregate_legitimacy_rating = 0

    
    #iterate through team members and find aggregate legitimacy of team
    def calculate_legitimacy_rating(self):
        num_members = len(self.Team_Members)
        pass


class Team_Member():
    #maintain name, social media link, image file, boolean flag list
    def __init__(self, name, image_file):
        self.name = name
        self.image_file = image_file
        self.social_media_links = [] 
        self.flag_list = []
        self.legitimacy = 0 #value should be bound between [-1,1]

    #determine heuristic to assign legitimacy rating for team member
    def legitimacy_rating(self):
        #determine weights (equal distribution? for )
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
        self.driver = None

    def setup_driver(self):
        #webdriver setup
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options, executable_path=self.geckodrv)

    def kill_driver(self):
        self.driver.quit()

    def get_df(self, d):
        target = self.root_dir + d
        if path.isdir(target):
            chdir(target)
            print(d)
            if path.exists(d + '.csv'):
                df = pd.read_csv(d + '.csv')
                return df
            else:
                temp_df = pd.DataFrame()
 
    def useSelenium(self, path, isCryptoSearch=False, crypto_search = ""):
        #get path
        self.driver.get(path)
        #raw html list to hold page results
        html_list = []
        #psuedo do-while
        if isCryptoSearch:
            #find search prompt
            search_prompt =self.driver.find_element_by_name('q')
            #send keys to write crypto name + string 'cryptocurrency'
            search_prompt.send_keys(crypto_search)
            #use webdriver wait to wait until google search button is clickable (previously it was not viewable) & search by xpath 
            search_input = WebDriverWait(self.driver, 20).until(expected_conditions.element_to_be_clickable((By.XPATH,'//input[@value = "Google Search"]')))
            #click google search buttom
            search_input.click()
            #gather contents of web page (only first one)
            target = self.driver.find_element_by_id('cnt')
            html_list.append(target.get_attribute('innerHTML'))
            return html_list
        else:
            while True:
                #grab raw-html
                target = self.driver.find_element_by_id('cnt')
                html_list.append(target.get_attribute('innerHTML'))
                #psuedo exit condition
                try: 
                    #if there is a next page go to it
                    self.driver.find_element_by_id('pnnext').click()
                except:
                    #otherwise no next page, quit driver & associated windows and return the raw_html list which correspond to the raw html for each results page
                    return html_list

    def trim_html(self, html_list, trim_start, trim_end = None):
        #use beautiful soup, make one giant string which is the joined raw_html
        soup = bs(' '.join(html_list), 'lxml')
        #documents list to store all header text for returned sites
        documents = []
        #iterate over soup and grab header text and append to list, header text is corresponding site info of results pages
        for link_html in soup.find_all('h3'):
            documents.append(re.sub(r'\W+', ' ', link_html.get_text())) # regular expression to remove non-alpha-numeric fluff
        return documents[trim_start:trim_end] #trim documents and return them back

    def make_corpora(self, documents):
        #remove common words/tokenize
        stoplist =  set('for of a the and to in an '.split())
        texts = [[word for word in document.lower().split() if word not in stoplist] for document in documents] #list comprehension that removes fluff (words from stoplist) for each document and compiles into a list
        frequency = defaultdict(int) #set default values for all keys in texts list
        #for each text in text and for each token in each text, assign frequency of word
        for text in texts:
            for token in text:
                frequency[token] +=1
        texts = [[token for token in text if frequency[token]>1] for text in texts] #cull list of tokens with frequency of 1
        return texts

    def reverseImageSearch(self, comparison_document, name, gyazo_url):
        #path for reverse image search
        person_search_path = 'https://images.google.com/searchbyimage?image_url='+gyazo_url
        #selenium grab innerhtml
        person_search_html_list = self.useSelenium(person_search_path)
        person_documents = self.trim_html(person_search_html_list, 3) #not sure if this is going to work yet
        #logging info
        # logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level = logging.INFO)
        #establish corpora for comparison documents and for person_documents
        person_texts = self.make_corpora(person_documents)
        #use bag-of-words document representation, we ask How many times does the word system appear in the document
        dictionary = corpora.Dictionary(person_texts)
        vec_bag_of_words = dictionary.doc2bow(comparison_document[0].lower().split())
        #decide on model to train tfidf, LSA, LDA:
        ''' Actually lets not save this... there are a lot of documents..
        dictionary.save('./tmp/{0}_results_matrix.dict'.format(name))
        '''
        corpus = [dictionary.doc2bow(text) for text in person_texts] # create corpus, assigns unique ID to for each word and counts occurences hence we have sparse vector of tuples (<unique_id>, <num_occurence>)
        #NOTE: Below we have layered on transformations to the corpus
        tfidf= models.TfidfModel(corpus) #initialize a model --> use LDA, for now will stick with tfidf model for objective of learning
        corpus_tfidf = tfidf[corpus]
        lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2)

        #debugging
        #lsi.print_topics(2)

        #Perform another transformation from tfidf -> LSI
        corpus_lsi = lsi[corpus_tfidf]
        query_LSI = lsi[vec_bag_of_words]
        # print(query_LSI)
        #Setup query structure
        query_index = similarities.MatrixSimilarity(corpus_lsi)
        query_similarities = query_index[query_LSI]
        query_similarities = sorted(enumerate(query_similarities), key = lambda item: -item[1])
        print(query_similarities)

    def verifyAll(self):
        dirs = sorted(listdir(self.root_dir), key=lambda x: str.lower(x))
        for d in dirs:
            df = self.get_df(d)
            if df.empty:
                print('RED FLAG')
            else:
                for index, row in df.iterrows():
                    img_file = row['Image File']
                    name = row['Name']
                    if img_file != 'N\A':
                        img_obj = self.gyazo.upload(img_file)
                        url = img_obj.url
                        self.reverseImageSearch(url)
                        break
                    else:
                        print('MIGHT BE RED FLAG')
                break
                chdir('..')

    #Attempt #3134: this is getting annoying...
    def search_crypto_name_in_results(self, crypto_name, social_name, path):
        #Use LinkedIn APIs
        if social_name == 'linkedin':
            return 1.0
        #can scrape
        #TODO: need to add passwords for facebook, instagram
        else:
            try:
                #Method 1
                #create password manager
                pass_mngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                #should definitely secure this with a secret, or just use proxy accounts for now lets leave unsecure 
                pass_mngr.add_password(None, path, 'bobjohnson85487', 'Soccer01!') #yes, this is bad but w/e for right now
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
                #NOTE: moved from outside try
                #nice utility that allows us to search html for relevant data 
                soup = bs(raw_html, 'lxml')
                #is crypto_name in soup?
                if soup.find(string = crypto_name) != None:
                    #ie return legitimate
                    return 1.0
                #ie return illegitimate
                return -1.0
            except:
                #flag team member here
                print('ERROR: Page could not be accessed!')
                return 
           

    #Note: Instead of reverse image searching then verifying social media instead lets just make one pass over the data and perform all checks in one go
    def verify_social_and_image(self):
        #return list of directories generated by icobench.py
        dirs = sorted(listdir(self.root_dir), key=lambda x: str.lower(x))
        #for every directory in the list grab corresponding csv file
        for d in dirs:
            df = self.get_df(d)
            #empty-> no social media (or images) -> throw RED FLAG 
            if df.empty:
                print('RED FLAG') #need to throw red flag (should be considered highly suspicious)
            else:
                #setup Team object
                TeamObj = Team(df)
                #make temp directory to save some relevant data
                # os.mkdir('./tmp')
                #else lets examine csv contents
                for index, row in df.iterrows():
                    social_media_file = row['Social Media File'] #grab social media file
                    image_file = row['Image File'] #grab image file
                    name = row['Name']
                    Team_MemberObj = Team_Member(row['Name'], image_file) #initialize team member object 
                    #no social media file-> throw red flag? (lower in severity then no csv?)
                    if social_media_file == 'N/A':
                        Team_MemberObj.flag_list.append(Flag("social", "N/A", -1.0))
                        break
                    else:
                        social_media_links = []
                        with open(social_media_file, 'r') as s_m_f:
                            for line in s_m_f:
                                social_media_links.append(line[line.find('|')+1:line.rfind('\n')]) #ewwwwwww, nasty one liner
                                break
                        Team_MemberObj.social_media_links = social_media_links #set social media links attr
                        #iterate through social media-links
                        for path in social_media_links:
                            #yeah... ill expand this later it looks pretty ugly
                            social_name = path[path.find('.')+1:path.find('.',13)]
                            Team_MemberObj.flag_list.append(Flag(social_name, "social",  self.search_crypto_name_in_results(d, social_name, path)))
                            break
                    if image_file == 'N\A':
                        Team_MemberObj.flag_list.append(Flag("image", "N/A", -1.0))
                        break
                    else:
                        #host image on gyazo
                        img_obj = self.gyazo.upload(image_file)
                        url = img_obj.url
                        #Look up crypto, and trim the html
                        crypto_search_path = 'https://www.google.com/'
                        crypto_query = d + ' crypto'
                        crypto_search_html_list = self.useSelenium(crypto_search_path, isCryptoSearch=True, crypto_search= crypto_query)
                        comparison_document = self.trim_html(crypto_search_html_list, 0, trim_end=1)
                        Team_MemberObj.flag_list.append(Flag("image", image_file, self.reverseImageSearch(comparison_document, name, url)))
                    TeamObj.Team_Members.append(Team_MemberObj)
                TeamObj.calculate_legitimacy_rating()
                self.team_list.append(TeamObj)
                chdir('..')

    def verifyICO(self, ico_name):
        # verify the legitamacy of an individual ico
        pass
client = Google()
#client.verifyAll()
client.setup_driver()
client.verify_social_and_image()
client.kill_driver()
