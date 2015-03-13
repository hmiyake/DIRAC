########################################################################
# $HeadURL$
########################################################################

""" BaseDB is the base class for multiple DIRAC databases. It uniforms the
    way how the database objects are constructed
"""

__RCSID__ = "$Id$"

import sys, types
from DIRAC                           import gLogger, gConfig, S_OK
from DIRAC.Core.Utilities.MySQL      import MySQL
from DIRAC.ConfigurationSystem.Client.Utilities import getDBParameters


########################################################################
class DB( MySQL ):

  def __init__( self, dbname, fullname, maxQueueSize, debug = False ):

    database_name = dbname
    self.log = gLogger.getSubLogger( database_name )

    result = getDBParameters( fullname, defaultQueueSize = maxQueueSize )
    if( not result[ 'OK' ] ):
      raise Exception \
                  ( 'Cannot get the Database parameters' % result( 'Message' ) )
    self.dbHost, \
      self.dbPort, \
      self.dbUser, \
      self.dbPass, \
      self.dbName, \
      self.maxQueueSize = result[ 'Value' ]

    MySQL.__init__( self, self.dbHost, self.dbUser, self.dbPass,
                   self.dbName, self.dbPort, maxQueueSize = maxQueueSize, debug = debug )

    if not self._connected:
      raise RuntimeError( 'Can not connect to DB %s, exiting...' % self.dbName )


    self.log.info( "==================================================" )
    #self.log.info("SystemInstance: "+self.system)
    self.log.info( "User:           " + self.dbUser )
    self.log.info( "Host:           " + self.dbHost )
    self.log.info( "Port:           " + str( self.dbPort ) )
    #self.log.info("Password:       "+self.dbPass)
    self.log.info( "DBName:         " + self.dbName )
    self.log.info( "MaxQueue:       " + str( self.maxQueueSize ) )
    self.log.info( "==================================================" )

#############################################################################
  def getCSOption( self, optionName, defaultValue = None ):
    return gConfig.getValue( "/%s/%s" % ( self.cs_path, optionName ), defaultValue )
