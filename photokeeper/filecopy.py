import itertools
import os, shutil, logging

class FileCopy(object):

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

