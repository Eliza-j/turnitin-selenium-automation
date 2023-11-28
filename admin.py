#import local pacakges
import repo
from repo import getCurrentTimestamp
import turnitin
import fileManager
import generateDriver

#import built-in libraries
from time import sleep
import os

processID = str(os.getpid())

def printAttributes(my_object):
    # Using vars() function
    attributes = vars(my_object)
    for attribute, value in attributes.items():
        print(attribute, "=", value)

def generateLog(message):
    print("{timestamp} Proses: {processId} Log: {message}".format(timestamp = getCurrentTimestamp(), processId = processID, message = message))
                
def addAssignmentToTurnitin(assignmentId):
    assignment = repo.getSingleAssignment(assignmentId)
    generateLog("Memulai pembuatan assignment sebagai format baru. Assignment ID: {assignment_id}".format(assignment_id = str(assignment.id)))
    credential = repo.getCredentialTest(assignment.prodi_id)
    print(assignment.prodi_id)
    driver = generateDriver.WebDriverFactory()
    turnitinPage = turnitin.TurnitinPageDriver(driver)

    turnitinPage.login(credential)
    turnitinPage.openHomePage(os.environ.get("class_name"))
    print(os.environ.get("class_name"))
    try:
        turnitinPage.addAssignment(
            assignmentName=assignment.title,
            repositoryOption=assignment.repoOption,
            excludeBiblioOption=assignment.excludeBiblio,
            excludeQuotedOption=assignment.excludeQuoted,
            excludeSmallSources=assignment.excludeSmallSources,
            excludeSmallSourcesType=assignment.excludeSmallType,
            excludeSmallValue=assignment.excludeSmallValue,
            templatePath=assignment.templatePath
            )
    except Exception as e:
        print(str(e))
    generateLog("Selesai membuat format baru. Nama format: {name} Assignment ID: {assignment_id}".format(name = assignment.title, assignment_id = str(assignment.id)))
    repo.updateAssignmentCreationStatus(assignmentId, "Created")
