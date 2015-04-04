'''
Created on Oct 17, 2014

@author: Prasanth Ram

 photo_organize.py <source-folder> <destination-folder?

 Reads files one by one from the source folder, then puts it into appropriate place
 destination folder

Organization is like this

    - year (ex. 2012)
             - [month-number]-[Optional-description]


'''

import sys
import os
import exifread
import shutil
import hashlib, random

def organize():

    sourceFolder = sys.argv[1]
    destFolder = sys.argv[2]
    #print sourceFolder, destFolder
    allImages = []
    miscFiles = []
    for dirpath, dirnames, filenames in os.walk(sourceFolder):
        #print dirpath, dirnames, filenames 
        for fn in filenames:
            if fn.upper().endswith(".JPG"): 
                allImages.append(dirpath + "/" + fn)
            else:
                miscFiles.append(dirpath + "/" + fn)
    print len(allImages) , " files found"
    
    for srcFilePath in allImages:
        srcFile = open(srcFilePath, 'rb')
        tags = exifread.process_file(srcFile)
        if 'EXIF DateTimeOriginal' in tags:
            date = tags['EXIF DateTimeOriginal'].values.split(":")
            #print date
            #.split(":")
            #2012:07:27 11:53:07
            year = date[0]
            month = int( date[1])
            #print year, month
            destFilePath = destFolder + "/" + str(year) + "/" + str(month)
        else:
            destFilePath = destFolder + "/unsorted"
            
        if not os.path.isdir(destFilePath):
            os.makedirs(destFilePath)
        
        print "copying ", srcFilePath, " to ", destFilePath
        destFilePath += "/" +  os.path.basename(srcFilePath)  
        if os.path.isfile(destFilePath):
        #file already exists
            if isFileDuplicate(destFilePath, srcFilePath):
                print "File is duplicate, skipping"
            else:
                print "Filename is name, contents are different"
                fileName, fileExtension = os.path.splitext(destFilePath)
                destFilePath = fileName + "_" + str(random.randint(1, 1000)) + fileExtension
                shutil.copy2(srcFilePath, destFilePath)
        else:
            shutil.copy2(srcFilePath, destFilePath)
        srcFile.close()


def isFileDuplicate(file1, file2):
    print "Checking for duplicate"
    
    #hasher = hashlib.md5()
    hasher = hashlib.new("md5")
    with open(file1, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
        hash1=hasher.hexdigest()

    hasher = hashlib.new("md5")
    with open(file2, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
        hash2=hasher.hexdigest()
    
    print hash1, hash2
    
    if hash1 == hash2:
        return True
    else:
        return False
    

if __name__ == '__main__':
    organize()



