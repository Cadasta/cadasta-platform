#!/usr/bin/env python

import os.path
import json

# S3 bucket for storing secrets.
s3_bucket = 'cadasta-secrets'
s3_folder = 'miscellaneous/'

# S3 bucket.
bucket = None


def set_session(aws=None):
    global bucket
    bucket = aws.resource('s3').Bucket(s3_bucket)


def list():
    return [os.path.basename(o.key)
            for o in bucket.objects.filter(Prefix=s3_folder)
            if o.key.endswith('.json')]


def exists(name=None):
    return name + '.json' in list()


def write(name, val):
    body = json.dumps(val, sort_keys=True, indent=4)
    bucket.put_object(Body=body.encode(),
                      ContentType='application/json',
                      Key=os.path.join(s3_folder, name + '.json'))


def read(name):
    key = os.path.join(s3_folder, name + '.json')
    body = bucket.Object(key).get()['Body'].read()
    return json.loads(body.decode())
