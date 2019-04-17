from DIRAC import gLogger, gConfig
from DIRAC import S_OK, S_ERROR

import errno
import json
import gfal2

class spaceTokenOccupancy(object):
  def getOccupancy(self, sePlugin):
    """ Gets the GFAL2_SRM2Storage occupancy info.

      TODO: needs gfal2.15 because of bugs:
      https://its.cern.ch/jira/browse/DMC-979
      https://its.cern.ch/jira/browse/DMC-977

      It queries the srm interface for a given space token.
      Out of the results, we keep totalsize, guaranteedsize, and unusedsize all in MB.
    """

    # Gfal2 extended parameter name to query the space token occupancy
    spaceTokenAttr = 'spacetoken.description?%s' % sePlugin.protocolParameters['SpaceToken']
    # gfal2 can take any srm url as a base.
    spaceTokenEndpoint = sePlugin.getURLBase(withWSUrl=True)['Value']
    try:
      occupancyStr = sePlugin.ctx.getxattr(spaceTokenEndpoint, spaceTokenAttr)
      try:
        occupancyDict = json.loads(occupancyStr)[0]
      except ValueError:
        # https://its.cern.ch/jira/browse/DMC-977
        # a closing bracket is missing, so we retry after adding it
        occupancyStr = occupancyStr[:-1] + '}]'
        occupancyDict = json.loads(occupancyStr)[0]

        # https://its.cern.ch/jira/browse/DMC-979
        # We set totalsize to guaranteed size
        # (it is anyway true for all the SEs I could test)
        occupancyDict['totalsize'] = occupancyDict.get('guaranteedsize', 0)

    except (gfal2.GError, ValueError) as e:
      errStr = 'Something went wrong while checking for spacetoken occupancy.'
      #self.log.verbose(errStr, e.message)
      return S_ERROR(getattr(e, 'code', errno.EINVAL), "%s %s" % (errStr, repr(e)))

    sTokenDict = {}

    sTokenDict['Total'] = float(occupancyDict.get('totalsize', '0')) / 1e6
    sTokenDict['Free'] = float(occupancyDict.get('unusedsize', '0')) / 1e6

    return S_OK(sTokenDict)
    
