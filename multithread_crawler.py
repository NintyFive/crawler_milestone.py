import re,csv,threading,time
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook

class myThread (threading.Thread):
   def __init__(self,milestones_url,milestone_id,project_name):
      threading.Thread.__init__(self)
      self.name = milestone_id
      self.milestones_url = milestones_url
      self.project_name = project_name
      self.milestone_driver = webdriver.PhantomJS(executable_path="C:/phantomjs.exe")  # using Phantomjs browser to interact with selenium web driver
   def run(self):
       _json = {}
       _json['milestone_id'] =  self.name # record  milestone id

       self.milestone_driver.get(self.milestones_url)  # get the closed_milestones web page
       cm_html = self.milestone_driver.page_source  # get the closed_milestone web page and use lxml parser to parse this web page
       cm_soup = BeautifulSoup(cm_html, 'lxml')

       if cm_soup.find('span', class_='remaining-days') == None \
               or cm_soup.find('span',class_='remaining-days').text != 'Past due':  # in case the milestone is completed on shedule
           return
       self.milestone_driver.find_element(By.LINK_TEXT, "Merge Requests").click()  # click the Merge Request link
       print(_json['milestone_id'], ':start waiting for json')
       element = WebDriverWait(self.milestone_driver, 30).until(  # click the Merge Request link
           EC.presence_of_element_located((By.XPATH, "//div[@class='col-md-3']"))
           # EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-3"))    #those below parameters are also right
           # EC.presence_of_element_located((By.CLASS_NAME, "div.col-md-3"))
       )
       print(_json['milestone_id'], ':waiting over')

       mq_html = self.milestone_driver.page_source  # the web page containig Merge_request panel
       mq_soup = BeautifulSoup(mq_html, 'lxml')  # the row used to store item's data to excel file
       for item in mq_soup.find('ul', id='merge_requests-list-merged').find_all('li'):  # retrieve all items in Merged list
           _json['description'] = item.find( 'a').text  # the first link in item specifies the  merged_request's description
           pattern_id = re.compile(r'!(.*)')
           _json['id'] = re.match(pattern_id,item.find('a').find_next('a').text.strip()).group(1)        #the second link in item specifies the merged_request's id
           pattern = re.compile(r'Assigned to (.*)')  # using regular expression to truncate the assigner's name

           if len(item.find_next('span', class_='assignee-icon').contents) == 1:  # some merged_requests item don't include any assigner's information
                                                                                      #contents = 1 means there is only one '\n' element in the span tag
               _json['assigner'] = 'NF'
           else:                                                     # assigner's name is included in this link's title atttribute
               _json['assigner'] = re.match(pattern, item.find_next('a', class_='has-tooltip')['title']).group(1)
           fileLock.acquire()  # acquire the filelock
           with open('Merged Request from GitLab Community Edition milestones.csv', 'a', encoding='utf-8', newline='') as csvfile:    # newline='' parameter is really important, otherwise, rows is terminated by '\r\r\n'
               writer = csv.DictWriter(csvfile, fieldnames=merged_request)
               writer.writerow(_json)
               fileLock.release()

base_url = 'https://gitlab.com';
colsed_milestones_url = 'https://gitlab.com/gitlab-org/gitlab-ce/milestones?sort=due_date_desc&state=closed'                                                                 #the dict to store the data crawled temporarily
merged_request = ['id','description','assigner','milestone_id','project_name']     #keywords in dict
start_time = time.time()
with open('Merged Request from GitLab Community Edition milestones.csv', 'w',newline='') as csvfile:
    spamwriter = csv.writer(csvfile,dialect='excel',delimiter=',',
                            quotechar='"',quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(merged_request)
driver = webdriver.PhantomJS(executable_path="C:/phantomjs.exe")  #using Phantomjs browser to interact with selenium web driver
driver.set_page_load_timeout(30)                                    #waiting maximum of 30 seconds to load a web page
driver.get(colsed_milestones_url)                                   #get the closed_milestones web page
cms_html = driver.page_source                                       #the closed milestones page containing all closed_milestones' profiles
cms_soup = BeautifulSoup(cms_html,'lxml')                                   #using lxml parser to parse a  HTML web page
threads = []
fileLock = threading.Lock()
project_name = cms_soup.find('a',class_='project-item-select-holder').text
# counter = 1
while (1):
    for li in cms_soup.find_all('li', class_='milestone milestone-closed'):  # get all closed_milestones' profiles

        milestones_url = base_url + cms_soup.find('li',id=li['id']).find('a')['href']  #the first link is
        thread = myThread(milestones_url,li['id'],project_name)                                         # Create new threads
        thread.start()                                                                   # Start new Threads
        threads.append(thread)                                                           # Add threads to thread list
        # counter = counter + 1
    if cms_soup.find('a', text='Next') == None:
        break
    else:
        driver.find_element(By.LINK_TEXT, "Next").click()                   # click the Merge Request link
        # colsed_milestones_url = base_url + cms_soup.find('a', text='Next')['href'] #those two statements service same function as the above one
        # driver.get(colsed_milestones_url)
        print('**************ri********************')
        cms_html = driver.page_source                         # get the new closed_milestone web page and use lxml parser to parse this web page
        cms_soup = BeautifulSoup(cms_html, 'lxml')

# Wait for all threads to complete
for t in threads:
    t.join()
print("Exiting Main Thread")
end_time = time.time()
print("%s: %d seconds" % ('running_time', end_time-start_time))