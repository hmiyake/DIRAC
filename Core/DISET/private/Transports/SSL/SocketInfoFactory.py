# $Header: /tmp/libdirac/tmp.stZoy15380/dirac/DIRAC3/DIRAC/Core/DISET/private/Transports/SSL/SocketInfoFactory.py,v 1.11 2008/07/07 16:37:19 acasajus Exp $
__RCSID__ = "$Id: SocketInfoFactory.py,v 1.11 2008/07/07 16:37:19 acasajus Exp $"

import socket
import GSI
from DIRAC.Core.Utilities.ReturnValues import S_ERROR, S_OK
from DIRAC.Core.DISET.private.Transports.SSL.SocketInfo import SocketInfo
from DIRAC.Core.DISET.private.Transports.SSL.SessionManager import gSessionManager
from DIRAC.Core.DISET.private.Transports.SSL.FakeSocket import FakeSocket
from DIRAC.Core.DISET.private.Transports.SSL.ThreadSafeSSLObject import ThreadSafeSSLObject

class SocketInfoFactory:

  def generateClientInfo( self, destinationHostname, kwargs ):
    infoDict = { 'clientMode' : True, 'hostname' : destinationHostname }
    for key in kwargs.keys():
      infoDict[ key ] = kwargs[ key ]
    try:
      return S_OK( SocketInfo( infoDict ) )
    except Exception, e:
      return S_ERROR( str( e ) )

  def generateServerInfo( self, kwargs ):
    infoDict = { 'clientMode' : False }
    for key in kwargs.keys():
      infoDict[ key ] = kwargs[ key ]
    try:
      return S_OK( SocketInfo( infoDict ) )
    except Exception, e:
      return S_ERROR( str( e ) )

  def getSocket( self, hostAddress, **kwargs ):
    osSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    retVal = self.generateClientInfo( hostAddress[0], kwargs )
    if not retVal[ 'OK' ]:
      return retVal
    socketInfo = retVal[ 'Value' ]
    sslSocket = GSI.SSL.Connection( socketInfo.getSSLContext(), osSocket )
    #sslSocket = ThreadSafeSSLObject( sslSocket )
    #sslSocket = FakeSocket( sslSocket )
    sessionId = str( hash( str( hostAddress ) + ":".join( socketInfo.getLocalCredentialsLocation() )  ) )
    socketInfo.sslContext.set_session_id( str( hash( sessionId ) ) )
    socketInfo.setSSLSocket( sslSocket )
    if gSessionManager.isValid( sessionId ):
      sslSocket.set_session( gSessionManager.get( sessionId ) )
    sslSocket.connect( hostAddress )
    retVal = socketInfo.doClientHandshake()
    if not retVal[ 'OK' ]:
      return retVal
    gSessionManager.set( sessionId, sslSocket.get_session() )
    return S_OK( socketInfo )

  def getListeningSocket( self, hostAddress, listeningQueueSize = 5, reuseAddress = True, **kwargs ):
    osSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    if reuseAddress:
      osSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    retVal = self.generateServerInfo( kwargs )
    if not retVal[ 'OK' ]:
      return retVal
    socketInfo = retVal[ 'Value' ]
    sslSocket = GSI.SSL.Connection( socketInfo.getSSLContext(), osSocket )
    sslSocket.bind( hostAddress )
    sslSocket.listen( listeningQueueSize )
    socketInfo.setSSLSocket( sslSocket )
    return S_OK( socketInfo )

gSocketInfoFactory = SocketInfoFactory()