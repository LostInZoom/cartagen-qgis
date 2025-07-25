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
    QgsFeature, QgsGeometry, QgsProcessingParameterDefinition, QgsWkbTypes
)
from qgis.core import (
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterMultipleLayers
)

import geopandas as gpd
import pandas
from cartagen4qgis import PLUGIN_ICON
from cartagen import heatmap
from cartagen4qgis.src.tools import list_to_qgis_feature

from shapely import Polygon
from shapely.wkt import loads

class VectorHeatmap(QgsProcessingAlgorithm):
    """
    Create a heatmap using the kernel density estimation technique (KDE).

    This function performs a spatial smoothing with the kernel density estimation technique (KDE), also known as heatmap. 
    More information about heatmaps can be found in Wilkinson & Friendly. [1]

    For more information about KDE, here is a link to the related Wikipedia article. This code is partially based on this script.

    Parameters:

        points (GeoDataFrame of Point) – The points used to calculates density.

        cell_size (int) – The size of the cell of the grid containing density values. Smaller size means smoother result, but also higher computation time.

        radius (int) – The radius used for the density calculation in each grid cells. For each centroid of grid cell, all the points within the radius are taken in account for density calculation. Higher radius means more generalized results.

        column (str, optional) – Name of the column of the point to use to weight the density value.

        method (str, optional) – Name of the smoothing method that calculates the density value of each point within the radius. Each method impacts the way distance is important in the density calculation. Possible values: ‘quartic’, ‘epanechnikov’, ‘gaussian’, ‘uniform’, ‘triangular’

        clip (GeoDataFrame of Polygon, optional) – Polygons to clip the resulting heatmap grid. Be aware that it can return MultiPolygon.

    Returns:

    grid (GeoDataFrame of Polygon) – The grid containing the values of density
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    CELL_SIZE = 'CELL_SIZE'
    RADIUS = 'RADIUS'
    FIELD = 'FIELD'
    METHOD = 'METHOD'
    CLIP = 'CLIP'
 
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Vector heatmap'

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
        return 'Points'

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
        return self.tr("Create a heatmap using the kernel density estimation technique (KDE), in the form of vector layer.\nCell size : the size of the cell of the grid containing density values. Smaller size means smoother result, but also higher computation time.\nRadius : the radius used for the density calculation in each grid cells. For each centroid of grid cell, all the points within the radius are taken in account for density calculation. Higher radius means more generalized results.\nField : name of the attribute of the point to use to weight the density value.\nMethod : name of the smoothing method that calculates the density value of each point within the radius. Each method impacts the way distance is important in the density calculation. Possible values: ‘quartic’, ‘epanechnikov’, ‘gaussian’, ‘uniform’, ‘triangular’\nClip : polygon vector layer to clip the resulting heatmap grid.")
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VectorHeatmap()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input point layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        cell_size = QgsProcessingParameterNumber(
            self.CELL_SIZE,
            self.tr('Cell size'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=500,
            optional=False
        )
        self.addParameter(cell_size)

        radius = QgsProcessingParameterNumber(
            self.RADIUS,
            self.tr('Radius'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=2000,
            optional=False
        )
        self.addParameter(radius)

        methods = ['quartic', 'epanechnikov', 'gaussian', 'uniform', 'triangular']
        
        method = QgsProcessingParameterEnum(
                self.METHOD,
                'Smoothing function',
                methods,
                defaultValue=1  
            )
        method.setFlags(method.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(method)
        
        field = QgsProcessingParameterField(
                self.FIELD,
                'Value field',
                '',
                self.INPUT,  
                QgsProcessingParameterField.Numeric,
                optional=True  
            )
        field.setFlags(field.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(field)

        clip = QgsProcessingParameterFeatureSource(
                self.CLIP,
                self.tr('Input polygon layer for clipping'),
                [QgsProcessing.TypeVectorPolygon],
                optional = True
            )
        clip.setFlags(clip.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(clip)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Heatmap')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """ 
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)

        # transform the source into a GeoDataFrame
        points = gpd.GeoDataFrame.from_features(source.getFeatures())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        # total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # Retrieve the other parameters
        cell_size = self.parameterAsInt(parameters, self.CELL_SIZE, context)
        radius = self.parameterAsInt(parameters, self.RADIUS, context)
        methods = ['quartic', 'epanechnikov', 'gaussian', 'uniform', 'triangular']
        method = self.parameterAsString(parameters, self.METHOD, context)
        field = self.parameterAsString(parameters, self.FIELD, context)

        if not field:
            field = None

        feedback.setProgress(1) #set loading bar to 1 %
        
        # perform de CartAGen algorithm without the clip parameter (else there is a bug)
        res = heatmap(points, cell_size=cell_size, radius=radius, column=field, method= methods[int(method)])
        
        feedback.setProgress(90) #set loading bar to 90 %
    
        #transform the result into a dictionnary, and the dictionnary into a list of QgsFeateur()
        res = res.to_dict('records')
        res = list_to_qgis_feature(res)

        # retrieve the cliping layer (if provided) and transform it into list of QgsFeature()
        clip_layer = self.parameterAsSource(parameters, self.CLIP, context)

        if clip_layer is not None:
            clip = gpd.GeoDataFrame.from_features(clip_layer.getFeatures())
            clip = clip.to_dict('records')
            clip = list_to_qgis_feature(clip)
        
            #clip the heatmap with the cliping layer using the .intersection() method from QGIS
            polygons_cliped = []

            for feature1 in res:
                geom1 = feature1.geometry()
        
                for feature2 in clip:
                    geom2 = feature2.geometry()
                    intersection = geom1.intersection(geom2)

                if not intersection.isEmpty():
                    new_feature = QgsFeature()
                    new_feature.setGeometry(intersection)
                    new_feature.setAttributes(feature1.attributes())
                    polygons_cliped.append(new_feature)
        
        else:
            polygons_cliped = res

        # declare the ouptput sink
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), QgsWkbTypes.Polygon, source.sourceCrs())
        
        # Add a feature in the sink depending on if a clip layer is provided
        if clip_layer:
            sink.addFeatures(polygons_cliped, QgsFeatureSink.FastInsert)
        else:        
            sink.addFeatures(res, QgsFeatureSink.FastInsert)

        feedback.setProgress(100) #set loading bar to 100 %
        return {
            self.OUTPUT: dest_id
        }
