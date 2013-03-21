Python-simple-getty
===================

Description
-----------

__Python-simple-getty__ is a very simple wrapper of Getty's REST API.
__Python-simple-getty__ allows you to `search` for images, `get_image_details` 
for a particular image, and finally `buy` an image. Session handling is done 
automatically, all you need to do is provide your credentials and the rest will 
be done for you.

### What Python-simple-getty is:
* Easy to use.
* Easy to integrate into your own python application.
* Simple code that can be easily modified and adapted to what you need.

### What Python-simple-getty is not:
* A thorough implementation of the Getty API.

Usage
-----

1. Download `getty.py` and place it where your sources are.
2. Install the requirements with `pip install -r requirements.txt`
3. Import the `Session` class like so:

        from getty import Session

4. Create a new instance of the `Session` class, passing it your credentials:

        s = Session('system_id', 'system_pass', 'user_name', 'user_pass')

5. Search for images. You'll have to specify the keywords to search for, how 
many items to return, and what the index of the first item is:

        s.search('Someone', items=50, from_item=1)

6. You can use the `get_image_details` to get some metadata for the search 
results you got. You can call it with just one ID as a `String` or give it 
multiple IDs in a list:

        s.get_image_details([one_id, another_id, ...])

7. Finally you can buy an image specifying it's ID and a optionaly a preferred 
size in bytes of the image to buy:

        s.buy(ID_to_buy, 1024 * 1024)


Getting extra metadata
----------------------

In case you need to get some more metadata when getting and images details, the
`__get_image_details` can be modified to do this easily. Just add the fields 
you want to the `props` dictionay. You can find all available fields 
[here](https://github.com/gettyimages/connect/blob/master/documentation/endpoints/search/GetImageDetails.md#response)

Links
-----

If you feel this wrapper is too simple for what you need, Getty's API 
documentation can be found [here](https://github.com/gettyimages/connect).
