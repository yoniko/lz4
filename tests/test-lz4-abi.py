#!/usr/bin/env python3
"""Test LZ4 interoperability between versions"""

#
# Copyright (C) 2011-present, Takayuki Matsuoka
# All rights reserved.
# GPL v2 License
#

import glob
import subprocess
import filecmp
import os
import shutil
import sys
import hashlib

repo_url = 'https://github.com/lz4/lz4.git'
tmp_dir_name = 'tests/abiTest'
env_flags = ' ' # '-j MOREFLAGS="-g -O0 -fsanitize=address"'
make_cmd = 'make'
git_cmd = 'git'
test_dat_src = 'README.md'
test_dat = 'test_dat'
head = 'v999'

def proc(cmd_args, pipe=True, dummy=False):
    if dummy:
        return
    if pipe:
        subproc = subprocess.Popen(cmd_args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    else:
        subproc = subprocess.Popen(cmd_args)
    return subproc.communicate()

def make(args, pipe=True):
    return proc([make_cmd] + args, pipe)

def git(args, pipe=True):
    return proc([git_cmd] + args, pipe)

def get_git_tags():
    stdout, stderr = git(['tag', '-l', 'r[0-9][0-9][0-9]'])
    tags = stdout.decode('utf-8').split()
    stdout, stderr = git(['tag', '-l', 'v[1-9].[0-9].[0-9]'])
    tags += stdout.decode('utf-8').split()
    return tags

# https://stackoverflow.com/a/19711609/2132223
def sha1_of_file(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

if __name__ == '__main__':
    error_code = 0
    base_dir = os.getcwd() + '/..'           # /path/to/lz4
    tmp_dir = base_dir + '/' + tmp_dir_name  # /path/to/lz4/tests/versionsTest
    clone_dir = tmp_dir + '/' + 'lz4'        # /path/to/lz4/tests/versionsTest/lz4
    lib_dir = base_dir + '/lib'              # /path/to/lz4/lib
    os.makedirs(tmp_dir, exist_ok=True)

    # since Travis clones limited depth, we should clone full repository
    if not os.path.isdir(clone_dir):
        git(['clone', repo_url, clone_dir])

    shutil.copy2(base_dir + '/' + test_dat_src, tmp_dir + '/' + test_dat)

    # Retrieve all release tags
    print('Retrieve all release tags :')
    os.chdir(clone_dir)
    tags = [head] + get_git_tags()
    print(tags);

    # Build all versions of liblz4
    # note : naming scheme only works on Linux
    for tag in tags:
        print('tag = ', tag)
        os.chdir(base_dir)
        dst_liblz4 = '{}/liblz4.so.{}'.format(tmp_dir, tag) # /path/to/lz4/test/lz4test/lz4c.<TAG>
        print('dst_liblz4 = ', dst_liblz4)
        if not os.path.isfile(dst_liblz4) or tag == head:
            if tag != head:
                r_dir = '{}/{}'.format(tmp_dir, tag)  # /path/to/lz4/test/lz4test/<TAG>
                print('r_dir = ', r_dir)
                os.makedirs(r_dir, exist_ok=True)
                os.chdir(clone_dir)
                git(['--work-tree=' + r_dir, 'checkout', tag, '--', '.'], False)
                os.chdir(r_dir + '/lib')  # /path/to/lz4/lz4test/<TAG>/lib
            else:
                print('lib_dir = {}', lib_dir)
                os.chdir(lib_dir)
            make(['clean', 'liblz4'], False)
            for bin in glob.glob("liblz4.*"):
                shutil.copy2(bin, dst_liblz4)

    os.chdir(tmp_dir)
    for lz4 in glob.glob("*.lz4"):
        os.remove(lz4)

    print('Compress test.dat expecting current ABI but linking to older Dynamic Library version')

#    for tag in tags:
#        proc(['./lz4c.'   + tag, '-1fz', test_dat, test_dat + '_1_64_' + tag + '.lz4'])

    print('Compress test.dat using current Dynamic Library expecting older ABI version')

#    for tag in tags:
#        proc(['./lz4c.'   + tag, '-1fz', test_dat, test_dat + '_1_64_' + tag + '.lz4'])

    # Decompress files, ensure they are readable
    # TBD

    # Compare all '.dec' files with test_dat
    decs = glob.glob('*.dec')
    for dec in decs:
        if not filecmp.cmp(dec, test_dat):
            print('ERR : ' + dec)
            error_code = 1
        else:
            print('OK  : ' + dec)
            os.remove(dec)

    if error_code != 0:
        print('ERROR')

    sys.exit(error_code)
