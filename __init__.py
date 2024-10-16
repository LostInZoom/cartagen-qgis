__author__ = 'Guillaume Touya, Justin Berli & Paul Bourcier'
__date__ = '2023-05-11'
__copyright__ = '(C) 2023 by Guillaume Touya, Justin Berli & Paul Bourcier'

import os
import cartagen4qgis.cartagen
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