########################################################################
# $HeadURL $
# File: ReTransfer.py
# Author: Krzysztof.Ciba@NOSPAMgmail.com
# Date: 2013/04/02 14:24:21
########################################################################
""" :mod: ReTransfer

    ================


    .. module: ReTransfer

    :synopsis: ReTransfer Operation handler

    .. moduleauthor:: Krzysztof.Ciba@NOSPAMgmail.com

    ReTransfer Operation handler
"""

__RCSID__ = "$Id $"

# #
# @file ReTransfer.py
# @author Krzysztof.Ciba@NOSPAMgmail.com
# @date 2013/04/02 14:24:31
# @brief Definition of ReTransfer class.

# # imports
from DIRAC import S_OK, S_ERROR
from DIRAC.FrameworkSystem.Client.MonitoringClient import gMonitor
from DIRAC.DataManagementSystem.Agent.RequestOperations.DMSRequestOperationsBase import DMSRequestOperationsBase
from DIRAC.Resources.Storage.StorageElement import StorageElement

from DIRAC.MonitoringSystem.Client.MonitoringReporter import MonitoringReporter
from DIRAC.Core.Utilities import Time, Network

########################################################################


class ReTransfer(DMSRequestOperationsBase):
  """
  .. class:: ReTransfer


  online ReTransfer operation handler

  :param self: self reference
  :param ~DIRAC.RequestManagementSystem.Client.Operation.Operation operation: Operation instance
  :param str csPath: CS path for this handler

  """

  def __init__(self, operation=None, csPath=None):
    """c'tor

    """
    # # base class ctor
    DMSRequestOperationsBase.__init__(self, operation, csPath)

  def __call__(self):
    """ reTransfer operation execution """

    # Check whether the ES flag is enabled so we can send the data accordingly.
    if self.rmsMonitoring:
      self.rmsMonitoringReporter = MonitoringReporter(monitoringType="RMSMonitoring")
    else:
      # # gMonitor stuff
      gMonitor.registerActivity("FileReTransferAtt", "File retransfers attempted",
                                "RequestExecutingAgent", "Files/min", gMonitor.OP_SUM)
      gMonitor.registerActivity("FileReTransferOK", "File retransfers successful",
                                "RequestExecutingAgent", "Files/min", gMonitor.OP_SUM)
      gMonitor.registerActivity("FileReTransferFail", "File retransfers failed",
                                "RequestExecutingAgent", "Files/min", gMonitor.OP_SUM)

    # # list of targetSEs
    targetSEs = self.operation.targetSEList
    # # check targetSEs for removal
    targetSE = targetSEs[0]
    bannedTargets = self.checkSEsRSS(targetSE)
    if not bannedTargets['OK']:
      if self.rmsMonitoring:
        for status in ["Attempted", "Failed"]:
          self.rmsMonitoringReporter.addRecord({
              "timestamp": int(Time.toEpoch()),
              "host": Network.getFQDN(),
              "objectType": "File",
              "operationType": self.operation.Type,
              "parentID": self.operation.OperationID,
              "status": status,
              "nbObject": len(self.operation)
          })
        self.rmsMonitoringReporter.commit()
      else:
        gMonitor.addMark("FileReTransferAtt")
        gMonitor.addMark("FileReTransferFail")
      return bannedTargets

    if bannedTargets['Value']:
      return S_OK("%s targets are banned for writing" % ",".join(bannedTargets['Value']))

    # # get waiting files
    waitingFiles = self.getWaitingFilesList()
    # # prepare waiting files
    toRetransfer = dict([(opFile.PFN, opFile) for opFile in waitingFiles])

    if self.rmsMonitoring:
      self.rmsMonitoringReporter.addRecord({
          "timestamp": int(Time.toEpoch()),
          "host": Network.getFQDN(),
          "objectType": "File",
          "operationType": self.operation.Type,
          "parentID": self.operation.OperationID,
          "status": "Attempted",
          "nbObject": len(toRetransfer)
      })
    else:
      gMonitor.addMark("FileReTransferAtt", len(toRetransfer))

    if len(targetSEs) != 1:
      error = "only one TargetSE allowed, got %d" % len(targetSEs)
      for opFile in toRetransfer.values():
        opFile.Error = error
        opFile.Status = "Failed"
      self.operation.Error = error

      if self.rmsMonitoring:
        self.rmsMonitoringReporter.addRecord({
            "timestamp": int(Time.toEpoch()),
            "host": Network.getFQDN(),
            "objectType": "File",
            "operationType": self.operation.Type,
            "parentID": self.operation.OperationID,
            "status": "Failed",
            "nbObject": len(toRetransfer)
        })
        self.rmsMonitoringReporter.commit()
      else:
        gMonitor.addMark("FileReTransferFail", len(toRetransfer))

      return S_ERROR(error)

    se = StorageElement(targetSE)
    for opFile in toRetransfer.values():

      reTransfer = se.retransferOnlineFile(opFile.LFN)
      if not reTransfer["OK"]:
        opFile.Error = reTransfer["Message"]
        self.log.error("Retransfer failed", opFile.Error)

        if self.rmsMonitoring:
          self.rmsMonitoringReporter.addRecord({
              "timestamp": int(Time.toEpoch()),
              "host": Network.getFQDN(),
              "objectType": "File",
              "operationType": self.operation.Type,
              "parentID": self.operation.OperationID,
              "status": "Failed",
              "nbObject": 1
          })
        else:
          gMonitor.addMark("FileReTransferFail", 1)

        continue
      reTransfer = reTransfer["Value"]
      if opFile.LFN in reTransfer["Failed"]:
        opFile.Error = reTransfer["Failed"][opFile.LFN]
        self.log.error("Retransfer failed", opFile.Error)

        if self.rmsMonitoring:
          self.rmsMonitoringReporter.addRecord({
              "timestamp": int(Time.toEpoch()),
              "host": Network.getFQDN(),
              "objectType": "File",
              "operationType": self.operation.Type,
              "parentID": self.operation.OperationID,
              "status": "Failed",
              "nbObject": 1
          })
        else:
          gMonitor.addMark("FileReTransferFail", 1)

        continue
      opFile.Status = "Done"
      self.log.info("%s retransfer done" % opFile.LFN)

      if self.rmsMonitoring:
        self.rmsMonitoringReporter.addRecord({
            "timestamp": int(Time.toEpoch()),
            "host": Network.getFQDN(),
            "objectType": "File",
            "operationType": self.operation.Type,
            "parentID": self.operation.OperationID,
            "status": "Successful",
            "nbObject": 1
        })
      else:
        gMonitor.addMark("FileReTransferOK", 1)

    if self.rmsMonitoring:
      self.rmsMonitoringReporter.commit()

    return S_OK()
