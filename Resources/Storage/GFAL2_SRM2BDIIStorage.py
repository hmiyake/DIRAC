#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from DIRAC import gLogger, gConfig, S_OK, S_ERROR
from DIRAC.Resources.Storage.GFAL2_SRM2Storage import GFAL2_SRM2Storage as DIRACGFAL2_SRM2Storage
from DIRAC.Core.Utilities.Grid import ldapsearchBDII

__RCSID__ = "$Id$"

class GFAL2_SRM2BDIIStorage(DIRACGFAL2_SRM2Storage):

  def __init__(self, storageName, parameters):
    """ """
    super(GFAL2_SRM2BDIIStorage, self).__init__(storageName, parameters)
    self.log = gLogger.getSubLogger("GFAL2_SRM2BDIIStorage", True)
    self.log.debug("GFAL2_SRM2BDIIStorage.__init__: Initializing object")
    self.pluginName = 'GFAL2_SRM2BDII'

    self.host = None
    if 'LCG_GFAL_INFOSYS' in os.environ:
      self.host = os.environ['LCG_GFAL_INFOSYS']

    self.attr = ['GlueSATotalOnlineSize', 'GlueSAFreeOnlineSize']
    
  def getOccupancy(self, *parms, **kws):
    sTokenDict={'Total':0, 'Free':0}
          
    filt = "(&(GlueSAAccessControlBaseRule=VO:%s)(GlueChunkKey=GlueSEUniqueID=%s))"  % (self.voName, self.protocolParameters['Host'])
    ret = ldapsearchBDII(filt, self.attr, host = self.host)
    if not ret['OK']:
      return ret
    if len(ret['Value']) > 0:
      if 'attr' in ret['Value'][0]:
        attr = ret['Value'][0]['attr']
        sTokenDict['Total'] = float( attr.get( self.attr[0], 0 ) ) * 1024 * 1024 * 1024
        sTokenDict['Free'] = float( attr.get( self.attr[1], 0 ) ) * 1024 * 1024 * 1024

    return S_OK(sTokenDict)
