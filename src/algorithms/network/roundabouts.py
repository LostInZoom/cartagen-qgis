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

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
    QgsFeature, QgsGeometry, QgsProcessingParameterDefinition,
    QgsWkbTypes, QgsVectorLayer, QgsField, QgsFields
)
from qgis.core import (
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
)
from qgis.PyQt.QtWidgets import QMessageBox

from cartagen.enrichment.network import is_roundabout
from cartagen import collapse_roundabouts, network_faces

from cartagen4qgis import PLUGIN_ICON
from cartagen4qgis.src.tools import list_to_qgis_feature, list_to_qgis_feature_2

import geopandas as gpd
from shapely import Polygon
from shapely.wkt import loads

class DetectRoundaboutsQGIS(QgsProcessingAlgorithm):
    """
        Detect dead-ends groups.

    This function detects dead-ends groups inside a road network.
    A dead-end group is a connected group of road sections that
    overlaps the border of only one network face.
    A connected group of road sections not connected to the rest
    of the network are considered dead-ends.

    Parameters
    ----------
    roads : GeoDataFrame of LineString
        The road network.
    outside_faces : bool, optional
        Whether dead-ends should be calculated on the outside faces
        of the road network. This can induce wrong characterization
        on the border of the provided dataset.

    Returns
    -------
    roads : GeoDataFrame of LineString
        The input road network with new attributes:

        - *'deadend'*: boolean indicating whether the road is part of a dead-end group. 
        - *'face'*: Index of the network face it belongs to.
        - *'deid'*: Index of the dead end group inside a given face.
        - *'connected'*: Set to true if the dead end group is connected to the network.
        - *'root'*: Set to true if the road section is the root of the dead end group,
          *i.e.* the section connecting the dead end group to the road network.
        - *'hole'*: Set to true if the road section touches a hole inside the dead end group.
    
    See Also
    --------
    eliminate_dead_ends
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    AREA = 'AREA'
    MILLER = 'MILLER'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input road network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
                QgsProcessingParameterNumber(
                self.AREA,
                self.tr('Maximum area'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=40000,
                optional=False
            )
        )

        miller = QgsProcessingParameterNumber(
            self.MILLER,
            self.tr('Minimum Miller index'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.95,
            optional=False
        )
        miller.setFlags(miller.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(miller)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Roundabouts')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Get the QGIS source from the parameters
        source = self.parameterAsSource(parameters, self.INPUT, context)

        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        records = gdf.to_dict('records')
        count = len(records)
        feedback.setProgress(1) # set the loading bar to 1 %

        # Compute the number of steps to display within the progress bar and
        total = 100.0 / count if count > 0 else 0
        
        # Retrieve parameters
        area = self.parameterAsInt(parameters, self.AREA, context)
        miller = self.parameterAsDouble(parameters, self.MILLER, context)

        # Actual algorithm
        roads = []
        for road in records:
            roads.append(road['geometry'])

        faces = network_faces(roads, convex_hull=False)

        roundabouts = []
        index = 0
        for current, face in enumerate(faces):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            add, infos = is_roundabout(face, area, miller)
            if add:
                infos['cid'] = index
                roundabouts.append(infos)
                index += 1

            # Update the progress bar
            feedback.setProgress(int(current * total))
           
        if len(roundabouts) == 0: #manually create fields if no roundabout is detected
            fields = QgsFields()
            fields.append(QgsField("index", QVariant.Double))
            fields.append(QgsField("cid",  QVariant.Int))
            res = [QgsFeature(fields)] #create a list of empty QgsFeature with the created fields

            # QMessageBox.warning(None, "Warning", "No roundabouts detected, output layer is empty.")

        else:    
            #convert the result to a GeoDataFrame, and this gdf into a list of dicts and then a list of QgsFeature()
            gdf_final = gpd.GeoDataFrame(roundabouts, crs = source.sourceCrs().authid())
            res = gdf_final.to_dict('records')
            res = list_to_qgis_feature(res)
       
        #Create the feature sink
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            fields=res[0].fields(),
            geometryType=QgsWkbTypes.Polygon,
            crs=source.sourceCrs()
        )
        
        #Add features to the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

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
        return 'Detect roundabouts'

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
        return 'Network'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Detect roundabouts based on geometric properties.\nThis algorithm proposed by Touya detects roundabouts inside a road network.\nArea threshold : the area (in square meters) above which the object is not considered a roundabout.\nMiller index : index of compactess that determines if the shape is round or not.")
        
    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return PLUGIN_ICON

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DetectRoundaboutsQGIS()

class CollapseRoundaboutsQGIS(QgsProcessingAlgorithm):
    """
    Collapse roundabouts to a point.

    This algorithm proposed by Touya :footcite:p:`touya:2010` collapses roundabouts to a point
    if their diameter is below the given value.
    
    Parameters
    ----------
    roads : GeoDataFrame of LineString
        Road network where roundabouts will be collapsed.
    roundabouts : GeoDataFrame of Polygon
        Polygons representing the faces of the network detected as roundabouts.
    crossroads : GeoDataFrame of Polygon, optional
        Polygons representing the faces of the network detected as branching crossroads. This
        allows incoming branching crossroads on roundabouts to be collapsed as well. 
    maximum_diameter : float, optional
        Diameter, in meter, below which roundabouts are collapsed. Collpase all roundabouts if left to None.

    Returns
    -------
    GeoDataFrame of LineString

    Warning
    -------
    Detecting branching crossroads beforehand is important as a branching crossroad
    may be an entrance to a roundabout. This algorithm will collapse the roundabout
    as well as all its connected branching crossroads.

    See Also
    --------
    detect_roundabouts : 
        Detect roundabouts inside the road network.
    detect_branching_crossroads : 
        Detect branching crossroads inside the road network.
    collapse_branching_crossroads :
        Collapse branching crossroads to a point.

    References
    ----------
    .. footbibliography::
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT_ROAD = 'INPUT_ROAD'
    INPUT_ROUNDABOUTS = 'INPUT_ROUNDABOUTS'
    INPUT_CROSSROADS = 'INPUT_CROSSROADS'
    MAXIMUM_DIAMETER = 'MAXIMUM_DIAMETER'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ROAD,
                self.tr('Input road network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_ROUNDABOUTS,
                self.tr('Input roundabouts'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CROSSROADS,
                self.tr('Input crossroads'),
                [QgsProcessing.TypeVectorPolygon],
                optional=True
            )
        )

        self.addParameter(
                QgsProcessingParameterNumber(
                self.MAXIMUM_DIAMETER,
                self.tr('Maximum diameter'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=25,
                optional=False
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Collapsed roundabouts')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Get the QGIS source from the parameters
        source = self.parameterAsSource(parameters, self.INPUT_ROAD, context)

        # Define the output sink
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            fields = source.fields(),
            geometryType = QgsWkbTypes.LineString,
            crs = source.sourceCrs()
        )

        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve parameters
        maximum_diameter = self.parameterAsDouble(parameters, self.MAXIMUM_DIAMETER, context)
        rb = self.parameterAsSource(parameters, self.INPUT_ROUNDABOUTS, context)
        rb = gpd.GeoDataFrame.from_features(rb.getFeatures())

        # Use the CartAGen algorithm with the right parameter accordingto the inputs
        if self.parameterAsSource(parameters, self.INPUT_CROSSROADS, context):
            cr = self.parameterAsSource(parameters, self.INPUT_CROSSROADS, context)
            cr = gpd.GeoDataFrame.from_features(cr.getFeatures())
            cllpsed = collapse_roundabouts(gdf,rb,cr,maximum_diameter)
        else:
            cllpsed = collapse_roundabouts(gdf,rb,maximum_diameter= maximum_diameter)
        
        # convert the resultto a list of dictionnaries
        cllpsed = cllpsed.to_dict('records')
        # Converts the list of dicts to a list of qgis features
        result = list_to_qgis_feature_2(cllpsed, source.fields())

        # Add features to the sink
        sink.addFeatures(result, QgsFeatureSink.FastInsert)
        
        return { self.OUTPUT: dest_id }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Collapse roundabouts'

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
        return 'Network'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Collapse roundabouts to a point.\nThis algorithm proposed by Touya collapses roundabouts to a point if their diameter is below the given value.\nRoundabouts : polygons representing the faces of the network detected as roundabouts.\nCrossroads : polygons representing the faces of the network detected as branching crossroads. This allows incoming branching crossroads on roundabouts to be collapsed as well.\nMaximum_diameter : diameter, in meter, below which roundabouts are collapsed. Collpase all roundabouts if left to None")
        
    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return PLUGIN_ICON

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CollapseRoundaboutsQGIS()