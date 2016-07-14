'''

@author: Prasanth Ram

 python photo_organize.py <source-folder> <destination-folder>

 source-folder contains the photos you want to sort and organize
 destination-folder your already organized photo folder

  It is advised (though not mandatory) that you arrange your already sorted photo folder in the following structure

    - year 
         - [month-number]-[Optional-description]
            - photo1.jpg
            - photo2.jpg
            

'''

import sys, os
import shutil, filecmp, subprocess
import random, hashlib
import re, json
import pickle

EXIF_TOOL_PATH="/usr/local/bin/exiftool"
ACCEPTED_EXTENSIONS = [ "jpg", "png", "mov"]
IGNORED_FILES = ["thumbs.db"]
HASH_INDEX_FILE = ".picdb"


def getHash(filePath):
    #hasher = hashlib.md5()
    hasher = hashlib.new("md5")
    with open(filePath, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
        return hasher.hexdigest()        
    return None


def createHashIndex(destinationFolder, recreate = False):
    
    #fetch and store the walk result in-order to estimate the time
    osWalkResult = []
    for item in os.walk(destinationFolder):
        osWalkResult.append(item)
        
    totalFolders=len(osWalkResult)
    currentFolderIndex=1
    for dirpath, dirnames, filenames in osWalkResult:        
        #print dirpath, dirnames, filenames
        #print "considering  ", dirpath
        
        # progress bar
        currentFolderIndex+=1
        numdots = int(20.0*(currentFolderIndex+1)/totalFolders)
        sys.stdout.write('\r')
        sys.stdout.write('[%-20s] %d of %d ' % ('='*numdots, currentFolderIndex+1, totalFolders))
        sys.stdout.flush()
        
        #get the list of all files
        allFiles = [] 
        for fn in filenames:
            if fn.startswith(".") or fn.lower() in IGNORED_FILES:
                continue
            allFiles.append(fn)
                
        #see if this is a proper folder with images
        isImageFolder = False
        for fn in allFiles:
            extension = os.path.splitext(fn)[1][1:]
            if extension.lower() in ACCEPTED_EXTENSIONS:
                isImageFolder = True
                break
        if not isImageFolder:
            #print "Is not a image folder"
            continue
        
        #print "Computing hash-index for the folder"
        #get the existing map
        hashEntries = {}
        hashFilePath = dirpath + "/" + HASH_INDEX_FILE
        if not recreate and os.path.isfile(hashFilePath):
            with open(hashFilePath, 'rb') as f:
                hashEntries = pickle.load(f)
            
        needsRefresh = False    
        for fn in allFiles:
            filePath = dirpath + "/" +  fn
            if fn not in hashEntries:
                hashEntries[fn] = getHash(filePath)
                needsRefresh = True
                
        if needsRefresh:
            with open(hashFilePath, 'wb') as f:
                pickle.dump(hashEntries, f) 
        #else:
            #print "no changes are needed for hash-index"
            
               


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


def organize(sourceFolder, destinationFolder):
    
    #create/update hash-index map of the destination folder
    
    print "Loading all Hash entries ....."
    allHashEntries = {}
    #create the hash-index map of all the files key=hash, value=full-path
    #get the files first
    allHashFiles = []
    for dirpath, dirnames, filenames in os.walk(destinationFolder): 
        hashFilePath = dirpath + "/" + HASH_INDEX_FILE
        if os.path.isfile(hashFilePath):
            allHashFiles.append(hashFilePath)            
    #load them with progress bar
    allHashFilesCt = len(allHashFiles)
    print "Total image folders: ", allHashFilesCt
    for idx, hashFile in enumerate(allHashFiles):
        dirpath = os.path.dirname(hashFile)
        with open(hashFile, 'rb') as f:
            hashIndexMap = pickle.load(f)
            for fn_hash in hashIndexMap.items():
                allHashEntries[fn_hash[1]] = dirpath + "/" + fn_hash[0]
               
        # progress bar
        numdots = int(20.0*(idx+1)/allHashFilesCt)
        sys.stdout.write('\r')
        sys.stdout.write('[%-20s] %d of %d ' % ('='*numdots, idx+1, allHashFilesCt))
        sys.stdout.flush()
    print ".... done"
                
    duplicateFiles=0
    copiedFiles=0
        
    # First, go through all files and pick the media files and unprocessable files
    unProcessableFiles = []
    allMediaFiles=[]
    for dirpath, dirnames, filenames in os.walk(sourceFolder):        
        #print dirpath, dirnames, filenames 
        for fn in filenames:
            if fn.startswith(".") or fn.lower() in IGNORED_FILES:
                continue
            extension = os.path.splitext(fn)[1][1:]
            if not extension:
                continue
            if extension.lower() in ACCEPTED_EXTENSIONS:
                allMediaFiles.append(dirpath + "/" + fn)
            else:
                unProcessableFiles.append(dirpath + "/" + fn)
                
    for fileMetadata in getMetadataMap(sourceFolder).items():
        
        sourceFilePath = fileMetadata[0][1] + "/" + fileMetadata[0][0]
        if sourceFilePath not in allMediaFiles: continue                
        if not fileMetadata[1]:
            if sourceFilePath not in unProcessableFiles:
                unProcessableFiles.append(sourceFilePath)
                
        #get the hash and check for duplicates
        fileHash = getHash(sourceFilePath)    
        if fileHash in allHashEntries:
            print "This file ", sourceFilePath[ len(sourceFolder): ], " already exists in the destination [", allHashEntries[fileHash][len(destinationFolder):], "]"
            duplicateFiles+=1
            continue    
        
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
    print "Total number of image files found ", len(allMediaFiles)
    print  copiedFiles, " were copied to appropriate location"
    print  duplicateFiles, " were duplicates and not copied"
    print len(unProcessableFiles), " number of unprocessable files were copied to misc location ", 

    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: python photo_organize.py <source-folder> <destination-folder>"
        sys.exit(-1)
    sourceFolder = sys.argv[1]
    destFolder = sys.argv[2]
    if sourceFolder[-1] == "/": sourceFolder = sourceFolder[:-1]
    if destFolder[-1] == "/": destFolder = destFolder[:-1]
    print "\nCreating a hash-index map of the destination, ", destFolder, " (This may take a while for large folders)..."
    createHashIndex(destFolder, False)    
    print " ... hash-index create/update done\n\n"
    print "Copying photos from ", sourceFolder, " to ", destFolder
    organize(sourceFolder, destFolder)  
                