from bs4 import BeautifulSoup as bs
from GyazoObject import GyazoObj
from os import path, chdir, listdir
import pandas as pd
import requests
from selenium import webdriver
import shutil
import time
import urllib
from collections import namedtuple
import logging 
from pprint import pprint
import re
from gensim import corpora, models, similarities
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import time
from lxml.html import fromstring
from itertools import cycle

icos = pd.read_csv('whitepapers_original.csv')

Flag = namedtuple("Flag", "type name legit_val")
#types will be social or image, link will be the link, and boolean is the flag
#??? maintain csv?, real only need team to mainatain team_member objects so that we can 
class Team():
    #init team with team_members, csv
    def __init__(self, csv):
        self.Team_Members = []
        self.Team_csv = csv
        self.aggregate_legitimacy_rating = 0

    
    #iterate through team members and find aggregate legitimacy of team
    #Use equal distribution of weights
    def calculate_legitimacy_rating(self):
        num_members = len(self.Team_Members)
        running_val = 0
        for member in self.Team_Members:
            running_val += member.legitimacy
        self.aggregate_legitimacy_rating = running_val/num_members


class Team_Member():
    #maintain name, social media link, image file, boolean flag list
    def __init__(self, name, image_file):
        self.name = name
        self.image_file = image_file
        self.social_media_links = [] 
        self.flag_list = []
        self.legitimacy = 0 #value should be bound between [-1,1]

    #Heuristic: weight social media by 0.4, image flags by 0.6
    #NOTE: the above heuristic was chosen purely by intuition and for the sake of simplicity
    def calculate_legitimacy_rating(self):
        #these can be manipulated as necessary
        social_media_weight = 0.4
        linkedin_weight = 1
        other_social_weight = 1
        image_file_weight = 0.6
        #decompose rating into social and image ratings
        social_rating = 0
        lnkedin_social_rating = 0
        other_social_rating = 0
        no_social = 0
        image_rating = 0
        # useful counts
        social_cnt = 0
        other_social_cnt = 0
        # one useful boolean
        no_social_bool = False

        # The essential idea for the below code is to identify the different social media flags and apply weights (which I've intuitively chosen). The weights that have been chosen
        # are 0.7 for linkedin and 0.3 for other social media (these weight both shift to 1 if the on or other does not exist e.g. only linkedin social media is provided
        # so we assign weight of 1 since we don't penalize for NOT providing some social media over others). Then we assign a global weight to the decomposed rating for social media
        # and image which are 0.4 and 0.6 respectively 
        for flag in self.flag_list:
            # debbbugging
            # print(f'Type: {flag.type}, Name: {flag.name} Value: {flag.legit_val}')
            if flag.type == 'social':
                if flag.name == 'linkedin':
                    lnkedin_social_rating = flag.legit_val
                elif flag.name == 'N/A':
                    no_social = flag.legit_val
                    no_social_bool = True
                else:
                    other_social_rating += flag.legit_val
                    other_social_cnt += 1
                social_cnt += 1
            else:
                image_rating = flag.legit_val
        if lnkedin_social_rating != 0 and other_social_rating != 0:
            lnkedin_social_weight = 0.7
            other_social_weight = 0.3
        social_rating = no_social if no_social_bool else linkedin_weight * lnkedin_social_rating + other_social_weight * (other_social_rating/other_social_cnt)
        self.legitimacy = social_media_weight * (social_rating/social_cnt) + image_file_weight * image_rating
        print(f'Legitimacy value: {self.legitimacy}')


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
        self.chromedrv = '/Users/noahquinones/Desktop/Senior_Project/Senior-Design/Reverse_Image_Search/chromedriver'
        self.team_list = []
        self.driver = None
        self.proxies = None

    def setup_driver(self):
        # try except clause here because Google doesn't like botting queries and I don't want a whole bunch of unterminated drivers hogging my bandwidth
        try:
            proxy = None
            for proxy in self.proxies:
                try: 
                    # webdriver setup- add proxy to arguments
                    options = webdriver.FirefoxOptions() #for some reason this breaks if I use chrome's options, somehow google is detecting botting when using chromeoptions
                    # options.set_headless()
                    options.add_argument(f'--proxy-server={proxy}')
                    self.driver = webdriver.Chrome(options=options, executable_path=self.chromedrv)
                    # print(f'Using proxy {proxy}')
                    break
                # proxy could not connect, go to the next one in the cycle
                except:
                    # print(f'There was an error connecting with this proxy {proxy}')
                    self.driver.quit()
                    next(self.proxies)
                    continue 
        except:
            raise
       

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
    # Credit to: scrape hero
    # Note: This may need to be updated in the future if the site changes how they organize their proxies
    # Designed to get free list of proxies from the below url by parsing the html text and looking for proxies that support https (this is why we search xpath of td[7] for yes),
    # made into a set so that our list contains unique IPs
    def get_proxies(self):
        res = requests.get('https://www.us-proxy.org/')
        parser = fromstring(res.text)
        proxies = set()
        for i in parser.xpath('//tbody/tr'):
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                #Grabbing IP and corresponding PORT
                proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxies.add(proxy)
        self.proxies = cycle(proxies)
   
    # Designed to use google to search for path, if that query is a crypto query then we need to send keys to search bar to perform search
    def useSelenium(self, path, isCryptoSearch=False, crypto_search = ""):
        # get path using previously setup driver 
        self.setup_driver()
        self.driver.get(path)
        # raw html list to hold page results
        html_list = []
        # psuedo do-while
        if isCryptoSearch:
            #find search prompt
            search_prompt = self.driver.find_element_by_name('q')
            #send keys to write crypto name + string 'cryptocurrency'
            search_prompt.send_keys(crypto_search)
            #use webdriver wait to wait until google search button is clickable (previously it was not viewable) & search by xpath 
            '''
            search_input = WebDriverWait(self.driver, 20).until(expected_conditions.element_to_be_clickable((By.XPATH,'//input[@value = "Google Search"]')))
            #click google search buttom
            search_input.click()
            '''
            search_prompt.submit()
            #gather contents of web page (only first one)
            target = self.driver.find_element_by_id('cnt')
            html_list.append(target.get_attribute('innerHTML'))
            # kill driver first
            self.driver.quit()
            # return scrape
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
                    #kill the driver first
                    self.driver.quit()
                    #otherwise no next page, quit driver & associated windows and return the raw_html list which correspond to the raw html for each results page
                    return html_list

    def trim_html(self, html_list, trim_start, trim_end = None):
        #use beautiful soup, make one giant string which is the joined raw_html
        soup = bs(' '.join(html_list), 'lxml')
        #documents list to store all header text for returned sites
        documents = []
        #iterate over soup and grab header text and append to list, header text is corresponding site info of results pages
        for link_html in soup.find_all('h3'):
            documents.append(re.sub(r'[^A-Za-z0-9]+', ' ', link_html.get_text())) # regular expression to remove non-alpha-numeric/non-english fluff
        # picking up some undesirable contents in documents from soup parse, so lets cull these too
        remove_list = ['visually similiar image', 'Description' ,' '] 
        documents = [word for word in documents if word not in remove_list]
        return documents[trim_start:trim_end] #trim documents and return them back

    #generate corpora by removing stoplist word and reducing inflection (ie reduce words of modified form to root form e.g. playing, played, plays -> play)
    #NOTE:Can introduce other scheme if something more suitable is found
    def make_corpora(self, documents):
        #remove common words/tokenize
        stoplist =  set(stopwords.words('english')) #use nltk to establish a stopword list
        stemmer = PorterStemmer() #nltk stemmer that reduces inflection
        texts = [[word for word in document.lower().split() if word not in stoplist] for document in documents] #list comprehension that removes fluff (words from stoplist) for each document and compiles into a list
        cleaned_texts = [[stemmer.stem(word) for word in text] for text in texts] #clean the texts
        return cleaned_texts

    def reverseImageSearch(self, comparison_document, name, gyazo_url):
        # path for reverse image search
        person_search_path = 'https://images.google.com/searchbyimage?image_url='+gyazo_url
        # selenium grab innerhtml
        person_search_html_list = self.useSelenium(person_search_path)
        person_documents = self.trim_html(person_search_html_list, 3) 
        if len(person_documents) == 0: return -1.0 #no search results besides suggested

        #logging info
        #logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level = logging.INFO)

        # establish corpora for comparison documents and for person_documents
        person_texts = self.make_corpora(person_documents)
        # use bag-of-words document representation, we ask How many times does the word system appear in the document
        dictionary = corpora.Dictionary(person_texts)
        vec_comparison_bow = dictionary.doc2bow(comparison_document[0].lower().split()) # vector (bow-esque) that contains the comparsion doc i.e. the document that is the top search result for the associated cryptocurrency
        corpus = [dictionary.doc2bow(text) for text in person_texts] # create corpus, assigns unique ID to for each word and counts occurences hence we have sparse vector of tuples (<unique_id>, <num_occurence>)
        # NOTE: Below we have layered on transformations to the corpus
        tfidf= models.TfidfModel(corpus) #initialize a model 
        corpus_tfidf = tfidf[corpus] #transform corpus to tfidf space
        lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2) if len(corpus)==1 else models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2) #tfidf transformation not appropriate for 1-document corpus
        # Perform another transformation from tfidf -> LSI
        corpus_lsi = lsi[corpus] if len(corpus)==1 else lsi[corpus_tfidf] #same as previous comment
        query_LSI = lsi[vec_comparison_bow] # transform query bow to query LSI
        # Setup query structure 
        query_index = similarities.MatrixSimilarity(corpus_lsi)
        # query the structure to observe similarity of cryptocurrency top search results against person documents that are in LSI space 
        query_similarities = query_index[query_LSI]
        query_similarities = sorted(enumerate(query_similarities), key = lambda item: -item[1])
        # Now we have an iterable similarities array that has give us an answer to the question "How similiar is this query document to each document in the query structure"
        # Assign equal weight to each value in array, find mean
        sim_total = 0
        for _id, value in query_similarities:
            sim_total += value
        return sim_total/len(query_similarities)

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
    # keyword params here are purely for testing, take them out when fully functional
    def search_crypto_name_in_results(self, crypto_name, social_name, path):
        #Use LinkedIn APIs
        if social_name.lower() == 'linkedin':
            return 1.0
        #can scrape
        #TODO: need to add passwords for facebook, instagram
        else:
            try:
                #NOTE: Don't need to do setup accounts for accessing any of these social media, will leave here in case it becomes necessary in the future
                #create password manager
                pass_mngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                #should definitely secure this with a secret, or just use proxy accounts for now lets leave unsecure 
                pass_mngr.add_password(None, path, 'username', 'password') #yes, this is bad but w/e for right now
                #create handler to deal with sites that send back 401
                auth_handler = urllib.request.HTTPBasicAuthHandler(pass_mngr)
                for proxy in self.proxies:
                    try:
                        #create proxy handler
                        proxy_handler = urllib.request.ProxyHandler({'https': proxy})
                        #OpenerDirector instance
                        opener = urllib.request.build_opener()
                        #Use opener for URL fetch
                        opener.open(path)
                        #install opener to tie urlopen to opener
                        urllib.request.install_opener(opener)
                        #create request, allow browser to identify itself through user-agent header 
                        req = urllib.request.Request(path, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'})
                        #make urlopen call on reques object and read raw html
                        raw_html = urllib.request.urlopen(req).read()
                        break
                    except:
                        next(self.proxies)
                        continue
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
                return -1.0
           

    #Note: Instead of reverse image searching then verifying social media instead lets just make one pass over the data and perform all checks in one go
    def verify_social_and_image(self):
        #return list of directories generated by icobench.py
        dirs = sorted(listdir(self.root_dir), key=lambda x: str.lower(x))
        #for every directory in the list grab corresponding csv file
        for d in dirs:
            d = 'TulipToken'
            df = self.get_df(d)
            #empty-> no social media (or images) -> illegitimate
            if df.empty:
                TeamObj = Team(df)
                TeamObj.aggregate_legitimacy_rating = -1.0
            else:
                #setup Team object
                TeamObj = Team(df)
                #make temp directory to save some relevant data
                #Look up crypto, and trim the html
                crypto_search_path = 'https://www.google.com/'
                crypto_query = d + ' crypto'
                crypto_search_html_list = self.useSelenium(crypto_search_path, isCryptoSearch=True, crypto_search= crypto_query)
                comparison_document = self.trim_html(crypto_search_html_list, 0, trim_end=1)
                #else lets examine csv contents
                for index, row in df.iterrows():
                    social_media_file = str(row['Social Media File']) #grab social media file
                    image_file = row['Image File'] #grab image file
                    name = row['Name']
                    Team_MemberObj = Team_Member(row['Name'], image_file) #initialize team member object 
                    if social_media_file == 'nan':
                        Team_MemberObj.flag_list.append(Flag("social", "N/A", -1.0))
                    else:
                        social_media_links = []
                        social_name = ""
                        # print(social_media_file)
                        with open(social_media_file, 'r') as s_m_f:
                            for line in s_m_f:
                                social_name = line[:line.find('|')]
                                social_media_links.append(line[line.find('|')+1:line.rfind('\n')]) #ewwwwwww, nasty one liner
                                # break
                        Team_MemberObj.social_media_links = social_media_links #set social media links attr
                        #iterate through social media-links
                        for path in social_media_links:
                            #yeah... ill expand this later it looks pretty ugly
                            Team_MemberObj.flag_list.append(Flag("social", social_name, self.search_crypto_name_in_results(d, social_name, path))) 
                            # break
                    if image_file == 'N\A':
                        Team_MemberObj.flag_list.append(Flag("image", "N/A", -1.0))
                    else:
                        #host image on gyazo
                        img_obj = self.gyazo.upload(image_file)
                        url = img_obj.url
                        Team_MemberObj.flag_list.append(Flag("image", image_file, self.reverseImageSearch(comparison_document, name, url)))
                    Team_MemberObj.calculate_legitimacy_rating()
                    TeamObj.Team_Members.append(Team_MemberObj)
                TeamObj.calculate_legitimacy_rating()
                self.team_list.append(TeamObj)
                self.kill_driver()
                chdir('..')
            print(TeamObj.aggregate_legitimacy_rating)
    def write_out_legitimacy_values(self):
        with open('legitimacy_values.csv', 'w', newline ='') as f:
            fwriter = csv.writer(f, delimiter=' ', quotechar='|', quoting = csv.QUOTE_MINIMAL)
            for team in self.team_list:
                fwriter.writerow([team.Team_csv, team.aggregate_legitimacy_rating])

    def verifyICO(self, ico_name):
        # verify the legitamacy of an individual ico
        pass
client = Google()
client.get_proxies() # Note: it may be beneficial to make this call inside of the verify call bc proxies may get stale
client.verify_social_and_image()
client.write_out_legitimacy_values()
# debugging
# client.search_crypto_name_in_results()
