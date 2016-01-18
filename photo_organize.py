'''
Created on Oct 17, 2014

@author: Prasanth Ram

 photo_organize.py <source-folder> <destination-folder>

 Reads files one by one from the source folder, then puts it into appropriate place
 destination folder

Organization is like this

    - year (ex. 2012)
             - [month-number]-[Optional-description]
             
             
       description should contain only alphanumeric chars and _
       if there are more than one folder for the same month, image will be copied to one randomly selected folder

'''

import sys
import os
import exifread
import shutil, filecmp, subprocess
import random
import re
import json

EXIF_TOOL_PATH="/usr/local/bin/exiftool"
ACCEPTED_EXTENSIONS = [ "jpg", "png", "mov"]

#  this class is based on code from Sven Marnach (http://stackoverflow.com/questions/10075115/call-exiftool-from-a-python-script)
class ExifTool(object):
    """used to run ExifTool from Python and keep it open"""

    sentinel = "{ready}"

    def __init__(self, executable=EXIF_TOOL_PATH, verbose=False):
        self.executable = executable
        self.verbose = verbose

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.rstrip(' \t\n\r').endswith(self.sentinel):
            increment = os.read(fd, 4096)
            if self.verbose:
                sys.stdout.write(increment)
            output += increment
        return output.rstrip(' \t\n\r')[:-len(self.sentinel)]

    def get_metadata(self, *args):

        try:
            return json.loads(self.execute(*args))
        except ValueError:
            sys.stdout.write('No files to parse or invalid data\n')
            exit()
            
def getMetadataMap(srcFolder):
    
    exifToolArgs = ['-j', '-a', '-G', '-r', sourceFolder]
    
    # get all metadata
    with ExifTool(verbose=False) as exifToolWrapper:
        print('Preprocessing with ExifTool.  May take a while for a large number of files.')
        sys.stdout.flush()
        allFilesMetadata = exifToolWrapper.get_metadata(*exifToolArgs)
    
    #print "metadata...", allFilesMetadata
    metadataMap = {}
    for fileMetadata in allFilesMetadata:
        #u'File:FileName'
        #u'File:Directory'
        #u'QuickTime:MediaCreateDate'
        #u'EXIF:DateTimeOriginal'
        fileName = str(fileMetadata[u'File:FileName'])
        directory = str(fileMetadata[u'File:Directory'])
        #print fileMetadata,"\n\n\n"
        if u'QuickTime:MediaCreateDate' in fileMetadata:
            creationDateStr = fileMetadata[u'QuickTime:MediaCreateDate']
        elif u'EXIF:DateTimeOriginal' in fileMetadata:
            creationDateStr = fileMetadata[u'EXIF:DateTimeOriginal']
        #2012:07:27 11:53:07
        if not creationDateStr:
            metadataMap[(fileName, directory)] = None
            continue
        creationDate =  str(creationDateStr).split(":")
        if len(creationDate)<5:
            metadataMap[(fileName, directory)] = None
            continue
        metadataMap[(fileName, directory)] = (creationDate[0],creationDate[1])
    
    return metadataMap


#
def createDestFolderMap(destinationFolder): 
    folderMap = {}
    yearMonthPattern = re.compile(r"\S+/(\d\d\d\d)/(\d\d)\-?(\w*)$")
    for dirpath, dirnames, filenames in os.walk(destinationFolder):        
        match = yearMonthPattern.match(dirpath) 
        if match:
            year = match.group(1)
            month = match.group(2)
            #print "year=", year, "month=", month
            folderMap[year+month] = dirpath
    return folderMap

def organize(sourceFolder, destinationFolder):
    

    duplicateFiles=0
    copiedFiles=0
    
    # As a safety check, get the total number of media files and list of unProcessableFiles in the folder
    unProcessableFiles = []
    totalMediaFiles=0
    for dirpath, dirnames, filenames in os.walk(sourceFolder):        
        #print dirpath, dirnames, filenames 
        for fn in filenames:
            if fn.startswith(".") or fn == "Thumbs.db":
                continue
            extension = os.path.splitext(fn)[1][1:]
            if not extension:
                continue
            if extension.lower() in ACCEPTED_EXTENSIONS:
                totalMediaFiles+=1
            else:
                unProcessableFiles.append(dirpath + "/" + fn)
                
    for fileMetadata in getMetadataMap(sourceFolder).items():
        
        sourceFilePath = fileMetadata[0][1] + "/" + fileMetadata[0][0]
        if not fileMetadata[1]:
            if sourceFilePath not in unProcessableFiles:
                unProcessableFiles.append(sourceFilePath)
        
        year =   fileMetadata[1][0]       
        month =   fileMetadata[1][1]
        destFilePath = destinationFolder + "/" + str(year) + "/" + str(month)
        if not os.path.isdir(destFilePath):
            os.makedirs(destFilePath)    
        destFilePath += "/" +  os.path.basename(sourceFilePath)     
            
        if os.path.isfile(destFilePath):
        #file already exists
            if filecmp.cmp(destFilePath, sourceFilePath):
                print "File ", sourceFilePath, " is duplicate, skipping"
                duplicateFiles+=1
            else:
                print "File ", sourceFilePath, " exists at destination, but contents are different.. renaming and copying"
                fileName, fileExtension = os.path.splitext(destFilePath)
                destFilePath = fileName + "_" + str(random.randint(1, 1000)) + fileExtension
                shutil.copy2(sourceFilePath, destFilePath)
                copiedFiles+=1
        else:
            print "Copying ", sourceFilePath, " to ", destFilePath
            shutil.copy2(sourceFilePath, destFilePath)
            copiedFiles+=1    
              
    #copy all un-processable files to "misc" folder            
    unSortedFilePath = destinationFolder + "/misc"   
    if not os.path.isdir(unSortedFilePath):
            os.makedirs(unSortedFilePath) 
    for srcFilePath in unProcessableFiles:
        print "Copying ", srcFilePath, " to ", unSortedFilePath
        shutil.copy2(srcFilePath, unSortedFilePath)

    print "\n\n"
    print "Total number of image files found ", totalMediaFiles
    print  copiedFiles, " were copied to appropriate location"
    print  duplicateFiles, " were duplicates and not copied"
    print len(unProcessableFiles), " number of unprocessable files were copied to misc location ", 

    
    

if __name__ == '__main__':
    sourceFolder = sys.argv[1]
    destFolder = sys.argv[2]
    print "Copying photos from ", sourceFolder, " to ", destFolder
    organize(sourceFolder, destFolder)  
        
        