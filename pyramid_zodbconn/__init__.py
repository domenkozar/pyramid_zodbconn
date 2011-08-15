from pyramid_zodbconn.uri import db_from_uri
from pyramid.exceptions import ConfigurationError

def get_connection(request):
    # not a tween.  rationale: tweens don't get called until the router accepts
    # a request.  during paster shell, paster ptweens, etc, the router is
    # never invoked
    registry = request.registry
    zodb_conn = getattr(request, '_zodb_conn', None)
    if zodb_conn is None:
        zodb_db = getattr(registry, 'zodb_database', None)
        if zodb_db is None:
            raise ConfigurationError(
                'pyramid_zodbconn not included in configuration or no '
                'zodbconn.uri defined in Pyramid application settings')
        zodb_conn = request._zodb_conn = zodb_db.open()
        def finished(request):
            del request._zodb_conn
            zodb_conn.transaction_manager.abort()
            zodb_conn.close()
        request.add_finished_callback(finished)
    return zodb_conn

def includeme(config, db_from_uri=db_from_uri):
    """
    Set up am implicit :term:`tween` to make a ZODB connection available
    to your Pyramid application.

    This includeme recognizes a ``zodbconn.uri`` setting in your deployment
    settings::

        zodbconn.uri: The database URI or URIs (either a whitespace-delimited
        string, a carriage-return-delimed string or a list of strings).  

    This tween configured to be placed 'above' the 'tm' tween.
    """
    uri = config.registry.settings.get('zodbconn.uri')
    if uri is None:
        config.registry.zodb_database = None
    else:
        db = db_from_uri(uri)
        config.registry.zodb_database = db