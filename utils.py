#!/usr/bin/env python

################################################################################
#
#          util.py - Supporting routines for the experiment scripts
#
################################################################################

import os
import shlex
import shutil
import subprocess

def check_binaries(required_binaries):
    for p in required_binaries:
        if not shutil.which(p):
            raise Exception(f"required command {p} not found")

def prompt_key(auto, opnum, optotal, prompt):
    if auto:
        print(f"\n({opnum} / {optotal}): {prompt}")
        return opnum + 1
    inp = False
    while inp != "":
        try:
            inp = input(f"\n({opnum} / {optotal}): {prompt} -- press any key to continue")
            return opnum + 1
        except Exception:
            pass

def display_command(cmd):
    print(f"[{os.getcwd()}] $ {cmd}")

def run_command(cmd, expected_retcode):
    retcode = subprocess.call(shlex.split(cmd))
    if retcode != expected_retcode:
        raise Exception(f"Expected {expected_retcode} from process but it exited with {retcode}.")
