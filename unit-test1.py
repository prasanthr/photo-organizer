'''
Created on Oct 17, 2014

@author: pramachandran
'''


from photo_organize import isFileDuplicate, createDestFolderMap
import unittest

#class hashTest(unittest.TestCase):

#    def testEquals(self):
#        self.failUnless(isFileDuplicate("test-images/img1.jpg","test-images/img1_1.jpg" ))
        
#    def testNotEquals(self):
#        self.failIf(isFileDuplicate("test-images/img1.jpg","test-images/img2.jpg" ))

class folderMap(unittest.TestCase):
    def test(self):
        fmap = createDestFolderMap("./testdata/test_folder")
        self.failUnlessEqual(fmap,
                {'201102': './testdata/test_folder/2011/02-some_photos1', '201103': './testdata/test_folder/2011/03-some_photos2', '201001': './testdata/test_folder/2010/01'}
                           )
                        
def main():
    unittest.main()

if __name__ == '__main__':
    main()