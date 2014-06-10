class Http302(Exception):
    """
    Error class which can be raised from within a handler to cause an
    early bailout and redirect at the middleware level.
    """
    status_code = 302

    def __init__(self, location, message=None):
        self.location = location
        self.message = message


class NotFound(Exception):
    """ Generic error to replace all "Not Found"-type API errors. """
    status_code = 404


class NotAuthenticated(Exception):
    """
    Raised when a user is trying to make requests and they are not logged in.

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthenticated`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    status_code = 403


class PermissionDeniedException(Exception):
    """
    Raised when a user does not have right to request an action or resource.
    """
    status_code = 403


class NotAuthorized(Exception):
    """
    Raised whenever a user attempts to access a resource which they do not
    have role-based access to (such as when failing the
    :func:`~horizon.decorators.require_roles` decorator).

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthorized`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    status_code = 401


class ServiceCatalogException(Exception):
    """
    Raised when a requested service is not available in the ``ServiceCatalog``
    returned by Keystone.
    """

    def __init__(self, service_name):
        message = 'Invalid service catalog service: %s' % service_name
        super(ServiceCatalogException, self).__init__(message)


class MediaFolderNotExistException(Exception):
    message = "Media Folder was not exist"

from keystoneclient.exceptions import (Unauthorized as keystone_Unauthorized,
                                       LicenseForbidden as
                                       keystone_LicenseForbidden)
from cinderclient.exceptions import (Unauthorized as cinder_Unauthorized,
                                     LicenseForbidden as
                                     cinder_LicenseForbidden)
from novaclient.exceptions import (Unauthorized as nova_Unauthorized,
                                   LicenseForbidden as nova_LicenseForbidden)
from quantumclient.common.exceptions import (Unauthorized as
                                             quantum_Unauthorized,
                                             LicenseForbidden as
                                             quantum_LicenseForbidden)
from glanceclient.exc import (Unauthorized as glance_Unauthorized,
                              LicenseForbidden as glance_LicenseForbidden)
# swiftclient use keystoneclient exception

Unauthorized = (keystone_Unauthorized,
                nova_Unauthorized,
                cinder_Unauthorized,
                quantum_Unauthorized,
                glance_Unauthorized)

LicenseForbidden = (keystone_LicenseForbidden,
                    cinder_LicenseForbidden,
                    nova_LicenseForbidden,
                    quantum_LicenseForbidden,
                    glance_LicenseForbidden,)
