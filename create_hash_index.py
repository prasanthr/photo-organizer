'''
Created on Jan 17, 2017

@author: Prasanth Ram

 create_hash_index <source-folder>

'''

import sys
import os
import hashlib, pickle

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


def createHashIndex(sourceFolder, recreate = False):
    
    for dirpath, dirnames, filenames in os.walk(sourceFolder):        
        #print dirpath, dirnames, filenames
        print "considering  ", dirpath
        
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
            print "Is not a image folder"
            continue
        
        print "Computing hash-index for the folder"
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
        else:
            print "no changes are needed for hash-index"
            
    

if __name__ == '__main__':
    sourceFolder = sys.argv[1]
    print "Creating hash index in ", sourceFolder
    createHashIndex(sourceFolder, False)  
        
        