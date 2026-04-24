#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#
"""
Driver that adds basic REST connectibity to the base Connector() class.
This implements base HTTP(s) GET, POST, PUT, and DELETE to other REST API drivers to inherit.
"""

import json
import time

from django.conf import settings
from django.http.request import HttpRequest
import requests

from switches.connect.connector import Connector
from switches.connect.utils import debug_response
from switches.models import Switch, SwitchGroup
from switches.utils import dprint


class RESTConnector(Connector):
    """
    This implements a basic REST interface with HTTP GET, POST, PUT and DELETE functions.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        """Set a few things, and then call the Connector.__init__()"""
        dprint("RESTConnector.__init__()")
        self.headers: dict = {}  # contains HTTP headers for GET/POST
        self.response = None  # full response from request, in case user wants it!
        self.base_url: str = ""  # base URL of REST queries
        self.cookies: dict = {}  # cookies to add to the request
        # call the base connector init:
        super().__init__(request, group, switch)

    def _set_base_url(self, base_url: str):
        """Set the base URL for all REST queries"""
        dprint(f"RESTConnector()._set_base_url() = {base_url}")
        self.base_url = base_url

    def _set_cookies(self, cookies: dict):
        """Set the cookie jar!"""
        dprint(f"RESTConnector()._set_cookies() = {cookies}")
        self.cookies = cookies

    #
    # we use the request library, see https://requests.readthedocs.io/en/latest/api/
    #
    # In generic REST APIs, the following methods are used:
    #
    # GET is used to read various configurations and operational data from the device.
    # Data is returned in the body of the response.
    #
    # POST can only be used to create new objects or attributes, ie when they are NOT SET YET!
    # Data is sent in the body of the request.
    #
    # PUT will update with value, but NOT clear out! (ie you cannot set description="").
    # Data is send in the body of the request.
    # Success will return code 204 - No content.
    # You can repeatedly PUT with the same value!
    #
    # DELETE needs to be used to remove an object. It does NOT take request body data.
    #

    def _get(self, path: str, headers: str = "", cookies: dict = {}, message: str = ""):
        """GET a specific REST endpoint and return JSON response.
        Will return json response or None if error is trapped (most likely because API endpoint does not exist).

        Args:
            path (str) - API path (ie withouth host url)
            headers (dict) - HTTPS headers to override default headers from login.
            cookies (dict) - cookied to add to the request. If not set, will use self.cookies (if set)
            message (str) - debug message added to debug_reponse()

        Note that headers can be passed to the request library as is!

        Returns:
            (json) - json response or None if error is trapped (most likely because API endpoint does not exist).
        """
        dprint("RESTConnector()._get()")

        if not headers:
            # set to default
            headers = self.headers
        if not cookies:
            cookies = self.cookies

        # make the request:
        start_time = time.time()
        self.response = requests.get(
            url=self.base_url + path,
            headers=headers,
            cookies=cookies,
            verify=self.switch.netmiko_profile.verify_hostkey,
            timeout=settings.REST_API_TIMEOUT,
        )
        read_duration = time.time() - start_time
        if not message:
            message = "_GET() Call"
        debug_response(response=self.response, message=message)
        try:
            self.response.raise_for_status()
        except Exception:
            # some error occured (after we had a valid token!), return nothing!
            return None

        self.add_timing(path, 1, read_duration)

        if self.response.status_code == 200:  # valid return!
            return json.loads(self.response.text)
        # likely 204 - Valid return, but No Content
        return None

    def _post(
        self, path: str, params: dict = {}, data: dict = {}, headers: dict = {}, cookies: dict = {}, message: str = ""
    ):
        """POST a specific REST endpoint and return JSON response.
            will raise exception on error

        Args:
            path (str) - API path (ie withouth host url)
            params (dict) - query string parameters, as string or dict if multiple.
            data (dict) - body data as json-encoded dict, if any.
            headers (dict) - HTTPS headers to override default headers from login.
            cookies (dict) - cookied to add to the request. If not set, will use self.cookies (if set)
            message (str) - debug message added to debug_reponse()

        Note that params, data and headers can be passed to the request library as is!

        Returns:
            (bool) - True on success, False otherwize. HTTP status code is in self.response.status_code, if needed.
        """
        dprint("RESTConnector._post()")

        if not headers:
            # set to default
            headers = self.headers
        if not cookies:
            cookies = self.cookies

        self.response = requests.post(
            url=self.base_url + path,
            headers=headers,
            cookies=cookies,
            params=params,
            data=data,
            verify=self.switch.netmiko_profile.verify_hostkey,
            timeout=settings.REST_API_TIMEOUT,
        )
        if not message:
            message = "_POST() Call"
        debug_response(response=self.response, message=message)
        self.response.raise_for_status()

        # no errors:
        if self.response.status_code in (200, 201, 202, 204):
            # valid returns:
            # 200 - Created, with content returned
            # 201 - Created, not content
            # 202 - Batch accepted (no content) - may still eventyally fail the batch of commands.
            # 204 - Processed, no content returned.
            return True

        return False

    def _put(
        self, path: str, params: dict = {}, data: dict = {}, headers: dict = {}, cookies: dict = {}, message: str = ""
    ):
        """PUT a specific REST endpoint and return JSON response.
        will raise exception on error

        Args:
            path (str) - API path (ie withouth host url)
            params (dict) - query string parameters, as string or dict if multiple.
            data (dict) - body data as json-encoded dict, if any.
            headers (dict) - HTTPS headers to override default headers from login.
            cookies (dict) - cookied to add to the request. If not set, will use self.cookies (if set)
            message (str) - debug message added to debug_reponse()

        Note that params, data and headers can be passed to the request library as is!

        Returns:
             data as json dict, or None if empty.
        """
        dprint("RESTConnector.put()")

        if not headers:
            # set to default
            headers = self.headers
        if not cookies:
            cookies = self.cookies

        self.response = requests.put(
            url=self.base_url + path,
            headers=headers,
            cookies=cookies,
            params=params,
            data=data,
            verify=self.switch.netmiko_profile.verify_hostkey,
            timeout=settings.REST_API_TIMEOUT,
        )
        if not message:
            message = "_PUT() Call"
        debug_response(response=self.response, message=message)
        self.response.raise_for_status()

        # no errors
        if self.response.status_code in (200, 204):
            return True
        # Hmm ?
        return False

    def _delete(
        self, path: str, params: dict = {}, data: dict = {}, headers: dict = {}, cookies: dict = {}, message: str = ""
    ):
        """DELETE a specific REST endpoint and return JSON response.
        will raise exception on error

        Args:
            path (str) - API path (ie withouth host url)
            params (dict) - query string parameters, as string or dict if multiple.
            data (dict) - body data as json-encoded dict, if any.
            headers (dict) - HTTPS headers to override default headers from login.
            cookies (dict) - cookied to add to the request. If not set, will use self.cookies (if set)
            message (str) - debug message added to debug_reponse()

        Note that params, data and headers can be passed to the request library as is!

        Returns:
            (bool) - True on success, False on failure. HTTP status code is in self.response.status_code, if needed.
        """
        dprint("RESTConnector.delete()")

        if not headers:
            # set to default
            headers = self.headers
        if not cookies:
            cookies = self.cookies

        self.response = requests.delete(
            url=self.base_url + path,
            headers=headers,
            cookies=cookies,
            params=params,
            data=data,
            verify=self.switch.netmiko_profile.verify_hostkey,
            timeout=settings.REST_API_TIMEOUT,
        )
        if not message:
            message = "_DELETE() Call"
        debug_response(response=self.response, message=message)
        self.response.raise_for_status()

        # no errors
        if self.response.status_code in (200, 204):
            return True
        # Hmm ?
        return False
