#!/usr/bin/env python

import sys
from os.path import normpath, join, dirname, abspath


machine_file = normpath(join(dirname(abspath(__file__)),
                             '../files/machine-images.csv'))


def read_machine_file():
    amis = {}
    with open(machine_file) as fp:
        for l in fp:
            type, region, ami = l[:-1].split(',')
            amis[type + ':' + region] = ami
    return amis


def write_machine_file(amis):
    with open(machine_file, 'w') as fp:
        for k in sorted(amis.keys()):
            type, region = k.split(':')
            print('{},{},{}'.format(type, region, amis[k]), file=fp)


def get_ami(type, region):
    return read_machine_file().get(type + ':' + region)


def set_ami(type, region, ami):
    amis = read_machine_file()
    amis[type + ':' + region] = ami
    write_machine_file(amis)


def main(argv):
    if len(argv) == 3:
        print(get_ami(argv[1], argv[2]))
    elif len(argv) == 4:
        set_ami(argv[1], argv[2], argv[3])
    else:
        print("""
Usage:

   Get AMI    ami.py <type> <region>
   Save AMI   ami.py <type> <region> <ami>
""")
    sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
