Photo Organizer Script
----------------------

   This script maintains all your photos in a pre-determined folder structure and makes downloading, de-deuping and organizing of new photos easy.

   The script works on two folders: a destination folder that has the photos in already organized folder structure and a source 
   folder which has the photos yet to be organized.

   It is advised (though not mandatory) that you arrange your organized photo folder in the following structure.

    - year 
         - [month-number]-[Optional-description]
            - photo1.jpg
            - photo2.jpg

    Example

      2015
          - 01-Birthday_Pics
            - photo1.jpg
            - photo2.jpg

   The script first creates an index file in each folder in destination that will contain the file-name and hash value of the contents.
   Then, it picks up all the photos in the source folder one by one and sees if it already exists in destination by looking it up in the index files.
   If it doesn't already exist in the destination, it is copied over into a folder structure as described above. You may add a verbal 
   description to the folder name later. If the exif data cannot be read, the image is copied to "misc" folder in the destination folder.

   The creation of hash-index will take some time when run initially. Once created, this index file will be reused for all future runs. If new
   files are added or existing files are renamed, the index file will be recreated.


Usage
-----
  
   The program requires that you install exiftool (http://www.sno.phy.queensu.ca/~phil/exiftool/)
 
   Run as
  
   photo-store.py <source-folder> <destination-folder>



