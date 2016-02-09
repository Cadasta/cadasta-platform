#!/usr/bin/env python

import boto3
import os, os.path, sys, time
import subprocess as sp
import functools, operator
from string import Template


def create_vpc(name):
