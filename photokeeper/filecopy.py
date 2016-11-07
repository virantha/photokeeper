# Copyright 2016 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import os, shutil, logging

from target import TargetBase

class FileCopy(TargetBase):

    def __init__(self):
        pass

    def check_duplicates(self, images):
        """ This is easy, since all the functionality is built into the source image file
            object
        """
        print("Checking for duplicates")
        images_1, images_2 = itertools.tee(images)
        for total,img in enumerate(images_1):
            if img.is_duplicate():
                img.dup = True

        n_dups = [i for i in images_2 if i.dup]
        print('Found {} duplicates out of {} images'.format(len(n_dups), total+1))


    def _get_unique_filename_suffix(self, filename):
        dirname = os.path.dirname(filename)
        fn_with_ext = os.path.basename(filename)
        fn, ext = os.path.splitext(fn_with_ext)
        
        suffix = 1
        if not os.path.exists(filename):  # Unique, no target filename conflict
            return filename
        else:
            while os.path.exists(os.path.join(dirname, fn+'_'+str(suffix)+ext)):
                suffix += 1
            return (os.path.join(dirname, fn+'_'+str(suffix)+ext))

    def execute_copy(self, images):

        skip_count = 0
        print("Copying and sorting files")
        for total, img in enumerate(images):
            if img.dup: 
                skip_count+=1
                continue
            srcfn = img.srcpath
            tgtfn = img.tgtpath
            tgtdir = os.path.dirname(tgtfn)
            tgtfn = self._get_unique_filename_suffix(tgtfn)
            logging.info("Copying %s to %s" % (srcfn, tgtfn))
            if not os.path.exists(tgtdir):
                logging.info("Creating directory {}".format(tgtdir))
                os.makedirs(tgtdir)

            shutil.copyfile(srcfn, tgtfn)
        print ("Skipped {} duplicate files".format(skip_count))
        print ("Copied {} files".format(total+1-skip_count))

