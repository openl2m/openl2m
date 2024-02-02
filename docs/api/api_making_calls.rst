.. image:: ../_static/openl2m_logo.png

================
Making API Calls
================

*An example REST client can be found at* https://github.com/openl2m/api_client

**All examples use the Python "requests" library !**

Make a call as such:

.. code-block:: python

    import requests

    headers = {
        "Authorization": "Token <your token>",
        "Content-Type": "application/json",     # we use JSON posting format.
        }
    url="your OpenL2M server url"
    response = requests.get(url=url, headers=headers)    # a GET api call
    response = request.post(url=url, headers=headers, json={ 'var': value } )   # a POST api call

If the API return is successful (ie. 200),
you can find the resulting data in "*response.json()*". Parse as needed.

If there is an error, the server may return a "reason" entry. You can parse this also with *response.json()*

.. code-block:: python

    if response.status_code ==  requests.codes.ok:
        # parse the return
        my_data = response.json()
        ...
    else:
        print(f"Failed with return code {response.status_code}: {response.json().get('reason', 'No reason found!')}")



POSTing data
------------

On the server side, OpenL2M(ie. Django) parses both "*application/json*" and "*application/x-www-form-urlencoded*" POST requests.
We use the "request.data" dictionary object for this, as explained in https://www.django-rest-framework.org/api-guide/parsers/

This means that your client side script can send POST data with either format.
This is shown in the two Python examples below.

Note that the Python 'requests' object automatically selects the content encoding based on the parameter given (e.g. data vs. json)
So the two examples only differ on that field!

Here is an example with 'x-www-form-urlencoded' POST format, to set an interface description.

.. code-block:: python

    import requests

    headers = {
        "Authorization": f"Token <your token here>",
    }
    form_data = {
        'description': "<your description>",
    }
    try:
        response = requests.post(url=<api url>, data=form_data, headers=headers)
    except  Exception as err:
        # handle error
    # parse response as needed, eg. look for response.status == 200, etc.


This is the equivalent 'application/json' POST format:

.. code-block:: python

    import requests

    headers = {
        "Authorization": f"Token <your token here>",
    }
    json_data = {
        'description': "<your description>",
    }
    try:
        response = requests.post(url=<api url>, json=json_data, headers=headers)
    except  Exception as err:
        # handle error
    # parse response as needed, eg. look for response.status == 200, etc.


