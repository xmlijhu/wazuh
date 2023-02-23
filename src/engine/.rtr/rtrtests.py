#!/usr/bin/python3

# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2


import subprocess
import logging
import os

BUILDDIR = '/build'
THREADS_DEFAULT = 2
DOXYGEN_TARGET = 'doc_doxygen'

def log(outputdir, module, stdout, stderr):
    with open(outputdir + f'/{module}.stdout.log', 'w') as f:
        f.write(stdout.decode('utf-8'))
    with open(outputdir + f'/{module}.stderr.log', 'w') as f:
        f.write(stderr.decode('utf-8'))

def cppcheck(params):
    command = 'cppcheck'
    # Creating folder for cppcheck build
    os.makedirs(os.path.join(params.output, 'build', 'cppcheck-build'), exist_ok=True)
    args = f'--error-exitcode=1 --force {params.source}'
    args += f' --std=c++17 --enable=warning,style,performance,portability,unusedFunction --suppress=constParameterCallback '
    args += f' --cppcheck-build-dir={params.output}{BUILDDIR}/cppcheck-build '
    if params.ignore:
        abs_ignore = [os.path.join(params.source, path)
                      for path in params.ignore]
        args += f'-i {" -i ".join(abs_ignore)}'
    logging.debug(f'Executing {command} {args}')
    result = subprocess.run(
        f'{command} {args}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode == 0 and not result.stderr:
        logging.info('CPPCHECK: successful')
    else:
        logging.info('CPPCHECK: fail')
        # TODO: we force the return code to 0 to allow the tool to continue
        result.returncode = 0
    log(params.output, 'cppcheck', result.stdout, result.stderr)
    return bool(not result.returncode)


def clangformat(params):
    file_extensions = ["*.cpp", "*.hpp"]
    find_extensions = f'-iname {" -o -iname ".join(file_extensions)}'
    if params.ignore:
        abs_ignore = [os.path.join(params.source, path)
                      for path in params.ignore]
        find_ignoredir = f'-path {" -o -path ".join(abs_ignore)}'
    find_cmd = f'find {params.source} -type f \( {find_extensions} \) -print -o \( {find_ignoredir} \) -prune'
    clangformat_dry_cmd = 'clang-format --dry-run -style=file -i'
    clangformat_cmd = 'clang-format -style=file -i'
    logging.debug(f'Executing {find_cmd} | xargs {clangformat_dry_cmd}')
    result = subprocess.run(f'{find_cmd} | xargs {clangformat_dry_cmd}',
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if not result.stderr and not result.stdout:
        logging.info('CLANG-FORMAT: successful')
    else:
        logging.info('CLANG-FORMAT: dry run fails.')
        # TODO: we force the return code to 0 to allow the tool to continue
        result.returncode = 0
    log(params.output, 'clangformat', result.stdout, result.stderr)
    return bool(not result.returncode)


def unittests(params):
    command = 'ctest'
    builddir = params.output + BUILDDIR
    args = f'--test-dir {builddir} --output-on-failure'
    logging.debug(f'Executing {command} {args}')
    # Creating directory tree for tests
    os.makedirs('/var/ossec', exist_ok=True)
    os.makedirs('/var/ossec/queue', exist_ok=True)
    os.makedirs('/var/ossec/queue/db', exist_ok=True)
    os.makedirs('/var/ossec/queue/alerts', exist_ok=True)

    result = subprocess.run(
        f'{command} {args}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode == 0 and not result.stderr:
        logging.info('TESTING: successful')
    else:
        logging.info('TESTING: fail')
    log(params.output, 'unittests', result.stdout, result.stderr)
    return bool(not result.returncode)


def configure(builddir, sourcedir):
    args = f'-B {builddir} -S {sourcedir}'
    command = 'cmake'
    logging.debug(f'Executing {command} {args}')
    result = subprocess.run(
        f'{command} {args}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    log(builddir, 'configure', result.stdout, result.stderr)
    return bool(not result.returncode)


def build(params):
    builddir = params.output + BUILDDIR
    #Adding safe directory in case the user running the command is not root
    subprocess.run(f"git config --global --add safe.directory '*'", shell=True)
    if configure(builddir, params.source):
        command = 'cmake'
        args = f'--build {builddir} -j{THREADS_DEFAULT}'
        logging.debug(f'Executing {command} {args}')
        result = subprocess.run(
            f'{command} {args}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if result.returncode == 0 and not result.stderr:
            logging.info('BUILDING: successful')
        else:
            logging.info('BUILDING: fail')
        log(params.output, 'build', result.stdout, result.stderr)
        return bool(not result.returncode)
    else:
        return False

def docs(params):
    command = 'make'
    args = f'-C {params.output}{BUILDDIR} {DOXYGEN_TARGET} -j{THREADS_DEFAULT}'
    logging.debug(f'Executing {command} {args}')
    result = subprocess.run(
        f'{command} {args}', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=params.output)
    if result.returncode == 0 and not result.stderr:
        logging.info('DOXYGEN GENERATION: successful')
    else:
        logging.info('DOXYGEN GENERATION: fail')
        # Forcing the return code to 1 in case of any message in stderr
        result.returncode = 1
    log(params.output, 'docs', result.stdout, result.stderr)
    return bool(not result.returncode)