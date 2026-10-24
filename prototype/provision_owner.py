#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Offline-review helper. Never run against a device before TLS and rollback gates."""
import argparse
import base64
import getpass
import hashlib
import json
import os
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,help='Explicit path for a new 0600 verifier file')
    args=parser.parse_args()
    if os.path.exists(args.output):
        parser.error('Refusing to overwrite an existing credential')
    password=getpass.getpass('New local owner password: ')
    confirm=getpass.getpass('Repeat password: ')
    if password != confirm or len(password) < 16:
        parser.error('Passwords differ or are shorter than 16 characters')
    salt=os.urandom(32)
    verifier=hashlib.pbkdf2_hmac('sha256',password,salt,200000)
    data={'algorithm':'pbkdf2-sha256','iterations':200000,
          'salt':base64.b64encode(salt),'verifier':base64.b64encode(verifier)}
    old=os.umask(0077)
    try:
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0600)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(data,stream)
        except:
            os.unlink(args.output)
            raise
    finally:
        os.umask(old)
    print('Local owner verifier created at the requested path; no password printed.')

if __name__ == '__main__':
    main()
