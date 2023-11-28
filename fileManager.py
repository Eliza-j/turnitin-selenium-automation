import requests
import os
import re
import shutil
import time
import re
import glob
import PyPDF2
import hashlib
import datetime


#receive link
#download
#save to FileDownload
#return downloaded file's path

# directoryPath = '/data/turnitin/temp'
submittedFileDownloadedFolderPath = os.environ.get("submitted_file_folder_path")
# assetsFolderPath = os.getcwd() + "/PlagiarismSelenium/assets/"\
assetsFolderPath = os.getcwd() + "\\PlagiarismSelenium\\assets\\"
downloadedReportTargetFolder = os.getcwd() + "\\PlagiarismSelenium\\DownloadedFile\\"
templateFolderPath = os.getcwd() + '\\PlagiarismSelenium\\template_files\\' 

def getCurrentTimestamp():
  return str(datetime.datetime.now())

def downloadDocs(submittedFileName):
    if not os.path.exists(submittedFileDownloadedFolderPath):
        # Create a new directory because it does not exist 
        os.makedirs(submittedFileDownloadedFolderPath)
        print("The new directory is created!")

    #LIVE
    # linkURLNew = os.environ.get("temp_path") + linkURL
    # linkURL = "http://dkfvnf" + submittedFileName
    # response = requests.get(linkURLNew)

    submittedFilePath = submittedFileDownloadedFolderPath + '/' + submittedFileName
    # open(filePath, "wb+").write(response.content)
    return submittedFilePath

def checkPdfContent(filePath):
    file= open(filePath, 'rb')
    ReadPDF = PyPDF2.PdfReader(file)
    pages = len(ReadPDF.pages)
    #print(pages)

    TWords = 0
    for i in range(pages):
        pageObj = ReadPDF.pages[i]
        text = pageObj.extract_text()
        TWords+=len(text.split())
    #print (TWords)
    file.close()
    return pages, str(TWords)


def clearDownload(filePath):
    if os.path.exists(filePath):
        os.remove(filePath)
    else:
        print("Can not delete the file as it doesn't exists")

def waitDownloadFinished(path):
    start_time = time.time()
    seconds = 180
    while not os.path.exists(path):
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        if elapsed_time > seconds:
            print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Pengunduhan terlalu lama.")
            raise

    if os.path.isfile(path):
        pass
    else:
        raise ValueError("%s isn't a file!" % path)
    
    time.sleep(5)
    return path

def checkTitle(title):
    special_characters = {
      "\"" : True,
      "\\" : True,
      "/"  : True,
      ":"  : True,
      "*"  : True,
      "?"  : True,
      "<"  : True,
      ">"  : True,
      "|"  : True
    }
    
    for c in title:
        if special_characters.get(c) is not None or c == " ":
            title = title.replace(c,"_")
    title = re.sub(' +', ' ',title)

    if len(title) >= 194:
      title = title[0:193]
    return title

def getTemplateFullPath(fileName):
    if len(fileName) == 0:
        return None
    splittedFileName = os.path.splitext(fileName)
    fileNameWithoutFormat = splittedFileName[0]
    format = splittedFileName[1]
    sanitizedFileName = checkTitle(fileNameWithoutFormat) + format

    oldFilePath = templateFolderPath + fileName
    newFilePath = templateFolderPath + sanitizedFileName

    os.rename(oldFilePath, newFilePath)
    return newFilePath

def setDownloadedFileName(id, title):
    return str(id) + '_' + title + '.pdf'

def setDownloadedFilePath(fileName):
    return downloadedReportTargetFolder + fileName

def setWatermark(fileName):
    pdfFile = fileName
    watermarkFile = assetsFolderPath + "watermark.pdf"

    inputFile = open(pdfFile, 'rb')
    inputPDF = PyPDF2.PdfReader(pdfFile)

    watermarkFileOpened = open(watermarkFile, 'rb')
    watermarkFilePDF = PyPDF2.PdfReader(watermarkFile)

    # pdfFirstPage = inputPDf.getPage(0)
    watermarkFirstPage = watermarkFilePDF.pages[0]

    output = PyPDF2.PdfWriter()
    for i in range(len(inputPDF.pages)):
        pdfPage = inputPDF.pages[i]
        pdfPage.merge_page(watermarkFirstPage)
        output.add_page(pdfPage)

    inputFile.close()
    with open(fileName, "wb") as mergedFile:
        output.write(mergedFile)