import os
import sys

# اضافه کردن مسیر پروژه به sys.path
INTERP = os.path.expanduser("~/virtualenv/ferdowsihosseini/3.9/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from ssl_config import SSLConfig

application = create_app('production')
SSLConfig.init_app(application)
SSLConfig.configure_proxy(application) 