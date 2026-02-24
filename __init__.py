# -*- coding: utf-8 -*-
"""
/***************************************************************************
CartAGen4QGIS
A QGIS plugin
***************************************************************************/
"""
__author__ = 'Guillaume Touya, Justin Berli & Paul Bourcier'
__date__ = '2025-07-01'
__copyright__ = '(C) 2025 by Guillaume Touya, Justin Berli & Paul Bourcier'

import os

PLUGIN_ICON = None

def get_plugin_icon():
    """Return the plugin icon"""
    global PLUGIN_ICON
    if PLUGIN_ICON is None:
        try:
            from qgis.PyQt.QtGui import QIcon
            icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.svg')
            
            # Check the file exists before loading it
            if os.path.exists(icon_path):
                PLUGIN_ICON = QIcon(icon_path)
            else:
                # If no svg, try the png
                icon_path_png = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
                if os.path.exists(icon_path_png):
                    PLUGIN_ICON = QIcon(icon_path_png)
                else:
                    # Get an empty icon
                    PLUGIN_ICON = QIcon()
        except Exception as e:
            # In case of error, return empty icon to avoid crash
            PLUGIN_ICON = QIcon()
    
    return PLUGIN_ICON

def classFactory(iface):
    """
    Load CartAGen4QGIS class from file CartAGen4QGIS.
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .cartagenplugin import CartAGen4QGISPlugin
    return CartAGen4QGISPlugin()