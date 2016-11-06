# -*- coding: utf-8 -*-
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
import sys, os
import logging

import yaml, pprint
import flickrapi
import urllib.request
from xml.etree import ElementTree
from tqdm import tqdm
import itertools, dateparser, time


class FileWithCallback(object):
    def __init__(self, filename):
        self.file = open(filename, 'rb')
        # the following attributes and methods are required
        self.len = os.path.getsize(filename)
        self.fileno = self.file.fileno
        self.tell = self.file.tell
        self.tqdm = tqdm(total=self.len, ncols=60,unit_scale=True, unit='B')

    def read(self, size):
        self.tqdm.update(size)
        return self.file.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.tqdm.close()


class FlickrMedia(object):
    def __init__(self, json_dict):
        self.json_dict = json_dict
        self.title = json_dict['title']
        self.photoid = json_dict['id']

        dt = json_dict['datetaken']
        self.datetime_taken = dateparser.parse(dt, date_formats=['%Y-%m-%d %H:%M:%S']) 


class PhotoSet(object):

    def __init__(self, json_dict):
        self.json_dict = json_dict
        self.title = json_dict['title']['_content']
        self.setid = json_dict['id']
        self.photos = None

class Photo(object):
    def __init__(self, photo_element):
        """Construct a photo object out of the XML response from Flickr"""
        attrs = { 'farm': 'farmid', 'server':'serverid','id':'photoid','secret':'secret'}
        for flickr_attr, py_attr in attrs.items():
            setattr(self, py_attr, photo_element.get(flickr_attr))
        
    def _construct_flickr_url(self):
        url = "http://farm%s.staticflickr.com/%s/%s_%s_b.jpg" % (self.farmid,self.serverid, self.photoid, self.secret)
        return url

    def download_photo(self, dirname, cache=False, tgt_filename=None):
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        tgt = os.path.join(dirname, "%s.jpg" % self.photoid)
        if cache:
            if os.path.isfile(tgt):
                return tgt
        urllib.request.urlretrieve(self._construct_flickr_url(), tgt)
        return tgt
        
class Flickr(object):

    def __init__(self):
        self.set_keys(*self.read_keys())
        self.get_auth2()
        # Might as well get all the photosets at this point as we'll need them
        self.photosets = self._get_photosets()


    def read_keys(self):
        """
            Read the flickr API key and secret from a local file
        """
        with open("flickr_api.yaml") as f:
            api = yaml.load(f)
        return (api["key"], api["secret"])

    def set_keys(self, key, secret):
        self.api_key = key
        self.api_secret = secret

    def get_auth2(self):
        print("Authenticating to Flickr")
        self.flickr = flickrapi.FlickrAPI(self.api_key, self.api_secret)
        self.flickr.authenticate_via_browser(perms='write')
        print("Authentication succeeded")
        return 

    def get_tagged(self, tags, count, download_dir="photos"):
        """ Get photos with the given list of tags
        """
        print ("connecting to flickr, and getting %d photos with tags %s" % (count, tags))
        x = self.flickr.photos_search(api_key = self.api_key, user_id="me", tags=','.join(tags), per_page=count)
        photos = self._extract_photos_from_xml(x)
        photo_filenames = self._sync_photos(photos, download_dir)
        print("Found %d photos" % len(photos))
        return photo_filenames


    def _sync_photos(self, photos, download_dir="photos", clean_up=False):
        """
            Connect to flickr, and for each photo in the list, download.
            Then, if delete photos that are present locally that weren't present in the list of photos.

            :returns: List of filenames downloaded
        """
        photo_filenames = []
        photo_count = len(photos)
        for i,photo in enumerate(photos):
            print("[%d/%d] Downloading %s from flickr" % (i,photo_count,photo.photoid))
            filename = photo.download_photo(download_dir, cache=True)
            photo_filenames.append(filename)

        # Now, go through and clean up directory if required
        
        if clean_up:
            photo_file_list = ["%s.jpg" % (x.photoid) for x in photos]
            for fn in os.listdir(download_dir):
                full_fn = os.path.join(download_dir, fn)
                if os.path.isfile(full_fn):
                    if not fn in photo_file_list:
                        print ("Flickr sync: Deleting file %s" % fn)
                        os.remove(full_fn)

        return photo_filenames

    def _extract_photos_from_xml(self, xml):
        photos = []
        for i in xml.iter():
            if i.tag == 'rsp':
                # the response header.  stat member should be 'ok'
                if i.get('stat') == 'ok':
                    continue
                else:
                    # error, so just break
                    break
            if i.tag == 'photo':
                photos.append(Photo(i))
        return photos

    def get_recent(self,count, download_dir="photos"):
        """ get the most recent photos
        """
        print ("connecting to flickr, and getting most recent %d photos" % count)
        x = self.flickr.people_getphotos(api_key = self.api_key, user_id="me",per_page=count)
        #x = self.flickr.photos_search(api_key=self.api_key,"me")

        photos = self._extract_photos_from_xml(x)
        photo_filenames = self._sync_photos(photos, download_dir)
        return photo_filenames


    def _get_photosets(self):
        print("Getting photosets from Flickr")
        resp = self.flickr.photosets.getList(format='parsed-json')
        photosets = {}
        for photoset in resp['photosets']['photoset']:
            p = PhotoSet(photoset)
            photosets[p.title] = p #TODO: Possible issue here because multiple photosets could have same title.  Oh well
        return photosets


    def _get_photos_in_album(self, album_name, cached=False):
        photoset = self.photosets[album_name]
        albumid = photoset.setid
        if not photoset.photos or not cached:
            resp = self.flickr.photosets.getPhotos(photoset_id=albumid, extras='date_taken', format='parsed-json')
            photos = {}
            for p in resp['photoset']['photo']:
                myphoto = FlickrMedia(p)
                photos[myphoto.title] = myphoto
            photoset.photos = photos
        return photoset.photos


    def _upload_file(self, filename):
        with FileWithCallback(filename) as f:
            resp = self.flickr.upload(filename=filename, fileobj=f, is_public=0)
            photoid = resp.find('photoid').text
            return photoid


    def _create_new_album(self, album_name, first_photo_filename):

        # First, we need to upload a dummy photo
        photoid = self._upload_file(first_photo_filename)

        resp = self.flickr.photosets.create(title=album_name, primary_photo_id=photoid, format='parsed-json')
         
        albumid = resp['photoset']['id']
        resp = self.flickr.photosets.getInfo(photoset_id=albumid, format='parsed-json')

        return (photoid, resp['photoset'])

        
    def _add_photo_to_album(self, photoid, albumid):
        #tqdm.write("Adding {} to {} ".format(photoid, albumid))
        self.flickr.photosets.addPhoto(photoset_id=albumid, photo_id=photoid)

    def _is_duplicate(self, image):
        album_name = image.tgtdatedir

        if not album_name in self.photosets:
            return False
        else:
            photos = self._get_photos_in_album(album_name, cached=True)
            image_title = os.path.basename(image.filename)
            if not image_title in photos:  # If photo with same title is not found, then no duplicates
                return False
            else:
                # Same title, but let's check the date too, to be sure
                #tqdm.write('{} has local date {}, and flickr date {}'.format(image_title, image.datetime_taken, photos[image_title].datetime_taken))
                if photos[image_title].datetime_taken != image.datetime_taken:
                    return False
                else:
                    return True


    def check_duplicates(self, images):
        print("Checking for duplicates in Flickr")
        images_1, images_2 = itertools.tee(images)
        for total,img in enumerate(images_1):
            if self._is_duplicate(img):
                img.flickr_dup = True

        n_dups = [i for i in images_2 if i.flickr_dup]
        print('Found {} duplicates out of {} images'.format(len(n_dups), total+1))


    def execute_copy(self, images):

        for img in images:
            if img.flickr_dup: continue
            album_name = img.tgtdatedir
            if album_name not in self.photosets:
                # Need to create album
                tqdm.write('Creating new album %s' % album_name)
                photoid, album_dict = self._create_new_album(album_name, img.srcpath)
                p = PhotoSet(album_dict)
                self.photosets[p.title] = p
            else:
                photoid = self._upload_file(img.srcpath)
                self._add_photo_to_album(photoid, self.photosets[album_name].setid)

            tqdm.write("Adding {} to {} ".format(img.filename, album_name))
            # Now, make sure we set the date-taken manually if it's a video
            if img.is_video:
                dt = img.datetime_taken.strftime('%Y-%m-%d %H:%M:%S')
                tqdm.write('Manually setting date on video {} to {}'.format(img.filename, dt))
                self.flickr.photos.setDates(photo_id=photoid, date_taken=dt)



def main():
    #logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    script = Flickr()
    #script.get_recent(10)
    #script.upload('test.jpg')
    script.flickr.photos.setDates(photoid='30735623495', date_taken='2016-06-24 10:12:02')


if __name__ == '__main__':
    main()


