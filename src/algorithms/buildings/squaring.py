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
from qgis.core import QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm, QgsFeature, QgsGeometry, QgsProcessingParameterDefinition
from qgis.core import QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink, QgsProcessingParameterNumber

from cartagen4qgis import PLUGIN_ICON
from cartagen import square_polygon_ls
from shapely import Polygon
from shapely.wkt import loads

class SquaringQGIS(QgsProcessingAlgorithm):
    """
    Square buildings using the least square method
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    MAX_ITERATION = 'MAX_ITERATION'
    NORM_TOLERANCE = 'NORM_TOLERANCE'
    RIGHT_TOLERANCE = 'RIGHT_TOLERANCE'
    FLAT_TOLERANCE = 'FLAT_TOLERANCE'
    HALF_RIGHT_TOLERANCE = 'HALF_RIGHT_TOLERANCE'
    WEIGHT_FIX = 'WEIGHT_FIX'
    WEIGHT_RIGHT = 'WEIGHT_RIGHT'
    WEIGHT_FLAT = 'WEIGHT_FLAT'
    WEIGHT_HALF_RIGHT = 'WEIGHT_HALF_RIGHT'
    THRESHOLD = 'THRESHOLD'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input buildings'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        maxiter = QgsProcessingParameterNumber(
            self.MAX_ITERATION,
            self.tr('Maximum number of iterations'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1000,
            optional=False
        )
        maxiter.setFlags(maxiter.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        normtol = QgsProcessingParameterNumber(
            self.NORM_TOLERANCE,
            self.tr('Norm tolerance'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.05,
            optional=False
        )
        normtol.setMetadata({'widget_wrapper':{ 'decimals': 2 }})
        normtol.setFlags(normtol.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        righttol = QgsProcessingParameterNumber(
            self.RIGHT_TOLERANCE,
            self.tr('Right angle tolerance'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10,
            optional=False
        )
        righttol.setMetadata({'widget_wrapper':{ 'decimals': 2 }})
        righttol.setFlags(righttol.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        flattol = QgsProcessingParameterNumber(
            self.FLAT_TOLERANCE,
            self.tr('Flat angle tolerance'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=10,
            optional=False
        )
        flattol.setMetadata({'widget_wrapper':{ 'decimals': 2 }})
        flattol.setFlags(flattol.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        hrtol = QgsProcessingParameterNumber(
            self.HALF_RIGHT_TOLERANCE,
            self.tr('45° and 135° angle tolerance'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=7,
            optional=False
        )
        hrtol.setMetadata({'widget_wrapper':{ 'decimals': 2 }})
        hrtol.setFlags(hrtol.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        wfix = QgsProcessingParameterNumber(
            self.WEIGHT_FIX,
            self.tr('Fixed points weight'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=5,
            optional=False
        )
        wfix.setFlags(wfix.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        wright = QgsProcessingParameterNumber(
            self.WEIGHT_RIGHT,
            self.tr('Right angles weight'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=100,
            optional=False
        )
        wright.setFlags(wright.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        wflat = QgsProcessingParameterNumber(
            self.WEIGHT_FLAT,
            self.tr('Flat angles weight'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=50,
            optional=False
        )
        wflat.setFlags(wflat.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        whright = QgsProcessingParameterNumber(
            self.WEIGHT_HALF_RIGHT,
            self.tr('45° and 135° angles weight'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=10,
            optional=False
        )
        whright.setFlags(whright.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.addParameter(maxiter)
        self.addParameter(normtol)
        self.addParameter(righttol)
        self.addParameter(flattol)
        self.addParameter(hrtol)
        self.addParameter(wfix)
        self.addParameter(wright)
        self.addParameter(wflat)
        self.addParameter(whright)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Squared')
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
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, source.fields(), source.wkbType(), source.sourceCrs())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        maxiter = self.parameterAsInt(parameters, self.MAX_ITERATION, context)
        normtol = self.parameterAsInt(parameters, self.NORM_TOLERANCE, context)
        rtol = self.parameterAsDouble(parameters, self.RIGHT_TOLERANCE, context)
        ftol = self.parameterAsDouble(parameters, self.FLAT_TOLERANCE, context)
        hrtol = self.parameterAsDouble(parameters, self.HALF_RIGHT_TOLERANCE, context)
        wfixed = self.parameterAsInt(parameters, self.WEIGHT_FIX, context)
        wright = self.parameterAsInt(parameters, self.WEIGHT_RIGHT, context)
        wflat = self.parameterAsInt(parameters, self.WEIGHT_FLAT, context)
        whright = self.parameterAsInt(parameters, self.WEIGHT_HALF_RIGHT, context)

        sq = Squarer(
            max_iteration=maxiter, norm_tolerance=normtol,
            right_tolerance=rtol, flat_tolerance=ftol, half_right_tolerance=hrtol,
            fixed_weight=wfixed, right_weight=wright, flat_weight=wflat, half_right_weight=whright
        )

        buildings = []
        attributes = []
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            attributes.append(feature.attributes())
            wkt = feature.geometry().asWkt()
            shapely_geom = loads(wkt)

            buildings.append(shapely_geom)
            # Update the progress bar
            feedback.setProgress(int(current * total))

        points = sq.square(buildings)
        simplified = sq.get_shapes_from_new_points(buildings, points)

        for i, simple in enumerate(simplified):
            result = QgsFeature()
            result.setGeometry(QgsGeometry.fromWkt(Polygon(simple).wkt))
            result.setAttributes(attributes[i])

            # Add a feature in the sink
            sink.addFeature(result, QgsFeatureSink.FastInsert)

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
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
        return 'Squaring'

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
        return self.tr("to be completed")
        
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SquaringQGIS()
