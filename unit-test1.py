'''
Created on Oct 17, 2014

@author: pramachandran
'''


from photo_organize import isFileDuplicate
import unittest

class hashTest(unittest.TestCase):

    def testEquals(self):
        self.failUnless(isFileDuplicate("test-images/img1.jpg","test-images/img1_1.jpg" ))
        
    def testNotEquals(self):
        self.failIf(isFileDuplicate("test-images/img1.jpg","test-images/img2.jpg" ))
    
                        
def main():
    unittest.main()

if __name__ == '__main__':
    main()