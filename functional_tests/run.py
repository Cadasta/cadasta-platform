#!/usr/bin/env python

import os.path
import sys
import pytest
from subprocess import Popen, DEVNULL


if __name__ == '__main__':
    d = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(d)
    sys.path.append(os.path.join(os.path.dirname(d), 'cadasta'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
    xvfb = Popen(["Xvfb", ":1"], stdout=DEVNULL, stderr=DEVNULL)
    os.environ['DISPLAY'] = ':1'
    result = pytest.main()
    xvfb.terminate()
    sys.exit(result)
