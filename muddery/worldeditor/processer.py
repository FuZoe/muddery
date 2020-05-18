"""
Decorators of web service controllers.

This decorator can add controllers to the controller dict for future usage.
"""

import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from evennia.utils import logger
from muddery.utils.exception import MudderyError, ERR
from muddery.mappings.request_set import REQUEST_SET
import muddery.worlddata.controllers
from muddery.worlddata.utils.response import error_response


class Processer(object):
    """
    HTTP request processer.
    """
    def __init__(self, path_prefix=None):
        if path_prefix:
            if path_prefix[0] != "/":
                path_prefix = "/" + path_prefix

        self.path_prefix = path_prefix

    @csrf_exempt
    def process(self, request):
        """
        Process a request by the func key.
        
        Args:
            request: HTTP request.
        """
        if request.method == "OPTIONS":
            return HttpResponse()
            
        path = request.path_info
        if self.path_prefix:
            if path.find(self.path_prefix) == 0:
                path = path[len(self.path_prefix):]

        data = {}
        func = ""
        args = {}

        if request.POST:
            data = request.POST.dict()
            print("data: %s" % data)
            func = data.get("func", "")
            args_text = data.get("args", None)
            if args_text:
                args = json.loads(args_text)

        if not data:
            try:
                data = json.loads(request.body)
                func = data.get("func", "")
                args = data.get("args", {})
            except Exception as e:
                logger.log_errmsg("Parse request body error: %s" % e)
                pass

        print("request: '%s' '%s' '%s'" % (path, func, args))

        processor = REQUEST_SET.get(path, func)
        if not processor:
            logger.log_errmsg("Can not find API: %s %s" % (path, func))
            return error_response(ERR.no_api, msg="Can not find API: %s %s" % (path, func))

        # check authentication
        if processor.login and not request.user.is_authenticated:
            logger.log_errmsg("Need authentication.")
            return error_response(ERR.no_authentication, msg="Need authentication.")

        # check staff
        if processor.staff and not request.user.is_staff and not request.user.is_superuser:
            return error_response(ERR.no_permission, msg="No permission.")

        # call function
        try:
            response = processor.func(args, request)
        except MudderyError as e:
            logger.log_errmsg("Error: %s, %s" % (e.code, e))
            response = error_response(e.code, msg=str(e), data=e.data)
        except Exception as e:
            logger.log_tracemsg("Error: %s" % e)
            response = error_response(ERR.internal, msg=str(e))

        return response


PROCESSER = Processer(settings.WORLD_DATA_API_PATH)

