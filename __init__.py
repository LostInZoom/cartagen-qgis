__author__ = 'Guillaume Touya, Justin Berli & Paul Bourcier'
__date__ = '2025-07-01'
__copyright__ = '(C) 2025 by Guillaume Touya, Justin Berli & Paul Bourcier'

import os
from PyQt5.QtGui import QIcon

PLUGIN_ICON = QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'icon.svg'))

def classFactory(iface):
    """
    Load CartAGen4QGIS class from file CartAGen4QGIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .cartagenplugin import CartAGen4QGISPlugin
    return CartAGen4QGISPlugin()