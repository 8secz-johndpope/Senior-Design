import time 
from selenium import webdriver
import selenium.webdriver.chrome.service as service

service = service.Service('/Users/noahquinones/Desktop/Senior_Project/Senior-Design/Reverse_Image_Search/chromedriver')
service.start()
capabilities = {'chrome.binary': '/Users/noahquinones/Applications/Google\ Chrome'}
driver = webdriver.