import re
import csv
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook

base_url = 'https://gitlab.com';
colsed_milestones_url = 'https://gitlab.com/gitlab-org/gitlab-ce/milestones?sort=due_date_desc&state=closed'                                                                 #the dict to store the data crawled temporarily
merged_request = ['id','description','assigner','milestone_id','project_name']     #keywords in dict
_json={}
with open('try.csv', 'w',newline='') as csvfile:
    spamwriter = csv.writer(csvfile,dialect='excel',delimiter=',',
                            quotechar='"',quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(merged_request)
driver = webdriver.PhantomJS(executable_path="C:/phantomjs.exe")  #using Phantomjs browser to interact with selenium web driver
driver.set_page_load_timeout(30)                                    #waiting maximum of 30 seconds to load a web page
driver.get(colsed_milestones_url)                                   #get the closed_milestones web page
cms_html = driver.page_source                                       #the closed milestones page containing all closed_milestones' profiles
cms_soup = BeautifulSoup(cms_html,'lxml')                                   #using lxml parser to parse a  HTML web page
_json['project_name'] = cms_soup.find('a',class_='project-item-select-holder').text
while (1):
    for li in cms_soup.find_all('li',class_='milestone milestone-closed'):           # get all closed_milestones' profiles
        _json['milestone_id'] = li['id']                                #record  milestone id
        print(_json['milestone_id'])
        # driver.find_element_by_xpath("//li[@class='milestone milestone-closed']//a[1]").click()  # first link element in this class
        str ="//li[@id='"+li['id']+"']//a[1]"
        driver.find_element_by_xpath(str).click()
        cm_html = driver.page_source                                            #get the closed_milestone web page and use lxml parser to parse this web page
        cm_soup = BeautifulSoup(cm_html,'lxml')

        if cm_soup.find('span',class_='remaining-days') == None \
                or cm_soup.find('span',class_='remaining-days').text != 'Past due':        #in case the milestone is completed on shedule
            continue;
        driver.find_element(By.LINK_TEXT,"Merge Requests").click()         # click the Merge Request link
        element = WebDriverWait(driver, 30).until(         # click the Merge Request link
            EC.presence_of_element_located((By.XPATH,"//div[@class='col-md-3']"))
             # EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-3"))    #those below parameters are also right
             # EC.presence_of_element_located((By.CLASS_NAME, "div.col-md-3"))
        )

        mq_html = driver.page_source                                                #the web page containig Merge_request panel
        mq_soup = BeautifulSoup(mq_html, 'lxml')                                                                # the row used to store item's data to excel file
        for item in mq_soup.find('ul',id='merge_requests-list-merged').find_all('li'): #retrieve all items in Merged list

            _json['description'] = item.find('a').text                         #the first link in item specifies the  merged_request's description
            pattern = re.compile(r'!(.*)')                                        #using regular expression to truncate the merged_request id
            _json['id'] = re.match(pattern, item.find('a').find_next('a').text).group(1)  #the second link in item specifies the merged_request's id
                                                      
            pattern = re.compile(r'Assigned to (.*)')                                           #using regular expression to truncate the assigner's name

            # _json['assigner'] = item.find_next('a',class_='has-tooltip')['title']
            if item.find_next('a',class_='has-tooltip') == None :               #some merged_requests item don't include any assigner's information
                _json['assigner'] = 'NF'
            else:                                                                    #assigner's name is included in this link's title atttribute
                 _json['assigner'] = re.match(pattern,item.find_next('a',class_='has-tooltip')['title']).group(1)
            # print(merged_request)
            with open('Merged Request from GitLab Community Edition milestones.csv', 'a',encoding='utf-8',newline='') as csvfile:             #
                writer = csv.DictWriter(csvfile, fieldnames=merged_request)
                writer.writerow(_json)
        driver.get(colsed_milestones_url)                                                      # reset the webdriver to colsed_milestones_url
    if cms_soup.find('a', text='Next') == None:
        break;
    else:
        # print(cms_soup.find('a',text='Next')['href'])
        colsed_milestones_url = base_url + cms_soup.find('a',text='Next')['href']
        driver.get(colsed_milestones_url)
        # driver.find_element(By.LINK_TEXT,"Next").click()  # click the Merge Request link
        cms_html = driver.page_source                         # get the new closed_milestone web page and use lxml parser to parse this web page
        cms_soup = BeautifulSoup(cms_html, 'lxml')

# with open('result.txt','w',encoding='utf-8') as outfile:
#      outfile.write(html)