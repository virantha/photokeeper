Photo Keeper - 
=========================================

|image_pypi| |passing| |quality| 

Photo Keeper is a small script that I wrote to address the demise of my Eye-Fi Wifi SD card.
This script will take a source directory (say the contents of a flash card from a camera), 
scan all the image/video file EXIFs, and sort them into date-based folders in a user-specified
directory.  It will optionally only copy files that have not already been copied (deduplication per 
folder).  Photo Keeper can also upload all the files to Flickr into the same date-based album 
structure, also taking care not to duplicate files.

At some point, I intend to integrate this with the FlashAir series of cards for auto-uploads directly
from the camera, but that is still a work in progress.

* Free and open-source software: ASL2 license
* Blog: http://virantha.com/category/projects/photokeeper
* Documentation: http://virantha.github.io/photokeeper/html
* Source: https://github.com/virantha/photokeeper

Features
########

* Sort image files (JPEG/TIFF) and video files into date-based folders (currently only YYYY-MM-DD format supported)
* Upload images and videos to Flickr into date-based albums
* Avoid duplication of files based on photo taken time, size, and filename

Usage:
######

Examine files
-------------

Examine the files in a given source directory (no changes or copying):

::
    
    photokeeper SRC_DIR examine

Results in:

::

	Examining 482 files in /source
	100%|██████████████████████████████████████▉| 481/482 [00:08<00:00, 59.88file/s]
	Found images from 14 days
	{   '2016-06-24': 5,
		'2016-07-02': 30,
		'2016-07-03': 12,
		'2016-07-04': 32,
		'2016-07-05': 3,
		'2016-07-21': 1,
		'2016-08-02': 20,
		'2016-08-05': 51,
		'2016-09-30': 13,
		'2016-10-09': 131,
		'2016-10-10': 46,
		'2016-10-29': 91,
		'2016-10-31': 45,
		'2016-11-06': 1}
	Total images: 481

Copy files to a directory
-------------------------
Copy the files in a given source directory to a target directory with no duplication:

::

	photokeeper SRC_DIR TGT_DIR dedupe file


Upload files to Flickr
----------------------
First, go to Flickr and get a private key at http://www.flickr.com/services/api/misc.api_keys.html                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                  
Then, create a directory from where you will start photokeeper, and create a file called flickr_api.yaml:                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                                  
.. code-block:: yaml                                                                                                                                                                                                                                                                                                                                              
                                                                                                                                                                                                                                                                                                                                                                  
    key: "YOUR_API_KEY"                                                                                                                                                                                                                                                                                                                                           
    secret: "YOUR_API_SECRET"              

Now, use the following command:

::

	photokeeper SRC_DIR TGT_DIR dedupe flickr



Full help
---------

::

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
		all         Run all steps in the flow (examine,dedupe,flickr,file)
		examine    Examine EXIF tags
		dedupe     Only select files not already present in target directory
		flickr     Upload to flickr
		file       Copy files

	Options:
		-h --help        show this message
		-v --verbose     show more information
		-d --debug       show even more information
		--conf=FILE      load options from file

Installation
############

PhotoKeeper is currently only tested and provided for Python 3.5.  I have no
plans to backport this to Python 2.x as I am shifting all my new development to
3.x exclusively.

.. code-block: bash

    $ pip install photokeeper

Disclaimer
##########

The software is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

.. |image_pypi| image:: https://badge.fury.io/py/photokeeper.png
   :target: https://pypi.python.org/pypi/photokeeper
.. |passing| image:: https://scrutinizer-ci.com/g/virantha/photokeeper/badges/build.png?b=master
.. |quality| image:: https://scrutinizer-ci.com/g/virantha/photokeeper/badges/quality-score.png?b=master
.. |Coverage Status| image:: https://coveralls.io/repos/virantha/photokeeper/badge.png?branch=develop
   :target: https://coveralls.io/r/virantha/photokeeper
