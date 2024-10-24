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
from cartagen import boffet_areas, partition_networks
from cartagen4qgis.src.tools import *

from shapely import Polygon
from shapely.wkt import loads

class BoffetArea(QgsProcessingAlgorithm):
    """
    Calculate urban areas from buildings.

    This algorithm proposed by Boffet uses
    buffer around the buildings, then simplify and erode the unioned result
    to characterize urban areas.

    Parameters
    ----------
    polygons : list of Polygon
        Buildings to generate the urban area from.
    buffer : float
        The buffer size used to merge buildings that are close from each other.
    erosion : float
        The erosion size to avoid the urban area to expand
        too far from the buildings located on the edge.
    simplification_distance : float, optional
        The distance threshold used by the
        Douglas-Peucker simplification on the edge.
    """

     # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    
    INPUT_BUILDINGS = 'INPUT_BUILDINGS'

    NETWORK_PARTITIONING_TF = 'NETWORK_PARTITIONING_TF'
    INPUT_NETWORK_PART = 'INPUT_NETWORK_PART'

    BUFFER = 'BUFFER'
    EROSION = 'EROSION'
    SIMPLIFICATION_DISTANCE = 'SIMPLIFICATION_DISTANCE' 

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Boffet area'

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
        return self.tr("Calculate urban areas from buildings.\nThis algorithm proposed by Boffet uses buffer around the buildings, then simplify and erode the unioned result to characterize urban areas.\nBuffer : the buffer size used to merge buildings that are close from each other.\nErosion : the erosion size to avoid the urban area to expand too far from the buildings located on the edge.\nSimplification distance : the distance threshold used by the Douglas-Peucker simplification on the edge.")
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BoffetArea()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_BUILDINGS,
                self.tr('Input buildings'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        buffer = QgsProcessingParameterNumber(
            self.BUFFER,
            self.tr('Buffer size used to merge buildings'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0,
            optional=False
        )
        self.addParameter(buffer)
       
        erosion = QgsProcessingParameterNumber(
            self.EROSION,
            self.tr('Erosion size'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10,
            optional=False
        )
        self.addParameter(erosion)

        simpl_dist = QgsProcessingParameterNumber(
            self.SIMPLIFICATION_DISTANCE,
            self.tr('Distance threshold used for the simplification'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1,
            optional=False
        )
        simpl_dist.setFlags(simpl_dist.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(simpl_dist)

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.NETWORK_PARTITIONING_TF,
                self.tr('Activate network partitioning'),
                defaultValue=False,
                optional=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_NETWORK_PART,
                self.tr('Input lines for the network partition'),
                layerType=QgsProcessing.TypeVectorLine,
                optional=True
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Boffet area')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT_BUILDINGS, context)
        gdf = qgis_source_to_geodataframe(source)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        #total = 100.0 / source.featureCount() if source.featureCount() else 0
       
        # Retrieve the network parameter and transform it to a lsit of GeoDataFrame
        networks = self.parameterAsLayerList(parameters, self.INPUT_NETWORK_PART, context)
        gdf_list_networks = []
        for i in networks:
            gdf_list_networks.append(qgis_source_to_geodataframe(i))
        
        # Retrieve other parameter values
        activate_network_part = self.parameterAsBoolean(parameters, self.NETWORK_PARTITIONING_TF, context)
        buffer = self.parameterAsDouble(parameters, self.BUFFER, context)
        erosion = self.parameterAsDouble(parameters, self.EROSION, context)
        simpl_dist = self.parameterAsInt(parameters, self.SIMPLIFICATION_DISTANCE, context)

        # Use the CartAGen algorithm with or without the network partitionning
        # Transform the result to QgsFeature()
        if len(gdf_list_networks) == 0 or activate_network_part == False:
            boffet = boffet_areas(gdf.geometry,buffer = buffer, erosion = erosion, simplification_distance = simpl_dist)
            
            boffet_gdf = geopandas.GeoDataFrame(geometry=geopandas.GeoSeries(boffet))
            res = boffet_gdf.to_dict('records')
            res = list_to_qgis_feature(res)

        else:
            part = partition_networks(gdf,gdf_list_networks[0])
            if part[0] != []:
                list_gdf = []
                for i in range(len(part[0])):
                    boffet = gdf.copy()
                    boffet = boffet.iloc[part[0][i]]
                    try:
                        generalized = boffet_areas(boffet.geometry, buffer=buffer, erosion = erosion, simplification_distance = simpl_dist) 
                    except: 
                        generalized = gdf.geometry
                    
                    list_gdf.append(geopandas.GeoDataFrame(geometry=geopandas.GeoSeries(generalized)))
            
                combined_gdf = pandas.concat(list_gdf, ignore_index=True)
                combined_gdf = geopandas.GeoDataFrame(combined_gdf, geometry='geometry')  
                res = combined_gdf.to_dict('records')
                res = list_to_qgis_feature(res)  

            else:
                raise Exception("No entity detected within the network used for partitioning datas") 
        
        #Create output sink
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }