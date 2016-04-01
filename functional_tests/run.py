#!/usr/bin/env python

import os.path
import sys
import pytest

if __name__ == '__main__':
    d = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(d)
    sys.path.append(os.path.join(os.path.dirname(d), 'cadasta'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
    sys.exit(pytest.main())
