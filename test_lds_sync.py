""" This script tests against the following API calls used in IONODES syncing with LDS (as pertaining to EEPD-10648).
User is expected to provide necessary values into yaml config prior to running.
"""

import pytest
import requests

__author__ = "Zack Waits"
__team__ = "QA:Archiver"

# GLOBALS
ENDPOINTS = {"protocol":     "https://",
             "bsd":          "", #branded sub-domain, populates later
             "base":         ".eagleeyenetworks.com",
             "authenticate": "/g/aaa/authenticate",
             "authorize":    "/g/aaa/authorize",
             "layout_list":  "/g/layout/list",
             "layout":       "/g/layout",
             "device_list":  "/g/device/list",
             "device":       "/g/device",
             "device_rtsp":  "/g/device/rtsp"}


# CUSTOM ERRORS
class Error(Exception):
    """Base class for other exceptions"""
    pass


class InvalidModelTypeError(Error):
    """Raised when model str is an invalid key from the yaml load to global VARCONFIG"""
    pass


class EENAuthenticationError(Error):
    """Raised when Authentication responds with non-2xx HTTP response"""
    pass


class EENAuthorizationError(Error):
    """Raised when Authentication responds with non-2xx HTTP response"""
    pass


class GetLayoutsListError(Error):
    """Raised when Layouts API call(s) responds with non-2xx HTTP response"""
    pass


class GetLayoutsError(Error):
    """Raised when Layouts API call(s) responds with non-2xx HTTP response"""
    pass


class GetDeviceListError(Error):
    """Raised when Device List API call(s) responds with non-2xx HTTP response"""
    pass


class GetCameraError(Error):
    """Raised when Camera API call(s) responds with non-2xx HTTP response"""
    pass


class GetCameraRtspError(Error):
    """Raised when Camera RTSP API call(s) responds with non-2xx HTTP response"""
    pass


class CameraRtspEmptyResponseError(Error):
    """Raised when Camera RTSP API call(s) responds with blank/missing information for valid camera ESN"""
    pass


# TESTS
def test_login(load_config, session, model):
    VARCONFIG = load_config
    """Log in with the user credentials for the desired account based on the model provided. 
    User credentials are pulled from yaml config.

    Args:
        SESSION (requests.Session): Session object for HTTP requests against API endpoints
        model (str): Must be a valid "key" from the yaml configuration file

    Raises:
        InvalidModelTypeError: User provided a model not found in the yaml configuration
        EENAuthenticationError: EEN authentication step failed
        EENAuthorizationError: EEN authorization step failed
    """
    # Set parameters for request based on model from yml config
    try:
        test = VARCONFIG["models"][model]
    except KeyError:
        raise InvalidModelTypeError
    params = {"username": VARCONFIG["models"][model]["username"],
              "password": VARCONFIG["models"][model]["password"],}

    # Authenticate
    r = session.post(ENDPOINTS["protocol"]+ "login" + ENDPOINTS["base"] + ENDPOINTS['authenticate'], params=params)
    if r.status_code == 200:
        # Authorize
        params = {"token": r.json()['token']}
        r = session.post(ENDPOINTS["protocol"]+ "login" + ENDPOINTS["base"] + ENDPOINTS['authorize'], params=params)
        if r.status_code == 200:
            # Update global with 'active_brand_subdomain' value from successful authorize response.
            ENDPOINTS['bsd'] = r.json()['active_brand_subdomain']
        else:
            raise EENAuthorizationError
    else:
        raise EENAuthenticationError
    assert r.status_code == 200

def test_get_layouts(session, model):
    """Test pulling list of layouts from API. Grab up to the first 5.

    Args:
        SESSION (requests.Session): Session object for HTTP requests against API endpoints
        model (str): Must be a valid "key" from the yaml configuration file

    Raises:
        InvalidModelTypeError: User provided a model not found in the yaml configuration
    """
    layout_ids = []
    r=session.get(ENDPOINTS["protocol"]+ ENDPOINTS['bsd'] + ENDPOINTS["base"] + ENDPOINTS['layout_list'])
    if r.status_code == 200:
        # Get up to the first 5 layouts
        print("jsonresponse: "+r.text)
        if len(r.json()) >= 5:
            for l in r.json():
                if(len(layout_ids) < 5):
                    layout_ids.append(l[0])
        else:
            for l in r.json():
                layout_ids.append(l[0])
        # Confirm successful response of layout endpoint for each of the 5
        for id in layout_ids:
            params = {"id": id}
            r=session.get(ENDPOINTS["protocol"]+ ENDPOINTS['bsd'] + ENDPOINTS["base"] + ENDPOINTS['layout'], params=params)
            if r.status_code != 200:
                raise GetLayoutsError
    else:
        raise GetLayoutsListError
    assert r.status_code == 200

def test_get_cameras_and_rtsp(session):
    """Tests against the cameras and rtsp API endpoints confirming each responds with 200. Additionally confirms the content response from RTSP endpoint is not null/"".

    Args:
        SESSION (requests.Session): Session object for HTTP requests against API endpoints

    Raises:
        GetCameraError: Camera endpoint responded with non-2xx 
        CameraRtspEmptyResponseError: Camera RTSP endpoint content was blank/empty
        GetCameraRtspError: Camera RTSP endpoint responded with non-2xx
        GetDeviceListError: Device List endpoint responded with non-2xx
    """
    camera_ids = []
    r = session.get(ENDPOINTS["protocol"]+ ENDPOINTS['bsd'] + ENDPOINTS["base"] + ENDPOINTS['device_list'])
    if r.status_code == 200:
        for device in r.json():
            if device[3] == "camera":
                if len(camera_ids) < 32:
                    camera_ids.append(device[1])
        for id in camera_ids:
            params = {"id": id}
            r = session.get(ENDPOINTS["protocol"]+ ENDPOINTS['bsd'] + ENDPOINTS["base"] + ENDPOINTS['device'], params=params)
            re = session.get(ENDPOINTS["protocol"]+ ENDPOINTS['bsd'] + ENDPOINTS["base"] + ENDPOINTS['device_rtsp'], params=params)
            if r.status_code != 200:
                raise GetCameraError
            if re.status_code == 200:
                if re.json()["preview_url"] == "" or \
                     re.json()["video_url"] == "":
                        raise CameraRtspEmptyResponseError
            else:
                raise GetCameraRtspError
    else:
        raise GetDeviceListError
    assert re.status_code == 200