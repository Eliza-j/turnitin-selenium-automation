import os
from time import sleep
import datetime
import fileManager
import generateDriver
from repo import getCurrentTimestamp
from random import randint
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select

# username1 = "tik@unsrat.ac.id"
# password1 = "unsrat@TIK2022"
# currDir = "/data/turnitin/"
currDir = os.getcwd() + '/'

class element_has_certain_content(object):
  def __init__(self, locator):
    self.locator = locator
  
  def __call__(self, driver):
    element = driver.find_element(*self.locator)   # Finding the referenced element
    if element.text != '':
      return element.text
    else:
      return False


def randSleep():
  sleep(randint(1,3))




class TurnitinPageDriver():
  def __init__(self, driver):
    self.driver = driver

  def setWebDriverWait(self, timeout):
    self.wait = WebDriverWait(self.driver, timeout)
  
  def login(self, credential):
    username = self.driver.find_element(By.NAME, "email")
    password = self.driver.find_element(By.NAME, "user_password")
    username.clear()
    username.send_keys(credential[0])
    password.clear()
    password.send_keys(credential[1])
    randSleep()
    self.driver.find_element(By.NAME, "submit").click()
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Selesai melakukan login")

  def checkAssignmentExist(self, assignmentTitle):
    try:
      self.openViewAssignment(assignmentTitle)
      print("found")
      return True
    except Exception as e:
      if type(e).__name__ == 'NoSuchElementException':
        return False

  def addAssignment(self, assignmentName, repositoryOption, excludeBiblioOption, excludeQuotedOption, excludeSmallSources, excludeSmallSourcesType, excludeSmallValue, templatePath):
    if self.checkAssignmentExist(assignmentName):
      print("Assignment already exists")
      return
    
    if repositoryOption is None:
      repositoryOption = 0
    
    if excludeBiblioOption == 1 or excludeBiblioOption is None:
      biblioElement = "use_biblio_exclusion_1"
    else:
      biblioElement = "use_biblio_exclusion_0"

    if excludeQuotedOption == 1 or excludeQuotedOption is None:
      quotedElement = "use_quoted_exclusion_1"
    else:
      quotedElement = "use_quoted_exclusion_0"

    if excludeSmallSources == 1 or excludeSmallSources is None:
      smallSourcesElement = "use_small_matches_1"
      # 0: exclude by word counts
      if excludeSmallSourcesType == 0:
        smallSourcesInputElement = "exclude_by_words_value"
      #1: exclude by percentage
      elif excludeSmallSourcesType == 1:
        smallSourcesInputElement= "exclude_by_percent_value"
    else:
      smallSourcesElement = "use_small_matches_0"
    
    repositoryLocation = {
      0 : "standard paper repository",
      1: "no repository"
    }
    
    self.driver.find_element(By.ID, "new_assignment_link").click()
    self.driver.find_element(By.NAME, "submit").click()
    titleBox = self.driver.find_element(By.NAME, "title")
    titleBox.clear()
    titleBox.send_keys(assignmentName)
    
    # repository option
    repoBox = Select(self.driver.find_element(By.NAME, 'submit_papers_to'))
    repoBox.select_by_visible_text(repositoryLocation[repositoryOption])
    sleep(3)
    
    # optional settings
    self.driver.find_element(By.ID, "on").click()
    
    # exclude bibliography
    self.driver.find_element(By.ID, biblioElement).click()
    
    # exclude quoted
    self.driver.find_element(By.ID, quotedElement).click()
    
    # exclude small sources
    self.driver.find_element(By.ID, smallSourcesElement).click()
    if excludeSmallSources:
      wordCountBox = self.driver.find_element(By.ID, smallSourcesInputElement)
      wordCountBox.click()
      wordCountBox.clear()
      wordCountBox.send_keys(excludeSmallValue)
    
    # include custom format template
    if templatePath is not None:
      userfile = self.driver.find_element(By.NAME, "userfile")
      userfile.send_keys(templatePath)

    # allow students see similarity reports
    self.driver.find_element(By.ID, "students_view_reports_1").click()
    
    # submit
    sleep(3)
    self.driver.find_element(By.ID, "submit").click()
    sleep(15)
    
  def openHomePage(self, className):
    classBtn = self.driver.find_element(By.LINK_TEXT, className)
    classBtn.click()
  
  def openSubmitPage(self, assignmentName):
    assignmentObj = self.driver.find_element(By.XPATH, '//*[@title="' + assignmentName + '"]')
    assignmentObj.find_element(By.LINK_TEXT, "More actions").click()
    assignmentObj.find_element(By.LINK_TEXT, "Submit").click()

  def openViewAssignment(self, assignmentName):
    assignmentObj = self.driver.find_element(By.XPATH, '//*[@title="' + assignmentName + '"]')
    assignmentObj.find_element(By.LINK_TEXT, "View").click()
     
  def backToHomepage(self, className):
     self.driver.find_element(By.LINK_TEXT, className.upper()).click()
     
  def openAllPaper(self):
    self.driver.find_element(By.ID, "now_viewing").click()
    self.driver.find_element(By.LINK_TEXT, "All papers").click()
     
  def check_exists_by_xpath(self, xpath):
    try:
       self.driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
       return False
    return True

  def checkLessWordsError(self):
    message_error_xpath = "//*[text()='You must submit more than 20 words of text.']"
    return self.check_exists_by_xpath(message_error_xpath)

  def checkUnreadableDocsError(self):
    message_error_xpath = """//*[text()="We're sorry, but we could not read the PDF you submitted. Please make sure that the file is not password protected and contains selectable text rather than scanned images."]"""
    return self.check_exists_by_xpath(message_error_xpath)

  def checkUnusualDocsError(self):
    message_error_xpath = """//*[text()="The paper you have submitted seems to have an unusual number of excessively long or short words. Please try changing your font and submitting again or contact our help desk if the problem persists."]"""
    return self.check_exists_by_xpath(message_error_xpath)
  
  def uploadDoc(self, job):
    authorfirst = self.driver.find_element(By.NAME, "author_first")
    authorlast = self.driver.find_element(By.NAME, "author_last")
    submissiontitle = self.driver.find_element(By.NAME, "title")
    authorfirst.clear()
    authorlast.clear()
    submissiontitle.clear()

    if len(job.firstName) <= 0:
       job.firstName = "Mr/Mrs" 
    
    authorfirst.send_keys(job.firstName)
    
    if len(job.lastName) <= 0:
      job.lastName = "et al"
    authorlast.send_keys(job.lastName)

    #if len(job.title) > 195:
    #  job.title = job.title[0:195]
    
    job.title  = fileManager.checkTitle(job.title)
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: melakukan upload untuk " + str(job.id) + '_' + job.title)
    submissiontitle.send_keys(str(job.id) + '_' + job.title)
    randSleep()
    
    userfile = self.driver.find_element(By.NAME, "userfile")
    userfile.send_keys(job.submittedFilePath)
    
    wait = WebDriverWait(self.driver,60)
    try:
       submitbutton = wait.until(EC.element_to_be_clickable((By.NAME, "submit_button")))
    except:
       raise
    submitbutton.click()
    
    confirm = wait.until(EC.element_to_be_clickable((By.ID, 'confirm-btn')))
    confirm.click()
    
    paperID = wait.until(element_has_certain_content((By.ID, "submission-metadata-oid")))
    job.paperID = paperID

  def getCurrentURL(self):
    return self.driver.current_url

  def getPage(self, linkPage):
    self.driver.get(linkPage)

  #Get assignment page's page list. Eg: page 1, 2, 3, 4, ...
  def getPages(self):
    try:
       pageBox = self.driver.find_element(By.CLASS_NAME, "ibox_pagination")
       pages = (pageBox.find_elements(By.TAG_NAME, "li"))
       page = pages[1].find_elements(By.TAG_NAME, "a")
       self.pageList = [a.text for a in page]
       self.pageList.pop(0)

    except Exception as e:
      if type(e).__name__ == 'NoSuchElementException':
         return []
      else:
         raise
  
  #Go to assignement page's next page from current location
  def nextPage(self):
    """
     - terima pageList
     - kase pindah ke halaman berikut
     - kase bale pageList yang dpe halaman sebelumnya so dpa se kurang satu
    """
    link = self.driver.current_url

    if link[-1] == '=' :
       link += self.pageList[0]
    elif link[1] == '1':
       link = link[:-1] + self.pageList[0]
    else:
       link = link[:-1] + self.pageList[0]
    
    self.pageList.pop(0)
    self.getPage(link)
  
  def backToFirstPage(self):
    link = self.driver.current_url
    if link[-1] == '=':
       link += '1'
    else:
       link = link[:-1] + '1'
    self.getPage(link)

  def refreshPage(self):
    self.driver.refresh()

  #Get a document's paper id element from assignment page given a paper id  ????
  def elementIfPidExist(self, pid):
    try:
      pidRow = self.driver.find_element(By.XPATH, "//*[text()='" + pid + "']")
      return pidRow
    except Exception as e:
      if type(e).__name__ == 'NoSuchElementException':
         raise
      else:
         raise
      
  #Get a document's ROW element from assignment page given a paper id
  def getReportRowElement(self, pid):
    pidElement = self.driver.find_element(By.XPATH, "//*[text()='" + pid + "']")
    self.reportRow = pidElement.find_element(By.XPATH, "./..")
  
  def getReportScore(self):
    checkFinished = self.reportRow.find_element(By.CLASS_NAME, "or_full_version")
    # print(checkFinished.text)
    if checkFinished.text == "--":
      return checkFinished.text
    
    return self.reportRow.find_element(By.CLASS_NAME, "or-percentage").text
  

  #??????
  def getDocScore(docElement):
    scoreText = docElement.find_element(By.CLASS_NAME, "or-percentage").text
    scoreTextWithoutPercentage = scoreText.rstrip(scoreText[-1])

    try:
      return int(scoreTextWithoutPercentage)
    except:
      print("invalid score")
  
  def getOriginalAssignmentWindow(self):
    self.assignment_window = self.driver.current_window_handle
  
  def assertWindowHandleCount(self):
    assert len(self.driver.window_handles) == 1

  def sortAssignmentByDate(self):
    self.driver.find_element(By.XPATH, "//*[@id='assign_inbox']/div[2]/table/tbody/tr[1]/th[10]/a").click()

  
  def switchToDownloadWindow(self):
    self.reportRow.find_element(By.CLASS_NAME, "or-link").click()
    self.wait.until(EC.number_of_windows_to_be(2))
    for window_handle in self.driver.window_handles:
      if window_handle != self.assignment_window:
         self.driver.switch_to.window(window_handle)
         break
    self.wait.until(EC.title_is("Feedback Studio"))

  def backToDownloadWindow(self):
    self.driver.switch_to.window(self.assignment_window)

  def downloadReport(self):
    wait2 = WebDriverWait(self.driver, 60)
    wait = WebDriverWait(self.driver, 300)
    self.driver.fullscreen_window()
    sleep(5)
    
    # If the download button is hidden
    # wait2.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[title=\"Download and information tools\"]")))
    # self.driver.find_element(By.CSS_SELECTOR, "[title=\"Download and information tools\"]").click()
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Mengeklik Download and information tools")

    
    sleep(3)
    self.driver.find_element(By.CSS_SELECTOR, "[title=\"Download\"]").click()
    #driver.find_element(By.XPATH, "//div[@title='Download']").click()
    self.driver.find_element(By.CSS_SELECTOR, "[aria-label=\"Current View\"]").click()
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Telah mengeklik tombol download. Menunggu....")
    # time.sleep(30)
    preparingDownloadElement = self.driver.find_element(By.XPATH, "//*[text()='Preparing download...']")
    wait.until(EC.staleness_of(preparingDownloadElement))
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Pengunduhan dimulai")
    self.driver.close();
    
  def closeTurnitin(self):
    self.driver.quit()





# def startDriver():
#     driver = webdriver.Chrome(chrome_options=options)
#     driver.get("https://www.turnitin.com/login_page.asp?lang=en_us")

#     return driver


#Method to get the downloaded file name (Not implemented)
# def getDownLoadedFileName(driver):
#     driver.execute_script("window.open()")
#     # switch to new tab
#     driver.switch_to.window(driver.window_handles[-1])
#     # navigate to chrome downloads
#     driver.get('chrome://downloads')
#     # define the endTime
#     endTime = time.time()
#     while True:
#         try:
#             # return the file name once the download is completed
#             return driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
#         except:
#             pass
#         time.sleep(1)
#         if time.time() > endTime:
#             break












