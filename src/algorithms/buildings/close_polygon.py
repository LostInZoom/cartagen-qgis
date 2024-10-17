# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CartAGen4QGIS
                                 A QGIS plugin
 Cartographic generalization
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-05-11
        copyright            : (C) 2023 by Guillaume Touya, Justin Berli & Paul Bourcier
        email                : guillaume.touya@ign.fr
 ***************************************************************************/
"""

__author__ = 'Guillaume Touya, Justin Berli & Paul Bourcier'
__date__ = '2023-05-11'
__copyright__ = '(C) 2023 by Guillaume Touya, Justin Berli & Paul Bourcier'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
    QgsFeature, QgsGeometry, QgsProcessingParameterDefinition
)
from qgis.core import (
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
    QgsProcessingParameterMultipleLayers
)

import geopandas
import pandas
from cartagen4qgis import PLUGIN_ICON
from cartagen import close_polygon
from cartagen4qgis.src.tools import *

from shapely import Polygon
from shapely.wkt import loads

class ClosePolygon(QgsProcessingAlgorithm):
    """
Close a polygon using dilation and erosion.

This algorithm relies on the successive dilation and erosion of polygon to merge close polygons together and 
simplify their complexity.

Parameters:
        polygon (Polygon or MultiPolygon) – The polygon to close.

        size (float) – The size of the dilation and erosion.

        quad_segs (int) – The number of linear segments in a quarter circle when performing the buffer.
         If above 1, the result may have round corners unsuitable for buildings.
    """

     # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    
    INPUT_POLYGONS = 'INPUT_POLYGONS'

    SIZE = 'SIZE'
    QUAD_SEGS = 'QUAD_SEGS'
 
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Close polygon'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Buildings'

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return PLUGIN_ICON

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Close a polygon using dilation and erosion.\nThis algorithm relies on the successive dilation and erosion of polygon to merge close polygons together and simplify their complexity.\nSize : The size of the dilation and erosion.\nQuad segs : the number of linear segments in a quarter circle when performing the buffer. If above 1, the result may have round corners unsuitable for buildings.")
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClosePolygon()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POLYGONS,
                self.tr('Input polygons'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )


        size = QgsProcessingParameterNumber(
            self.SIZE,
            self.tr('Size of the dilation and erosion'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0,
            optional=False
        )
        self.addParameter(size)
       
        quad_segs = QgsProcessingParameterNumber(
            self.QUAD_SEGS,
            self.tr('Number of linear segments in a quarter circle when performing the buffer'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1,
            optional=False
        )
        quad_segs.setFlags(quad_segs.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(quad_segs)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Closed polygons')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT_POLYGONS, context)
        gdf = qgis_source_to_geodataframe(source)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        size = self.parameterAsDouble(parameters, self.SIZE, context)
        quad_segs = self.parameterAsInt(parameters, self.QUAD_SEGS, context)

        cp = gdf.copy()
        for i in range(len(gdf)):
            cp.loc[i,'geometry'] = close_polygon(gdf.loc[i,"geometry"],size = size, quad_segs= quad_segs)
            
            res = cp.to_dict('records')
            res = list_to_qgis_feature_2(res,source.fields())
     
        # features = []
        # fields = source.fields()

        # for entity in res:
        #     feature = QgsFeature()
        #     feature.setFields(fields)
        #     for i in range(len(fields)):
        #         feature.setAttribute(fields[i].name(), entity[fields[i].name()])
            
        #     # Si votre entité a une géométrie (par exemple, des coordonnées x et y)
        #     geom = QgsGeometry.fromWkt(str(entity['geometry']))
        #     feature.setGeometry(geom)
            
        #     features.append(feature)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }