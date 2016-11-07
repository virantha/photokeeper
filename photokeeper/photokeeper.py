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

"""

Usage:
    photokeeper.py [options] SOURCE_DIR examine
    photokeeper.py [options] SOURCE_DIR TARGET_DIR [dedupe] file
    photokeeper.py [options] SOURCE_DIR [dedupe] flickr
    photokeeper.py [options] SOURCE_DIR TARGET_DIR [dedupe] file flickr
    photokeeper.py [options] SOURCE_DIR TARGET_DIR all
    photokeeper.py --conf=FILE
    photokeeper.py -h

Arguments:
    SOURCE_DIR  Source directory of photos
    TARGET_DIR  Where to copy the image files
    all         Run all steps in the flow (%s)
%s

Options:
    -h --help        show this message
    -v --verbose     show more information
    -d --debug       show even more information
    --conf=FILE      load options from file

"""

from docopt import docopt
import yaml
import sys, os, logging, shutil, datetime, pprint, filecmp
from collections import OrderedDict, defaultdict
from schema import Schema, And, Optional, Or, Use, SchemaError
import piexif, dateparser

from tqdm import tqdm
from photokeeper.flickr import Flickr
from photokeeper.filecopy import FileCopy

from photokeeper.version import __version__
from photokeeper.utils import ordered_load, merge_args

"""
   
.. automodule:: photokeeper
    :private-members:
"""
class ImageFile(object):
    def __init__(self, srcdir, filename, tgtbasedir, tgtdatedir, datetime_taken, exif_timestamp_missing=False):
        self.srcdir = srcdir
        self.filename = filename
        self.tgtbasedir = tgtbasedir
        self.tgtdatedir = tgtdatedir
        self.datetime_taken = datetime_taken
        self.dup = False
        self.flickr_dup = False
        self.exif_timestamp_missing = exif_timestamp_missing
        #print("adding {} with datetime {}".format(filename, datetime_taken.strftime('%Y-%m-%d %H:%M:%S')))
        pass

    @property
    def srcpath(self):
        return os.path.join(self.srcdir, self.filename)
    
    @property
    def tgtpath(self):
        return os.path.join(self.tgtbasedir, self.tgtdatedir, self.filename)

    def is_duplicate(self, shallow_compare = True):
        # First, see if there is a file already there
        if not os.path.exists(self.tgtpath):
            return False
        elif os.path.getsize(self.srcpath) != os.path.getsize(self.tgtpath):
            return False
        #elif not filecmp.cmp(self.srcpath, self.tgtpath, shallow_compare):  # This is too slow over a network share
        #   return False
        return True


class PhotoKeeper(object):
    """
        The main clas.  Performs the following functions:

    """

    def __init__ (self):
        """ 
        """
        self.args = None
        self.flow = OrderedDict([ ('examine', 'Examine EXIF tags'),
                                  ('dedupe', 'Only select files not already present in target directory'),
                                  ('flickr', 'Upload to flickr'),
                                  ('file',    'Copy files'),
                      ])
        self.images = []




    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        padding = max([len(x) for x in self.flow.keys()]) # Find max length of flow step names for padding with white space
        docstring = __doc__ % (#'|'.join(self.flow), 
                              ','.join(self.flow.keys()),
                              '\n'.join(['    '+k+' '*(padding+4-len(k))+v for k,v  in self.flow.items()]))
        args = docopt(docstring, version=__version__)

        # Load in default conf values from file if specified
        if args['--conf']:
            with open(args['--conf']) as f:
                conf_args = yaml.load(f)
        else:
            conf_args = {}
        args = merge_args(conf_args, args)
        logging.debug (args)
        schema = Schema({
            'SOURCE_DIR': Or(os.path.isdir, error='Source directory does not exist'),
            'TARGET_DIR': Or(lambda x: x is None, os.path.isdir, error='Destination directory does not exist'),
            object: object
            })
        try:
            args = schema.validate(args)
        except SchemaError as e:
            exit(e)

        logging.debug (args)
        if args['all'] == 0:
            for f in list(self.flow):
                if args[f] == 0: del self.flow[f]
            logging.info("Doing flow steps: %s" % (','.join(self.flow.keys())))

        self.src_dir = args['SOURCE_DIR']
        self.tgt_dir = args['TARGET_DIR']
        if self.tgt_dir:
            assert os.path.abspath(self.src_dir) != os.path.abspath(self.tgt_dir), 'Target and source directories cannot be the same'

        if args['--debug']:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        elif args['--verbose']:
            logging.basicConfig(level=logging.INFO, format='%(message)s')   

        self.args = args # Just save this for posterity


    def get_file_count(self, _dir):
        cnt = 0
        for root, dirs, files in os.walk(_dir):
            cnt += len(files)
        return cnt


    def examine_files(self, img_dir):
        counts = defaultdict(int)
        dt_format = '%Y-%m-%d'
        pp = pprint.PrettyPrinter(indent=4)
        raw_count = self.get_file_count(img_dir)
        print("Examining {} files in {}".format(raw_count, img_dir))
        with tqdm(total=raw_count, ncols=80, unit='file') as progress:
            for root, dirs, files in os.walk(img_dir):
                for fn in files:
                    if fn.startswith('.'): continue
                    filename = os.path.join(root, fn)
                    progress.update(1)
                    try:
                        exif_timestamp_missing = False
                        tags_dict = piexif.load(filename)
                        image_date = tags_dict['0th'][piexif.ImageIFD.DateTime]
                        # Why am I even using dateparser if it can't parse this??
                        image_datetime = dateparser.parse(image_date.decode('utf8'), date_formats=['%Y:%m:%d %H:%M:%S']) 
                    except (KeyError, ValueError) as e:

                        logging.info('IGNORED: %s is not a JPG or TIFF' % (filename))
                        file_mod_time = os.path.getmtime(filename)
                        image_datetime = datetime.datetime.fromtimestamp(file_mod_time)
                        logging.info('Using %s ' % (image_datetime))
                        exif_timestamp_missing = True  # Need to mark this since we don't have EXIF and Flickr doesn't honor file date for date-taken
                    
                    image_datetime_text = image_datetime.strftime(dt_format)
                    counts[image_datetime_text] += 1
                    self.images.append(ImageFile(os.path.dirname(filename), os.path.basename(filename), self.tgt_dir, image_datetime_text, image_datetime, exif_timestamp_missing))

        counts = dict(counts)
        total = sum(counts.values())
        print('Found images from {} days'.format(len(counts)))
        pp.pprint (counts)
        
        print('Total images: {}'.format(total))


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
            


    def all_images(self):
        n = len(self.images)
        with tqdm(total=n, ncols=80, unit='file') as progress:
            for i, img in enumerate(self.images):
                yield img
                progress.update(1)

    def go(self, argv):
        """ 
            The main entry point into PhotoKeeper

            #. Do something
            #. Do something else
        """
        # Read the command line options
        self.get_options(argv)
        self.examine_files(self.src_dir)
        for photo_target, TargetClass in [('file', FileCopy), ('flickr', Flickr)]:
            if photo_target in self.flow:
                f = TargetClass()
                if 'dedupe' in self.flow:
                    f.check_duplicates(self.all_images())
                f.execute_copy(self.all_images())

def main():
    script = PhotoKeeper()
    script.go(sys.argv[1:])

if __name__ == '__main__':
    main()

