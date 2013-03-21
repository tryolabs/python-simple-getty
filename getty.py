import json

from time import time
from requests import post


class Session:
    """Getty Session used to interact with the Gettyimages.com API."""

    __GETTY_BASE = 'https://connect.gettyimages.com/v1'
    __SGETTY_BASE = 'https://connect.gettyimages.com/v1'
    __CREATE_SESSION = '/session/CreateSession'
    __RENEW_SESSION = '/session/RenewSession'
    __SEARCH = '/search/SearchForImages'
    __IMAGE_DETAILS = '/search/GetImageDetails'
    __DOWNLOAD_AUTHORIZATIONS = '/download/GetImageDownloadAuthorizations'
    __DOWNLOAD_REQUEST = '/download/CreateDownloadRequest'

    __JSON_HEADER = {'content-type': 'application/json'}

    __REFRESH_AFTER = 60 * 25
    __EXPIRE_AFTER = 60 * 30
    __MAX_SIZE = 1 * 1024 * 1024

    __details_cache = {}

    def __init__(self, system_id, system_password, user_name, user_password):
        """
        Creates a new Session object.

        system_id: The System ID provided by Getty.
        system_password: The System Password provided by Getty.
        user_name: The Getty user you are making requests on behalf of.
        user_password: The password for the Getty user.
        """

        self.__system_id = system_id
        self.__system_password = system_password
        self.__user_name = user_name
        self.__user_password = user_password
        self.__token = None
        self.__secure_token = None
        self.__last_refresh = None

    def __start_session(self):
        request_headers = {'Token': None, 'CoordinationId': None}
        request_body = {'SystemId': self.__system_id,
                        'SystemPassword': self.__system_password,
                        'UserName': self.__user_name,
                        'UserPassword': self.__user_password}

        payload = {'RequestHeader': request_headers,
                   'CreateSessionRequestBody': request_body}

        r = post('%s%s' % (self.__SGETTY_BASE, self.__CREATE_SESSION),
                 json.dumps(payload),
                 headers=self.__JSON_HEADER)

        if r.status_code != 200:
            raise Exception()

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        self.__token = r['CreateSessionResult']['Token']
        self.__secure_token = r['CreateSessionResult']['SecureToken']
        self.__last_refresh = time()

    def __renew_session(self):
        request_headers = {'Token': None, 'CoordinationId': None}
        request_body = {'SystemId': self.__system_id,
                        'SystemPassword': self.__system_password}

        payload = {'RequestHeader': request_headers,
                   'CreateSessionRequestBody': request_body}

        r = post('%s%s' % (self.__SGETTY_BASE, self.__RENEW_SESSION),
             json.dumps(payload),
             headers={self.__JSON_HEADER})

        if r.status_code != 200:
            raise Exception("Got status code: %d" % r.status_code)

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        self.__token = r['CreateSessionResult']['Token']
        self.__secure_token = r['CreateSessionResult']['SecureToken']
        self.__last_refresh = time()

    def __check_session(self):
        if self.__last_refresh is None:
            self.__start_session()
        elif time() - self.__last_refresh > self.__EXPIRE_AFTER:
            self.__start_session()
        elif time() - self.__last_refresh > self.__REFRESH_AFTER:
            self.__renew_session()

    def search(self, keywords, items, from_item):
        """
        Performs a search. Returns a dictionary containing the search results
        including some basic information about them.

        keywords: The keywords to search for.
        items: The maximum number of items to be returned. Please note that not
        all values are valid, only 1, 2 ,3 ,4 ,5 ,6 , 10, 12, 15, 20, 25, 30,
        50, 60 and 75 can be used for tis field.
        from_item: The index of the first image to return. This index is
        1-based.
        """
        self.__check_session()

        request_headers = {'Token': self.__token, 'CoordinationId': None}
        request_query = {'SearchPhrase': keywords}
        request_results = {'ItemCount': items, 'ItemStartNumber': from_item}

        payload = {'RequestHeader': request_headers,
                   "SearchForImages2RequestBody": {
                       'Query': request_query,
                       'ResultOptions': request_results}}

        r = post('%s%s' % (self.__GETTY_BASE, self.__SEARCH),
                 json.dumps(payload),
                 headers=self.__JSON_HEADER)

        if r.status_code != 200:
            raise Exception("Got status code: %d" % r.status_code)

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        ret = []
        for image in r['SearchForImagesResult']['Images']:
            img = {'image_id': image['ImageId'],
                   'source': 'Getty',
                   'title': image['Caption'],
                   'img_url': image['UrlPreview'],
                   'img_thumb': image['UrlThumb']}
            ret.append(img)

        return ret

    def __get_image_details(self, ids):
        self.__check_session()

        request_headers = {'Token': self.__token, 'CoordinationId': None}
        request_body = {'ImageIds': ids,
                        'Language': 'en-us'}

        payload = {'RequestHeader': request_headers,
                   'GetImageDetailsRequestBody': request_body}

        r = post('%s%s' % (self.__GETTY_BASE, self.__IMAGE_DETAILS),
                 json.dumps(payload),
                 headers=self.__JSON_HEADER)

        if r.status_code != 200:
            raise Exception("Got status code: %d" % r.status_code)

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        ret = {}
        for image in r['GetImageDetailsResult']['Images']:
            props = {}
            props['Artist'] = image['Artist']
            props['Caption'] = image['Caption']
            props['PreviewURL'] = image['UrlPreview']
            props['Copyright'] = image['Copyright']
            props['Sizes'] = image['SizesDownloadableImages']

            ret[image['ImageId']] = props
            self.__details_cache[image['ImageId']] = props

        return ret

    def get_image_details(self, ids):
        """
        Returns a dictionary containing metadata for the specified image IDs.

        ids: The ID of an image (String) or a lost of IDs ([String]).
        """
        if type(ids) == str:
            ids = [ids]

        not_found = [i for i in ids if i not in self.__details_cache]
        self.__get_image_details(not_found)

        ret = {}
        for i in ids:
            ret[i] = self.__details_cache[i]

        return ret

    def buy(self, image_id, size=__MAX_SIZE):
        """
        Buys an image. Returns the download URL of the selected image.

        image_id: The id of the image to be bought.
        size: Specifies a preferred image size (in bytes) to download.. By
        default 1MB is used as the preferred image size.
        """
        details = self.get_image_details(image_id)[image_id]

        sizekey = None
        selected_size = 0
        for size in details['Sizes']:
            s = size['FileSizeInBytes']
            #select the biggest one smaller than MAX_SIZE
            #if none is found the smallest image is returned
            if s < size and s > selected_size:
                sizekey = size['SizeKey']
                selected_size = s
            elif selected_size > size and s < selected_size:
                sizekey = size['SizeKey']
                selected_size = s

        if not sizekey:
            raise Exception("There doesn't seem to be any download sizes.")

        self.__check_session()
        request_headers = {'Token': self.__secure_token,
                           'CoordinationId': None}
        request_body = {'ImageSizes':
                            [{'ImageId': image_id,
                              'SizeKey': sizekey}]
                        }

        payload = {'RequestHeader': request_headers,
                   'GetImageDownloadAuthorizationsRequestBody': request_body}

        r = post('%s%s' % (self.__SGETTY_BASE, self.__DOWNLOAD_AUTHORIZATIONS),
                 json.dumps(payload),
                 headers=self.__JSON_HEADER)

        if r.status_code != 200:
            raise Exception("Got status code: %d" % r.status_code)

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        download_token = (r['GetImageDownloadAuthorizationsResult']
                           ['Images'][0]
                           ['Authorizations'][0]
                           ["DownloadToken"])

        request_headers = {'Token': self.__secure_token,
                           'CoordinationId': None}
        request_body = {"DownloadItems":
                            [{'DownloadToken': download_token}]
                        }
        payload = {'RequestHeader': request_headers,
                   'CreateDownloadRequestBody': request_body}

        r = post('%s%s' % (self.__SGETTY_BASE, self.__DOWNLOAD_REQUEST),
                 json.dumps(payload),
                 headers=self.__JSON_HEADER)

        if r.status_code != 200:
            raise Exception("Got status code: %d" % r.status_code)

        r = r.json()
        if r['ResponseHeader']['Status'] != 'success':
            raise Exception(r['ResponseHeader'])

        return r['CreateDownloadRequestResult']['DownloadUrls']
