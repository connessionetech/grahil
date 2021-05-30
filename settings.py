'''
This file is part of `Reactivity` 
Copyright 2018 Connessione Technologies

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
"""Global settings for the project"""

import os.path
import sys

from tornado.options import define

define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")

__BASE_PACKAGE__ = "oneadmin"
__MODULES__PACKAGE__ = "modules" 
__MODULES__CONF_PACKAGE__ = "conf"

__ROOT_PATH__ = os.path.dirname(os.path.realpath(sys.argv[0])) 

settings = {}

settings["base_path"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__)
settings["app_configuration"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "configuration.json")
settings["log_configuration"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "logging.json")
settings["users_configuration"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "users.json")
settings["permissions_configuration"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "permissions.json")
settings["scripts_folder"] = os.path.join(__ROOT_PATH__, "scripts")
settings["rules_folder"] = os.path.join(__ROOT_PATH__, "rules")
settings["reports_folder"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "reports")

settings["cookie_secret"] = "6Lf0itAlZvRKe24eQpCOFrJu4"
settings["login_url"] = "/login"
settings["static_folder"] = "static"
settings["static_path"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, settings["static_folder"])
settings["template_path"] = os.path.join(os.path.dirname(__file__), __BASE_PACKAGE__, "templates")
settings["xsrf_cookies"] = False
