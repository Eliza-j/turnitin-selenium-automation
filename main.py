#import local packages

import repo
from repo import getCurrentTimestamp
import turnitin
import fileManager
import generateDriver
import upload
import download
import admin

#import built-in libraries
import sys

#import third party libraries
from dotenv import load_dotenv
load_dotenv()


mode = sys.argv[1]

if mode == "upload":
    try:
        uploadJobList = upload.getUploadJobs()
    except Exception as e:
        print("Tidak ada job yang perlu dieksekusi")
        print(str(e))
        exit()
    try:
        uploadJobs = upload.UploadJob(uploadJobList)
        uploadJobs.startUploadJob()
    finally:
        uploadJobs.revertUnfinishedJobs()
elif mode == "download":
    try:
        downloadJobList = download.getDownloadJobs()
    except:
        print("Tidak ada job yang perlu dieksekusi")
        exit()
    try:
        downloadJobs = download.DownloadJob(downloadJobList)
        downloadJobs.startDownloadJob()
    finally:
        downloadJobs.revertUnfinishedJobs()

elif mode == "admin":
    admin.addAssignmentToTurnitin(sys.argv[2])

