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

import geopandas as gpd
from cartagen4qgis import PLUGIN_ICON
from cartagen import random_displacement, partition_networks

from shapely import Polygon
from shapely.wkt import loads

class BuildingDisplacementRandomQGIS(QgsProcessingAlgorithm):
    """
    Iteratively displace polygons overlapping each other and the provided network.

    Displace the provided buildings if they overlap each other
    or are closer than the width value to the provided networks.

    Parameters
    ----------
    polygons : GeoDataFrame of Polygon
        The buildings to displace.
    networks : list of GeoDataFrame of LineString, optional
        A list of networks the polygons need to be moved away from.
        If left to None, polygons will only be moved away from each other.
    polygon_distance : float, optional
        The minimum acceptable distance between polygons.
    network_distance : float, optional
        The minimum acceptable distance between the polygons
        and the provided networks.
    max_trials : int, optional
        The maximum number of trials before stopping the iteration.
        A trial represent the movement of one polygon that did not
        lower the mean overlapping area between polygons and networks.
    max_displacement : float, optional
        The maximum allowed distance of displacement per iteration.
    network_partioning : GeoDataFrame of LineString, optional
        The network to partition the data with. If provided, each network
        face is treated individually, thus improving performance on larger dataset.

    Returns
    -------
    GeoDataFrame
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    
    INPUT_BUILDINGS = 'INPUT_BUILDINGS'

    INPUT_NETWORK = 'INPUT_NETWORK'

    NETWORK_PARTITIONING_TF = 'NETWORK_PARTITIONING_TF'
    INPUT_NETWORK_PART = 'INPUT_NETWORK_PART'

    POLYGON_DISTANCE = 'POLYGON_DISTANCE'
    NETWORK_DISTANCE = 'NETWORK_DISTANCE'
    
    MAX_TRIALS = 'MAX_TRIALS'
    MAX_DISPLACEMENT = 'MAX_DISPLACEMENT' 

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

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_NETWORK,
                self.tr('Input rivers and/or roads networks'),
                layerType=QgsProcessing.TypeVectorLine,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.POLYGON_DISTANCE,
                self.tr('Minimum acceptable distance between polygons'),
                defaultValue=10.0,
                optional=False,
                parentParameterName='INPUT_BUILDINGS'
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.NETWORK_DISTANCE,
                self.tr('Minimum acceptable distance between the polygons and the provided networks'),
                defaultValue=10.0,
                optional=True,
                parentParameterName='INPUT_BUILDINGS'
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.NETWORK_PARTITIONING_TF,
                self.tr('Network partitioning'),
                defaultValue=True,
                optional=False
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

        maxtrials = QgsProcessingParameterNumber(
            self.MAX_TRIALS,
            self.tr('Maximum number of trials'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=25,
            optional=False
        )
        maxtrials.setFlags(maxtrials.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(maxtrials)

        maxdisp = QgsProcessingParameterNumber(
            self.MAX_DISPLACEMENT,
            self.tr('Maximum allowed distance of displacement per iteration'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10.0,
            optional=True
        )
        maxdisp.setFlags(maxdisp.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(maxdisp)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Displaced')
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
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        # Retrieve the network and transform it into a list of GeoDataFrame
        networks = self.parameterAsLayerList(parameters, self.INPUT_NETWORK_PART, context)
        gdf_list_networks = []
        for i in networks:
            gdf_list_networks.append(gpd.GeoDataFrame.from_features(i.getFeatures()))

        # Retrieve the other parameter values 
        max_displ = self.parameterAsDouble(parameters, self.MAX_DISPLACEMENT, context)
        maxtrials = self.parameterAsInt(parameters, self.MAX_TRIALS, context)
        poly_dist = self.parameterAsDouble(parameters, self.POLYGON_DISTANCE, context)
        network_dist = self.parameterAsDouble(parameters, self.NETWORK_DISTANCE, context)
        activate_network_part = self.parameterAsBoolean(parameters, self.NETWORK_PARTITIONING_TF, context)
        network_part = self.parameterAsLayerList(parameters, self.INPUT_NETWORK_PART, context)

        # Use the CartAGen algorithm with or without network partitionning
        if len(network_part) == 0 or activate_network_part == False:
            d = random_displacement(
                polygons=gdf, networks=gdf_list_networks, polygon_distance=poly_dist, 
                network_distance=network_dist, max_trials=maxtrials, max_displacement=max_displ
            )
        
        else:
            
            network_part_gdf = gpd.GeoDataFrame.from_features(network_part[0])
            d = random_displacement(
                polygons=gdf, networks=gdf_list_networks, polygon_distance=poly_dist, 
                network_distance=network_dist, max_trials=maxtrials, max_displacement=max_displ, network_partitioning=[network_part_gdf]
            )
        
        # Convert the result to a list of dictionnaries
        d = d.to_dict('records')

        #Convert the list to a list of QgsFeature() (TO-DO : use the converter.py instead)
        features = []
        fields = source.fields()
        for entity in d:
            feature = QgsFeature()
            feature.setFields(fields)
            for i in range(len(fields)):
                feature.setAttribute(fields[i].name(), entity[fields[i].name()])
            
            # Si votre entité a une géométrie (par exemple, des coordonnées x et y)
            geom = QgsGeometry.fromWkt(str(entity['geometry']))
            feature.setGeometry(geom)
            
            features.append(feature)
        
        # Create the output sink
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, features[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(features, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Random displacement'

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
        return self.tr("Iteratively displace polygons overlapping each other and the provided network.\nDisplace the provided buildings if they overlap each other or are closer than the width value to the provided networks.\nNetworks : a list of networks the polygons need to be moved away from. If left to None, polygons will only be moved away from each other.\nPolygon distance : the minimum acceptable distance between polygons.\nNetwork distance : the minimum acceptable distance between the polygons and the provided networks.\nMax trials : the maximum number of trials before stopping the iteration. A trial represent the movement of one polygon that did not lower the mean overlapping area between polygons and networks.\nMax displacement : the maximum allowed distance of displacement per iteration.\nNetwork partioning : the network to partition the data with. If provided, each network face is treated individually, thus improving performance on larger dataset")
        

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BuildingDisplacementRandomQGIS()
