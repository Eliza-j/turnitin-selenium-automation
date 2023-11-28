#import local pacakges
import repo
from repo import getCurrentTimestamp
import turnitin
import fileManager
import generateDriver

#import built-in libraries
from time import sleep
import os

#LIVE
# className = "Dokumen"
# assignmentName = 2023

#Check job table for null Paperpath

def getDownloadJobs():
	jobList = repo.getDownloadQueueRows()
	if len(jobList) == 0:
		raise
	return jobList

def revertJob(jobList):
	print(getCurrentTimestamp() + " Proses: " + str(os.getpid()) + " Log: Menandai dokumen yang belum diproses ke database")
	repo.revertDownload(jobList)

def openTurnitinPage():
    driver = generateDriver.WebDriverFactory()
    return turnitin.TurnitinPageDriver(driver)

def closeDownloadJob():
	repo.commitToJob()
	repo.closeConn()

class DownloadJob():
	className = os.environ.get("class_name")
	assignmentName = os.environ.get("assignment_name")
	
	def __init__(self, jobList):
		self.turnitinPage = None
		self.jobList = jobList
		self.sameAsBefore = False
		self.credential = None
		self.reportNotFinished = False
		self.reportNotExist = False
		self.processID = str(os.getpid())

	def generateLog(self, message):
		print("{timestamp} Proses: {processId} Log: {message}".format(timestamp = getCurrentTimestamp(), processId = self.processID, message = message))
	
	def setDownloadStatus(self):
		for row in self.jobList:
			repo.updateStatus(row, "Downloading...")
			repo.commitToJob()
	
	def generateNewTurnitinPage(self):
		driver = generateDriver.WebDriverFactory()
		self.turnitinPage = turnitin.TurnitinPageDriver(driver)

	def setJobCredential(self, prodiID):
		self.credential = repo.getCredential(prodiID)
		
	def loginTurnitin(self):
		self.turnitinPage.login(self.credential)

	def openPaperList(self, row):
		self.turnitinPage.openHomePage(DownloadJob.className)
		row = repo.getAssignmentName(row)
		self.turnitinPage.openViewAssignment(row.assignmentName) 
		self.turnitinPage.openAllPaper()
	
	def continueDownloadSameProdiID(self, row):
		self.turnitinPage.backToHomepage(DownloadJob.className)
		row = repo.getAssignmentName(row)
		self.turnitinPage.openViewAssignment(row.assignmentName) 
		self.preparationBeforeDownload()

	def preparationBeforeDownload(self):
		self.turnitinPage.getPages()
		self.turnitinPage.setWebDriverWait(300)
		self.turnitinPage.getOriginalAssignmentWindow()
		self.turnitinPage.assertWindowHandleCount()

	def setReportNotFinishedTrue(self):
		self.reportNotFinished = True
	
	def setReportNotExistTrue(self):
		self.reportNotExist = True
	
	def setProdiIdSameAsBefore(self):
		self.sameAsBefore = True

	def revertPage(self):
		self.turnitinPage.backToFirstPage()
		self.turnitinPage.getPages()
		sleep(3)
		
	def sortAssignmentByDate(self):
		self.generateLog("Mengurutkan dokumen pada halaman Assignment Inbox")
		for i in range(2):
			self.turnitinPage.sortAssignmentByDate()
		self.generateLog("Selesai mengurutkan dokumen berdasarkan tanggal")
		
    
	def searchPaperID(self, paperID):
		while True:
			try:
				self.turnitinPage.getReportRowElement(paperID)
				sleep(5)
				break
			except Exception as e:
				if type(e).__name__ == 'NoSuchElementException':
					#Jika sudah sampai halaman terakhir, maka dokumen tidak ada dan akan direset
					#Jika belum sampai halaman terakhir, lanjut halaman berikut
					if len(self.turnitinPage.pageList) == 0:
						self.turnitinPage.backToFirstPage()
						self.turnitinPage.getPages() 
						self.setReportNotExistTrue() 
						break
					self.turnitinPage.nextPage()
					self.turnitinPage.refreshPage()
					self.generateLog("Mencari ke halaman berikut")
					sleep(3)
					continue
    
	def restoreReportNotExist(self, row):
		repo.restoreJob(row)
		self.reportNotExist = False
		self.sameAsBefore = False

	def getOriginalityPercentage(self):
		originalityPercentageRaw = None
		for i in range(5):
			try:
				originalityPercentageRaw = self.turnitinPage.getReportScore()
				break
			except Exception as e:
				# print(type(e).__name__)
				if type(e).__name__ == 'NoSuchElementException':
					self.turnitinPage.refreshPage()
					sleep(5)
					if i == 4:
						self.reportNotFinished = True
						return False
					continue

		if originalityPercentageRaw is not None and originalityPercentageRaw != "--":
			originalityPercentage = originalityPercentageRaw.rstrip(originalityPercentageRaw[-1])
			return int(originalityPercentage)
		elif originalityPercentageRaw == "--":
			return originalityPercentageRaw


	def revertReportNotFinished(self, row):
		repo.updateStatus(row, "Sedang diproses")
		repo.commitToJob()

	def restoreJobFromError(self, row):
		self.generateLog("Terjadi masalah dalam memasuki laman Turnitin")
		repo.updateStatus(row, "Sedang diproses")
		self.turnitinPage.closeTurnitin()

	def startDownloadReport(self, row):
		self.turnitinPage.switchToDownloadWindow()
		try:
			self.turnitinPage.downloadReport()
		except Exception as e:
			self.turnitinPage.closeTurnitin()
			self.sameAsBefore = False
			repo.updateStatus(row, "Sedang diproses")
			raise
		
		self.turnitinPage.backToDownloadWindow()
		row.title = fileManager.checkTitle(row.title)
		row.fileServerName = fileManager.setDownloadedFileName(row.id, row.title)
		row.fileServerPath = fileManager.setDownloadedFilePath(row.fileServerName)

		try:
			self.generateLog("Mengunduh dokumen dengan judul {title}".format(title = row.title))
			fileManager.waitDownloadFinished(row.fileServerPath)
		except:
			self.sameAsBefore = False
			repo.updateStatus(row, "Sedang diproses")
			raise

		

		# row.fileServerName = fileManager.renameFileToMD5(row.fileServerPath)
		# print(row.fileServerName)

	def finishDownloadJob(self, row):
		repo.updatePaperPath(row)
		repo.updateStatus(row, "Selesai")
		repo.updateTimeChecked(row)
		repo.commitToJob()
		row.downloadTurnitinFinished = repo.setFinished()
	
	def setUnfinishedJob(self, row):
		repo.updateStatus(row, "Terjadi kesalahan dari sistem, silahkan submit kembali")
		repo.updateTimeChecked(row)
		repo.commitToJob()
		row.downloadTurnitinFinished = repo.setFinished()

	def revertUnfinishedJobs(self):
		self.generateLog("Mengembalikan proses yang belum selesai ke bentuk semula")
		repo.revertDownload(self.jobList)
		
	def startDownloadJob(self):
		print(getCurrentTimestamp() + " Log: Proses " + str(os.getpid()))
		self.generateLog("Memulai proses download dari Turnitin")
		self.setDownloadStatus()
		for job, nextJob in repo.listWithNext(self.jobList):
			self.generateLog("Mengecek Paper ID {paperId}, Row ID {rowId}".format(paperId = str(job.paperID), rowId = str(job.id)))
			if not self.sameAsBefore:
				try:
					self.generateNewTurnitinPage()
					self.generateLog("Login menuju akun {prodiId}".format(prodiId = str(job.prodi_id)))
					self.setJobCredential(job.prodi_id)
					self.loginTurnitin()
					self.openPaperList(job)
					self.preparationBeforeDownload()
				except Exception as e:
					self.restoreJobFromError(job)
					print(str(e))
					continue
			else:
				self.continueDownloadSameProdiID(job)
			
			self.sortAssignmentByDate()
			self.searchPaperID(job.paperID)
			if self.reportNotExist:
				self.generateLog("Dokumen dengan Paper ID {paperId} tidak ditemukan di halaman Turnitin. Mereset...".format(paperId = str(job.paperID)))
				self.restoreReportNotExist()
				continue
			
			job.score = self.getOriginalityPercentage()
			if job.score == "--":
				job.score = None
				self.generateLog("Dokumen dengan Paper ID {paperId} tidak bisa diunduh.".format(paperId = str(job.paperID)))
				self.generateLog("Melanjutkan...")
				self.setUnfinishedJob(job)
				continue

			if self.reportNotFinished:
				self.generateLog("Dokumen dengan Paper ID {paperId} belum bisa diakses.".format(paperId = str(job.paperID)))
				self.revertReportNotFinished(job)
				continue
			
			try:
				self.startDownloadReport(job)
				self.generateLog("Menambahkan watermark...")
				fileManager.setWatermark(job.fileServerPath)
			except Exception as e:
				self.generateLog("Terjadi gangguan dalam pengunduhan. Lanjut dokumen berikut....")
				print(str(e))
				continue
			if nextJob is not None and nextJob.prodi_id == job.prodi_id:
				self.setProdiIdSameAsBefore()
			else:
				self.sameAsBefore = False
				self.turnitinPage.closeTurnitin()

			self.generateLog("Dokumen dengan Paper ID {paperId} telah selesai diunduh".format(paperId = str(job.paperID)))
			self.finishDownloadJob(job)

		self.turnitinPage.closeTurnitin()

