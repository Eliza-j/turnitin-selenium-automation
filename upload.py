#import local packages
import repo
from repo import getCurrentTimestamp
import fileManager
import turnitin
import generateDriver

#import built-in libraries
import os
# import time

#import third party

#LIVE
# className = "Dokumen"
# assignmentName = 2023

# #LOCAL
# className = os.environ.get("class_name")
# assignmentName = os.environ.get("assignment_name")

def getUploadJobs():
    #Check job table for null PaperId
    jobList = repo.getUploadQueueRows()
    if len(jobList) == 0:
        raise
    return jobList

def getUploadJobFiles(job):
    job.submittedFilePath = fileManager.downloadDocs(job.submittedFileName)
    print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Berhasil mengambil dokumen dengan id " + str(job.id) + " dari server")
    job.pages, job.wordCount = fileManager.checkPdfContent(job.submittedFilePath)

def openTurnitinPage():
    driver = generateDriver.WebDriverFactory()
    return turnitin.TurnitinPageDriver(driver)


class UploadJob():
    className = os.environ.get("class_name")
    # assignmentName = os.environ.get("assignment_name")

    def __init__(self, jobList):
        self.turnitinPage = None
        self.jobList = jobList
        self.sameAsBefore = False
        self.credential = None
        self.processID = str(os.getpid())

    def generateLog(self, message):
        print("{timestamp} Proses: {processId} Log: {message}".format(timestamp = getCurrentTimestamp(), processId = self.processID, message = message))

    def downloadSubmittedDocs(self):
        for row in self.jobList:
            try:
                getUploadJobFiles(row)
                repo.setPdfInfo(row)
            except Exception as e:
                self.generateLog("Terjadi kesalahan dalam pengambilan dokumen {row}. Error: {errorMsg}".format(row = str(row.id), errorMsg = str(e)))
                if str(e) == "EOF marker not found":
                    repo.updateStatus(row, "Dokumen tak terbaca")
                row.errorFlag = True
                continue
        repo.updateStatus(row, "Uploading...")
        repo.commitToJob()
    
    def setJobCredential(self, prodiID):
        self.credential = repo.getCredential(prodiID)

    def generateNewTurnitinPage(self):
        driver = generateDriver.WebDriverFactory()
        self.turnitinPage = turnitin.TurnitinPageDriver(driver)

    def loginTurnitin(self):
        self.turnitinPage.login(self.credential)

    def goToSubmitPage(self, row):
        self.turnitinPage.openHomePage(UploadJob.className)
        row = repo.getAssignmentName(row)
        self.turnitinPage.openSubmitPage(row.assignmentName)
    
    def restoreJobFromError(self, row):
        repo.updateStatus(row, None)
        repo.commitToJob()
        self.turnitinPage.closeTurnitin()

    def continueUploadSameProdiID(self, row):
        self.turnitinPage.backToHomepage(UploadJob.className)
        row = repo.getAssignmentName(row)
        self.turnitinPage.openSubmitPage(row.assignmentName)

    def checkUploadTurnitinError(self, e, row):
        self.generateLog("Terjadi error dalam pengisian dokumen ke dalam turnitin. Error: {errMsg}".format(errMsg = str(e)))
        print(str(e))
        if self.turnitinPage.checkLessWordsError():
            self.generateLog("Pesan Turnitin: The document has little to no text")
            repo.updateStatus(row, "Dokumen kurang dari 20 kata")
            row.uploadTurnitinFinished = True
        elif self.turnitinPage.checkUnreadableDocsError():
            self.generateLog("Pesan Turnitin: The document is unreadable")
            repo.updateStatus(row, "Dokumen tak terbaca")
            row.uploadTurnitinFinished = True
        elif self.turnitinPage.checkUnusualDocsError():
            self.generateLog("Pesan Turnitin: The document have to many short or long words")
            repo.updateStatus(row, "Unusual number of excessively long or short words. Upload again")
            row.uploadTurnitinFinished = True
        elif self.turnitinPage.checkDuplicateSubmissionError():
            self.generateLog("Pesan Turnitin: This student has already submitted a paper to this assignment.")
        else:
            repo.updateStatus(row, None)

        self.generateLog("Lanjut upload dokumen berikut")
        self.turnitinPage.closeTurnitin()
        self.sameAsBefore = False

    def startUploadReport(self, row):
        self.turnitinPage.uploadDoc(row)

    def finishUploadJob(self, row):
        self.generateLog("{jobId} telah terupload ke Turnitin".format(jobId=str(row.id)))
        repo.updatePaperId(row)
        repo.updateStatus(row, "Sedang diproses")
        repo.commitToJob()
        row.uploadTurnitinFinished = True
        self.generateLog("{jobId} telah diupdate di database".format(jobId=str(row.id)))
    
    def revertUnfinishedJobs(self):
        self.generateLog("Mengembalikan proses yang belum selesai ke bentuk semula")
        repo.revertUpload(self.jobList)
        
    def startUploadJob(self):
        print(getCurrentTimestamp() + " Log: Proses " + str(os.getpid()))
        self.generateLog("Memulai proses upload ke Turnitin")
        self.downloadSubmittedDocs()

        for job, nextJob in repo.listWithNext(self.jobList):
            if job.errorFlag:
                fileManager.clearDownload(job.submittedFilePath)
                continue
            if not self.sameAsBefore:
                try:
                    self.generateNewTurnitinPage()
                    self.generateLog("Login menuju akun {prodiId}".format(prodiId = str(job.prodi_id)))
                    self.setJobCredential(job.prodi_id)
                    self.loginTurnitin()
                    self.goToSubmitPage(job)
                except Exception as e:
                    self.generateLog("Terjadi masalah dalam laman Turnitin. Error = {errMsg}".format(errMsg=str(e)))
                    self.restoreJobFromError(job)
                    continue
            else:
                self.continueUploadSameProdiID(job)

            try:
                self.startUploadReport(job)
            except Exception as e:
                self.checkUploadTurnitinError(e, job)
                continue

            if nextJob is not None and nextJob.prodi_id == job.prodi_id:
                self.sameAsBefore = True
            else:
                self.sameAsBefore = False
                self.turnitinPage.closeTurnitin()

            self.generateLog("Dokumen dengan row ID {rowId} telah selesai diupload".format(rowId = str(job.id)))
            self.finishUploadJob(job)


