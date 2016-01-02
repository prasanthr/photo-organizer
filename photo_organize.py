'''
Created on Oct 17, 2014

@author: Prasanth Ram

 photo_organize.py <source-folder> <destination-folder?

 Reads files one by one from the source folder, then puts it into appropriate place
 destination folder

Organization is like this

    - year (ex. 2012)
             - [month-number]-[Optional-description]
             
             
       description should contain only alphanumeric-chars and _
       if there are more than one folder for the same month, image will be copied to one randomly selected folder

'''

import sys
import os
import exifread
import shutil, filecmp, subprocess
import random
import re
import json

exifToolPath="/usr/local/bin/exiftool"


#  this class is based on code from Sven Marnach (http://stackoverflow.com/questions/10075115/call-exiftool-from-a-python-script)
class ExifTool(object):
    """used to run ExifTool from Python and keep it open"""

    sentinel = "{ready}"

    def __init__(self, executable=exifToolPath, verbose=False):
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
    sortedFiles= 0
    unsortedFiles=0
    duplicateFiles=0
    unSortedFilePath = destinationFolder + "/misc"
    if not os.path.isdir(unSortedFilePath):
            os.makedirs(unSortedFilePath)
    #folderMap = createDestFolderMap(destinationFolder)
    
    #go through all files and a form a list of all .jpg files and a list of misc files
    allImages = []
    miscFiles = []    
    for dirpath, dirnames, filenames in os.walk(sourceFolder):        
        #print dirpath, dirnames, filenames 
        for fn in filenames:
            if fn.startswith(".") or fn == "Thumbs.db":
                continue
            if fn.upper().endswith(".JPG") or fn.upper().endswith(".MOV") : 
                allImages.append(dirpath + "/" + fn)
            else:
                miscFiles.append(dirpath + "/" + fn)
    print (len(allImages) +len(miscFiles)) , " total files found"
    
    for srcFilePath in allImages:
        srcFile = open(srcFilePath, 'rb')
        tags = exifread.process_file(srcFile)
        if 'EXIF DateTimeOriginal' in tags:
            date = tags['EXIF DateTimeOriginal'].values.split(":")
            #2012:07:27 11:53:07
            year = date[0]
            month = date[1]
            #print year, month
            #destFilePath = folderMap[year+month]
            #if destFilePath:
                #print "Destination folder already exists for ", year, month
            #else:
                #destFilePath = destinationFolder + "/" + str(year) + "/" + str(month)
            destFilePath = destinationFolder + "/" + str(year) + "/" + str(month)
            sortedFiles+=1
        else:
            print "Exif not found for ", srcFilePath
            destFilePath = unSortedFilePath
            unsortedFiles+=1
            
        if not os.path.isdir(destFilePath):
            os.makedirs(destFilePath)
        
        #print "copying ", srcFilePath, " to ", destFilePath
        destFilePath += "/" +  os.path.basename(srcFilePath)  
        if os.path.isfile(destFilePath):
        #file already exists
            if filecmp.cmp(destFilePath, srcFilePath):
                print "File ", srcFilePath, " is duplicate, skipping"
                duplicateFiles+=1
                sortedFiles-=1
            else:
                print "Filename is same, contents are different"
                fileName, fileExtension = os.path.splitext(destFilePath)
                destFilePath = fileName + "_" + str(random.randint(1, 1000)) + fileExtension
                shutil.copy2(srcFilePath, destFilePath)
        else:
            shutil.copy2(srcFilePath, destFilePath)
            
        srcFile.close()
        
        
    for srcFilePath in miscFiles:
        shutil.copy2(srcFilePath, unSortedFilePath)
        unsortedFiles+=1

    print "Copied ", sortedFiles, " into proper location"
    print "Copied ", unsortedFiles, " into unsorted location"
    print  duplicateFiles, " were duplicates"
    
    

if __name__ == '__main__':
    sourceFolder = sys.argv[1]
    #destFolder = sys.argv[2]
    #print "Copying photos from ", sourceFolder, " to ", destFolder
    #organize(sourceFolder, destFolder)
    
    # setup arguments to exiftool
    exifToolArgs = ['-j', '-a', '-G', '-r', sourceFolder]
    
    # get all metadata
    with ExifTool(verbose=False) as exifToolWrapper:
        print('Preprocessing with ExifTool.  May take a while for a large number of files.')
        sys.stdout.flush()
        allFilesMetadata = exifToolWrapper.get_metadata(*exifToolArgs)
    
    #print "metadata...", allFilesMetadata
    for fileMetadata in allFilesMetadata:
        #u'File:FileName'
        #u'File:Directory'
        #u'QuickTime:MediaCreateDate'
        #u'EXIF:CreateDate'
        print "data.....", fileMetadata
        print "\n\n\n\n"
        
        
        