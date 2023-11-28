import os
from selenium import webdriver

currDir = os.getcwd() + '\\PlagiarismSelenium\\'


#set download path


class WebDriverFactory():
    def __new__(cls):
        baseURL = "https://www.turnitin.com/login_page.asp?lang=en_us"
        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : currDir + "DownloadedFile"}
        options.add_experimental_option("prefs",prefs)
        # options.add_argument("--headless")
        driver = driver = webdriver.Chrome(chrome_options=options)

        driver.get(baseURL)
        return driver
