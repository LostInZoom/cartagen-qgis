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
    QgsProcessingParameterMultipleLayers
)

import geopandas
import pandas
from cartagen4qgis import PLUGIN_ICON
from cartagen import gaussian_smoothing
from cartagen4qgis.src.tools import *

from shapely import Polygon
from shapely.wkt import loads

class GaussianSmoothing(QgsProcessingAlgorithm):
    """
    Smooth a line and attenuate its inflexion points.
    The gaussian smoothing has been studied by Babaud et al. for image processing,
    and by Plazanet for the generalisation of cartographic features.

    Parameters:
        line (LineString) – The line to smooth.

        sigma (float, optional) – Gaussian filter strength. Default value to 30, which is a high value.

        sample (float, optional) – The length in meter between each nodes after resampling the line. If not provided, the sample is derived from the line and is the average distance between each consecutive vertex.

        densify (bool, optional) – Whether the resulting line should keep the new node density. Default to True.
    """

     # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    
    INPUT = 'INPUT'

    SIGMA = 'SIGMA'
    SAMPLE = 'SAMPLE'
    DENSIFY = 'DENSIFY'
 
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Gaussian smoothing'

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
        return 'Lines'

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
        return self.tr("Smooth a line and attenuate its inflexion points.\nThe gaussian smoothing has been studied by Babaud et al. for image processing, and by Plazanet for the generalisation of cartographic features.\nSigma : gaussian filter strength. Default value to 30, which is a high value.\nSample : the length in meter between each nodes after resampling the line. If not provided, the sample is derived from the line and is the average distance between each consecutive vertex.\nDensify : whether the resulting line should keep the new node density. Default to True.\nNote that this algorithm also works on polygons, but is not really suited for it.")
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GaussianSmoothing()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input lines or polygons'),
                [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine]
            )
        )


        sigma = QgsProcessingParameterNumber(
            self.SIGMA,
            self.tr('Gaussian filter strength'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=30.0,
            optional=False
        )
        self.addParameter(sigma)
       
        densify = QgsProcessingParameterBoolean(
            self.DENSIFY,
                self.tr('Keep the new node density'),
                optional=False,
                defaultValue=True
            )
        densify.setFlags(densify.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(densify)

        sample = QgsProcessingParameterNumber(
            self.SAMPLE,
            self.tr('Length in meter between each nodes after resampling'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=30.0,
            optional=False
        )
        self.addParameter(sample)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Smoothed')
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
        gdf = qgis_source_to_geodataframe(source)
        
        # Compute the number of steps to display within the progress bar and
        # get features from source
        #total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # retrieve the other parameters values
        sigma = self.parameterAsDouble(parameters, self.SIGMA, context)
        sample = self.parameterAsDouble(parameters, self.SAMPLE, context)
        densify = self.parameterAsBoolean(parameters, self.DENSIFY, context)

        #Using CartAGen algorithm and transforming the result to a list of QgsFeature()
        #Depending on the type of geometry of the input data
        if source.wkbType().name == 'Polygon':
            gs = gdf.copy()
            for i in range(len(gdf)):
                #try:
                gs.loc[i,'geometry'] = gaussian_smoothing(list(gs.geometry)[i], sigma= sigma, sample= sample, densify = densify)
                # except:
                #     gs.loc[i,'geometry'] = gs.loc[i,'geometry'] 
                
                #gs.loc[i,'geometry'] = Polygon(gs.loc[i,'geometry'])

            res = gs.to_dict('records')
            res = list_to_qgis_feature_2(res,source.fields())

        else:
            gs = gdf.copy()
            for i in range(len(gdf)):
                try:
                    gs.loc[i,'geometry'] = gaussian_smoothing(list(gs.geometry)[i], sigma= sigma, sample= sample, densify = densify)
                except:
                    gs.loc[i,'geometry'] = gs.loc[i,'geometry']
            
            res = gs.to_dict('records')
            res = list_to_qgis_feature_2(res,source.fields())

        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }