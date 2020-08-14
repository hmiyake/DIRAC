#!/usr/bin/env python

from __future__ import print_function

__RCSID__ = "$Id$"

import os

from DIRAC import exit as DIRACExit
from DIRAC.Core.Base import Script

Script.setUsageMessage("""
Get the given file replica metadata from the File Catalog

Usage:
   %s <LFN | fileContainingLFNs> SE
""" % Script.scriptName)

Script.parseCommandLine()

from DIRAC import gLogger
from DIRAC.DataManagementSystem.Client.DataManager import DataManager

args = Script.getPositionalArgs()
if not len(args) == 2:
  Script.showHelp(exitCode=1)
else:
  inputFileName = args[0]
  storageElement = args[1]

if os.path.exists(inputFileName):
  inputFile = open(inputFileName, 'r')
  string = inputFile.read()
  lfns = [lfn.strip() for lfn in string.splitlines()]
  inputFile.close()
else:
  lfns = [inputFileName]

res = DataManager().getReplicaMetadata(lfns, storageElement)
if not res['OK']:
  print('Error:', res['Message'])
  DIRACExit(1)

print('%s %s %s %s' % ('File'.ljust(100), 'Migrated'.ljust(8), 'Cached'.ljust(8), 'Size (bytes)'.ljust(10)))
for lfn, metadata in res['Value']['Successful'].items():
  print(
      '%s %s %s %s' %
      (lfn.ljust(100), str(
          metadata['Migrated']).ljust(8), str(
          metadata.get(
              'Cached', metadata['Accessible'])).ljust(8), str(
          metadata['Size']).ljust(10)))
for lfn, reason in res['Value']['Failed'].items():
  print('%s %s' % (lfn.ljust(100), reason.ljust(8)))
