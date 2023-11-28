import datetime
import mysql.connector
import os
import db
import fileManager

from itertools import tee, islice, chain

def listWithNext(some_iterable):
    items, nexts = tee(some_iterable, 2)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(items, nexts)

class Job:
  def __init__(self):
    self.id = None
    self.firstName = None
    self.lastName = None
    self.title = None
    self.submittedFileName = None
    self.submittedFilePath = None
    self.paperID = None
    self.prodi_id = None
    
    self.score = None
    self.fileServerName = None
    self.fileServerPath = None

    self.downloadTurnitinFinished = None
    self.uploadTurnitinFinished = None
    self.pages = None
    self.wordCount = None
    self.errorFlag = None

    self.submissionType = None
    self.assignmentId = None
    self.assignmentName = None

class Assignment:
  def __init__(self):
    self.id = None
    self.title = None
    self.prodi_id = None
    self.repoOption = None
    self.excludeBiblio = None
    self.excludeQuoted = None
    self.excludeSmallSources = None
    self.excludeSmallType = None
    self.excludeSmallValue = None
    self.templatePath = None

# Get database connection
dbConn = db.createDBConn()
mycursor = dbConn.cursor()

#SELECT
#Get 10 documents to be uploaded to turnitin
def getUploadQueueRows():
    sqlStatement = """
    SELECT
        id, first_name, last_name, submission_title, submitted_filename, prodi_id, submission_type, assignment_id
    FROM
        jobs
    WHERE
        turnitin_paper_id IS NULL AND status_message IS NULL AND first_name IS NOT NULL
    ORDER BY 
        prodi_id, submitted_timestamp LIMIT 10
    """
    #sqlStatement = "select id, first_name, last_name, submission_title, submitted_filename, prodi_id from turnitin where id = 210"
    mycursor.execute(sqlStatement)
    myresult = mycursor.fetchall()

    jobList = []
    for result in myresult:
       job = Job()

       job.id = result[0]
       job.firstName = result[1]
       job.lastName = result[2]
       job.title = result[3]
       job.submittedFileName = result[4]
       job.prodi_id = result[5]
       job.submissionType = result[6]
       job.assignmentId = result[7]

       jobList.append(job)

    return jobList

#Get 10 documents to be uploaded, according to kodeProdi
def getUploadQueueRowsTest(kodeProdi):
    sqlStatement = """
    SELECT
      cache.turnID, cache.first_name, last_name, cache.submission_title, cache.submitted_filename, cache.prodi_id
    FROM
      (SELECT
         id, first_name, last_name, submission_title, submitted_filename, prodi_id
       FROM
         jobs
       WHERE
         prodi_id = %s AND turnitin_paper_id IS NULL AND status_message IS NULL AND first_name IS NOT NULL
       ORDER BY
         submitted_timestamp LIMIT 5)
    AS cache
    NATURAL JOIN
      jobs
    ORDER BY
      jobs.prodi_id
    """
    mycursor.execute(sqlStatement, (kodeProdi))
    myresult = mycursor.fetchall()

    jobList = []
    for result in myresult:
       job = Job()

       job.id = result[0]
       job.firstName = result[1]
       job.lastName = result[2]
       job.title = result[3]
       job.linkURL = result[4]
       job.prodi_id = result[5]

       jobList.append(job)

    return jobList

#Get turnitin login credentials with prodi_id provided
def getCredential(prodi_id):
    temp = prodi_id
    if prodi_id >= 84:
      prodi_id = 777
    mycursor.execute("select username, password from akun_prodi where prodi_id = %s",([prodi_id]))
    #mycursor.execute("SELECT username, password FROM akun_prodi WHERE prodi_id = 77")
    myresult = mycursor.fetchone()

    return myresult

def getCredentialTest(prodi_id):
    temp = prodi_id
    mycursor.execute("SELECT username, password FROM akun_prodi WHERE prodi_id = %s",([prodi_id]))
    #mycursor.execute("select username, password from akun_prodi where prodi_id = 77")
    myresult = mycursor.fetchone()

    return myresult

#Get 5 documents to be checked if the corresponding similarity report is available in turnitin
def getDownloadQueueRows():
    sqlStatement =   """
    SELECT
        id, turnitin_paper_id, submission_title, prodi_id, submission_type, assignment_id
    FROM
        jobs
    WHERE
        turnitin_downloaded_filename IS NULL AND turnitin_paper_id IS NOT NULL AND first_name IS NOT NULL AND status_message = 'Sedang diproses'
    ORDER BY
        prodi_id, submitted_timestamp LIMIT 10
    """
    #sqlStatement = "select id, turnitin_paper_id, submission_title, prodi_id from turnitin where id = 397"
    mycursor.execute(sqlStatement)
    myresult = mycursor.fetchall()

    jobList = []
    for result in myresult:
      job = Job()
      job.id = result[0]
      job.paperID = result[1]
      job.title = result[2]
      job.prodi_id = result[3]
      job.submissionType = result[4]
      job.assignmentId = result[5]

      jobList.append(job)

    return jobList

#Get 5 documents (per kodeProdi) to be checked if the corresponding similarity report is available in turnitin
def getDownloadQueueRowsTest(kodeProdi):
    sqlStatement =   """
    SELECT
      cache.id, cache.turnitin_paper_id, cache.submission_title, cache.prodi_id
    FROM
      (SELECT
         id, turnitin_paper_id, submission_title, prodi_id
       FROM
         jobs
       WHERE
         prodi_id = %s and turnitin_downloaded_filename IS NULL AND turnitin_paper_id IS NOT NULL AND first_name IS NOT NULL AND status_message = 'Sedang diproses'
       ORDER BY
         submitted_timestamp ASC LIMIT 5)
    AS cache
    NATURAL JOIN
      jobs
    ORDER BY
      jobs.prodi_id
    """
    mycursor.execute(sqlStatement, (kodeProdi))
    myresult = mycursor.fetchall()

    jobList = []
    for result in myresult:
      newJob = Job(result[0], None, None, result[2], None, result[1], result[3])
      jobList.append(newJob)
    return jobList

#Get 5 documents to be deleted from turnitin assignment list (not implemented yet)
def getClearQueueRows(kodeProdi):
  sqlStatement = """
  SELECT
      id, turnitin_paper_id
  FROM
      jobs
  WHERE
      status_message = 'Selesai' AND prodiId = %s
  ORDER BY
      id LIMIT 5
  """
  
  mycursor.execute(sqlStatement, (kodeProdi))
  myresult = mycursor.fetchall()
  jobList = [Job(result[0], None, None, None, None, result[1], None) for result in myresult]
  return jobList

def getAssignmentName(job: Job):
  if job.assignmentId is not None:
    sqlStatement = """SELECT assignment_name FROM assignments WHERE id = %s"""
    mycursor.execute(sqlStatement, [(job.assignmentId)])
    myresult = mycursor.fetchone()
    job.assignmentName = fileManager.checkTitle(myresult[0])
  elif job.submissionType == 2:
    job.assignmentName = "Tugas"
  elif job.submissionType == 0 or job.submissionType == 1:
    job.assignmentName = os.environ.get("default_assignment_name")
  
  return job

def getSingleAssignment(assignmentId) -> Assignment:
  sqlStatement = """
  SELECT 
		assignment_name, prodi_id, repository_option, exclude_biblio, exclude_quoted, exclude_small_sources, exclusion_threshold_type, exclusion_threshold_value, template_name, creation_status_message
	FROM 
		assignments 
	WHERE 
		id = %s"""
  
  mycursor.execute(sqlStatement, ([assignmentId]))
  myresult = mycursor.fetchone()
  assignment = Assignment()
  assignment.id = assignmentId
  assignment.title = fileManager.checkTitle(myresult[0]) 
  assignment.prodi_id = myresult[1]
  assignment.repoOption = myresult[2]
  assignment.excludeBiblio = myresult[3]
  assignment.excludeQuoted = myresult[4]
  assignment.excludeSmallSources = myresult[5]
  assignment.excludeSmallType = myresult[6]
  assignment.excludeSmallValue = myresult[7]
  assignment.templatePath = fileManager.getTemplateFullPath(myresult[8])

  return assignment


#UPDATE
#Change turnitin paper ID for a document
def updatePaperId(row):
  params = []
  params.append(row.paperID)
  params.append(row.id)
  params = tuple(params)
  mycursor.execute("UPDATE jobs SET turnitin_paper_id = %s WHERE id = %s", params)

def restoreJob(row):
  statementList = []
  statementList.append("UPDATE jobs SET turnitin_paper_id = NULL where id = %s")
  statementList.append("UPDATE jobs SET status_message = NULL where id = %s")
  for statement in statementList:
     params = [row.id]
     params = tuple(params)
     mycursor.execute(statement, params)
  commitToJob() 

#Set a status message for a document in job table
def updateStatus(job, message):
  params = [message, job.id]
  params = tuple(params)
  sqlStatement = "UPDATE jobs SET status_message = %s WHERE id = %s"

  mycursor.execute(sqlStatement, params)
  commitToJob()

def setFinished():
  return True

def revertDownload(jobList):
  for row in jobList:
    if not row.downloadTurnitinFinished:
      updateStatus(row, "Sedang diproses")

def revertUpload(jobList):
  for row in jobList:
    if not row.uploadTurnitinFinished:
      updateStatus(row, None)

def setPdfInfo(row):
  params = [row.pages, row.wordCount, row.id]
  params = tuple(params)
  sqlStatement = "UPDATE jobs SET page_count = %s, word_count = %s where id = %s"

  mycursor.execute(sqlStatement, params)
  commitToJob()

#Set timestam for finished document
def updateTimeChecked(row):
  sqlStatement = "UPDATE jobs SET checked_timestamp = CURRENT_TIMESTAMP() WHERE id = %s"
  mycursor.execute(sqlStatement, ([row.id]))

"""
for row in job:
  job.updatePaperPath(row)

"""

#Write the paper's path in the server directory to be accessed from the internet, along with the
#similarity value
def updatePaperPath(row):
  if row.fileServerName is None:
    finalPath = None
  else:
    # finalPath = (r"turnitin-file/" + row.fileServerPath)
    finalPath = (row.fileServerName)
  queryParam1 = []
  queryParam1.insert(0, finalPath)
  queryParam1.append(row.paperID)
  mycursor.execute("UPDATE jobs SET turnitin_downloaded_filename = %s WHERE turnitin_paper_id = %s", (queryParam1))

  queryParam2 = []
  if row.score is not None:
    queryParam2.insert(0, row.score)
    queryParam2.append(row.paperID)
    mycursor.execute("UPDATE jobs SET similarity_score = %s WHERE turnitin_paper_id = %s", (queryParam2))
  else:
    pass

def commitToJob():
  dbConn.commit()


def fillProdiID():
   statement = "Select * from akun_prodi where prodi_id is NULL and id != 27"
   mycursor.execute(statement)
   #mydb.commit()

   myresult = mycursor.fetchall()
   for row in myresult:
    # if count >= 77:
    #    break
    if row[3][4] == "0":
       prodi_id = row[3][5]
    else:
       prodi_id = row[3][4] + row[3][5]
    # prodi_id = str(count)
    statement = "update akun_prodi set prodi_id = '{prodi_id}' where id = %s".format(prodi_id = prodi_id)
    params = [row[0]]
    params = tuple(params)
    mycursor.execute(statement, params)
    # count += 1

   commitToJob()

def updateAssignmentCreationStatus(assignmentId, message):
  params = [message, assignmentId]
  params = tuple(params)
  sqlStatement = "UPDATE assignments SET creation_status_message = %s WHERE id = %s"

  mycursor.execute(sqlStatement, params)
  commitToJob()

def closeConn():
   mycursor.close()
   dbConn.close()
#fillProdiID()

def getCurrentTimestamp():
  return str(datetime.datetime.now())





"""
select distinct prodi_id from job;
prodList = [ps1, ps2, ps3 , switch, xbox, gamecube]
for prod in prodList:
  login(prodID)
  jobList = job.getRowFromPS(prod)
  for row in jobList:
    wsoiehfwoiehjf 
"""

"""
#update
#statement = "update turnitin set status_message = 'Sedang diproses' where status_message = 'Downloading...'"
#statement = "update turnitin set status_message = NULL where status_message = 'Sedang diproses' and turnitin_paper_id IS NULL"
#statement = "update turnitin set status_message = 'Selesai' where status_message = 'Sedang diproses' and similarity_score IS NOT NULL"
#statement = "update turnitin set status_message = 'Unusual number of excessively long or short words.' where status_message = 'Dokumen memiliki kata terlalu panjang atau pendek.'"

#check credential
#statement = "select * from akun_prodi"
#statement = "update akun_prodi set prodi_id = '777' where prodi_id = '77'"
#statement = "select distinct prodi_id from turnitin order by prodi_id"

#check latest entries
#statement = "select * from turnitin where status_message != 'Selesai'"
statement = "select * from turnitin where status_message = 'Sedang diproses'"
#statement = "select * from turnitin where turnID = 1928"
#statement = "select * from turnitin where status_message = 'Downloading...' or status_message = 'Uploading...'"
#statement = "select * from turnitin order by id desc limit 10"
#statement = "select * from turnitin where first_name like 'Defina%'"

#check upload jobs
#statement = "select id, first_name, last_name, submission_title, submitted_filename, prodi_id from turnitin where turnitin_paper_id IS NULL and status_message IS NULL and first_name IS NOT NULL order by submitted_timestamp limit 5"

#check download jobs
#statement = "select id, turnitin_paper_id, submission_title, prodi_id from turnitin where turnitin_downloaded_filename IS NULL AND turnitin_paper_id is NOT null and first_name is NOT NULL order by submitted_timestamp asc limit 5"
mycursor.execute(statement)
#dbConn.commit()

myresult = mycursor.fetchall()
for row in myresult:
 print(row)
"""


    # self.id = id
    # self.firstName = firstName
    # self.lastName = lastName
    # self.title = title
    # self.linkURL = linkURL
    # self.prodi_id = prodi_id
    
    # self.pid = pid
    # self.score = ""
    # self.fileName = ""
    # self.filePath = ""
    # self.pepId = ""

    # self.finished = False
    # self.pages = 0
    # self.wordCount = ""
    # self.errorFlag = False