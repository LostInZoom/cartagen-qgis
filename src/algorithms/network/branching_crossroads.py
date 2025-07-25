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
__date__ = '2024-07-31'
__copyright__ = '(C) 2024 by Guillaume Touya, Justin Berli & Paul Bourcier'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
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
from qgis.PyQt.QtCore import QVariant, QDateTime
from qgis.PyQt.QtWidgets import QMessageBox

import math
import geopandas as gpd
from shapely import Polygon
from shapely.wkt import loads

from cartagen import detect_branching_crossroads, collapse_branching_crossroads

from cartagen4qgis import PLUGIN_ICON
from cartagen4qgis.src.tools import list_to_qgis_feature

class DetectBranchingCrossroads(QgsProcessingAlgorithm):
    """
    Detect branching crossroads based on geometric properties.

    This algorithm proposed by Touya :footcite:p:`touya:2010` detects
    branching crossroads inside a road network based on the proximity between
    the geometry of the network face and a triangle.

    Parameters
    ----------
    roads : GeoDataFrame of LineString
        Road network to analyze.
    roundabouts : GeoDataFrame of Polygon, optional
        The polygons representing the network faces considered as roundabouts.
        If provided, links the branching crossroad to a roundabout for collapsing.
    area_threshold : int, optional
        The area (in square meters) above which the object is not considered a branching crossroads.
    maximum_distance_area : float, optional
        The maximum distance area between the actual polygon
        and the triangle formed by the 3 nodes connecting
        the junction to the rest of the network.
    allow_middle_node : bool, optional
        If set to True, allow 4 nodes to form the crossroads,
        but each must have a degree of 3 and the 'middle'
        node must have an angle of 180°.
    middle_angle_tolerance : float, optional
        If allow_middle_node is set to True,
        indicate an angle tolerance in degree
        for the fourth node of the crossroad to be considered the middle node.
    allow_single_4degree_node : bool, optional
        If set to True, allow one and only one node to have a degree of 4.

    Returns
    -------
    GeoDataFrame of Polygon

    Warning
    -------
    Detecting roundabouts beforehand is important as a branching crossroad
    may be an entrance to a roundabout. This algorithm will link branching
    crossroads to a roundabout when applicable, and this will help collapsing
    both objects.

    See Also
    --------
    detect_roundabouts : 
        Detect roundabouts inside the road network.
    collapse_roundabouts :
        Collapse roundabouts to a point.
    collapse_branching_crossroads :
        Collapse branching crossroads to a point.
    
    References
    ----------
    .. footbibliography::
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_ROAD = 'INPUT_ROAD'
    INPUT_ROUNDABOUT = 'INPUT_ROUNDABOUT'
    OUTPUT = 'OUTPUT'
    AREA_THRESHOLD = 'AREA_THRESHOLD'
    MAXIMUM_DISTANCE_AREA = 'MAXIMUM_DISTANCE_AREA'
    ALLOW_MIDDLE_NODE = 'ALLOW_MIDDLE_NODE'
    MIDDLE_ANGLE_TOLERANCE = 'MIDDLE_ANGLE_TOLERANCE'
    ALLOW_SINGLE_4DEGREE_NODE = 'ALLOW_SINGLE_4DEGREE_NODE'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DetectBranchingCrossroads()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Detect branching crossroads'

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
        return self.tr("This algorithm proposed by Touya detects branching crossroads inside a road network based on the proximity between the geometry of the network face and a triangle.\nRoundabouts : the polygons representing the network faces considered as roundabouts. If provided, links the branching crossroad to a roundabout for collapsing.\nArea threshold : the area (in square meters) above which the object is not considered a branching crossroads.\nMaximum_distance_area : the maximum distance area between the actual polygon and the triangle formed by the 3 nodes connecting the junction to the rest of the network.\nAllow_middle_node : if set to True, allow 4 nodes to form the crossroads, but each must have a degree of 3 and the 'middle' node must have an angle of 180°.\nMiddle_angle_tolerance : if allow_middle_node is set to True, indicate an angle tolerance in degree for the fourth node of the crossroad to be considered the middle node.\nAllow_single_4degree_node : if set to True, allow one and only one node to have a degree of 4.")
        
    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return PLUGIN_ICON


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
                self.INPUT_ROUNDABOUT,
                self.tr('Input roundabouts'),
                [QgsProcessing.TypeVectorPolygon],
                optional=True
            )
        )          
                
        area_threshold = QgsProcessingParameterNumber(
            self.AREA_THRESHOLD,
                self.tr('Area threshold'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue= 1000
            )
        self.addParameter(area_threshold)	  

        maximum_distance_area = QgsProcessingParameterNumber(
            self.MAXIMUM_DISTANCE_AREA,
                self.tr('Maximum distance area'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue= 0.5
            )
        maximum_distance_area.setFlags(maximum_distance_area.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(maximum_distance_area)	    
	
        allow_middle_node = QgsProcessingParameterBoolean(
            self.ALLOW_MIDDLE_NODE,
                self.tr('Allow middle node'),
                optional=True,
                defaultValue=True
            )
        allow_middle_node.setFlags(allow_middle_node.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(allow_middle_node)

        middle_angle_tolerance = QgsProcessingParameterNumber(
            self.MIDDLE_ANGLE_TOLERANCE,
                self.tr('Middle angle tolerance'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue=10
            )
        middle_angle_tolerance.setFlags(middle_angle_tolerance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(middle_angle_tolerance)

        allow_single_4degree_node = QgsProcessingParameterBoolean(
            self.ALLOW_SINGLE_4DEGREE_NODE,
                self.tr('Allow single 4degree node'),
                optional=True,
                defaultValue=True
            )
        allow_single_4degree_node.setFlags(allow_single_4degree_node.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(allow_single_4degree_node)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Detected branching crossroads')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Get the QGIS source from the parameters
        source = self.parameterAsSource(parameters, self.INPUT_ROAD, context)

        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # retrieve the other input
        rb = self.parameterAsSource(parameters, self.INPUT_ROUNDABOUT, context)
        allow_mid_node = self.parameterAsBoolean(parameters, self.ALLOW_MIDDLE_NODE, context)
        allow_4degree = self.parameterAsBoolean(parameters, self.ALLOW_SINGLE_4DEGREE_NODE, context)
        max_dist_area = self.parameterAsDouble(parameters, self.MAXIMUM_DISTANCE_AREA, context)
        mid_angle_tolerance = self.parameterAsDouble(parameters, self.MIDDLE_ANGLE_TOLERANCE, context)
        area_thrshld = self.parameterAsDouble(parameters, self.AREA_THRESHOLD, context)

        #Perform the CartAGen algorithm with or without the roundabount input
        if rb:
            rb = gpd.GeoDataFrame.from_features(rb.getFeatures())
            br = detect_branching_crossroads(
                gdf, roundabouts= rb, area_threshold = area_thrshld,
                maximum_distance_area = max_dist_area, allow_middle_node = allow_mid_node,
                middle_angle_tolerance = mid_angle_tolerance, allow_single_4degree_node = allow_4degree
            )
            
        else:
            br = detect_branching_crossroads(
                gdf, area_threshold = area_thrshld, maximum_distance_area = max_dist_area, 
                allow_middle_node = allow_mid_node, middle_angle_tolerance = mid_angle_tolerance,
                allow_single_4degree_node = allow_4degree
            )
        
        # Manually create an empty QgsFeature() if there are no branching crossroads detected
        if br.shape[0] == 0:    
            fields = QgsFields()
            fields.append(QgsField("distance_area", QVariant.Double))
            fields.append(QgsField("cid",  QVariant.Int))
            fields.append(QgsField("middle",  QVariant.Int))
            fields.append(QgsField("roundabout",  QVariant.Int))
            fields.append(QgsField("type",  QVariant.String))

            res = [QgsFeature(fields)]
            # QMessageBox.warning(None, "Warning", "No branching crossroads detected, output layer is empty.")

        else:
            res = list_to_qgis_feature(br.to_dict('records'))
          
        #Create the output sink
        (sink, dest_id) = self.parameterAsSink(
                parameters, self.OUTPUT, context,
                fields=res[0].fields(),
                geometryType=QgsWkbTypes.Polygon,
                crs=source.sourceCrs()
            )

        #Add features in the output sink   
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }


class CollapseBranchingCrossroads(QgsProcessingAlgorithm):
    """
    Collapse branching crossroads to a point.

    This algorithm proposed by Touya collapses
    detected branching crossroads below the provided area to a point on what
    is detected as the main road.
    
    Parameters
    ----------
    roads : GeoDataFrame of LineString
        The road network where branching crossroads will be collapsed.
    crossroads : GeoDataFrame of Polygon
        Polygons representing the faces of the network detected as branching crossroads.
        Crossroads connected to a roundabout won't be collapsed.
    maximum_area : float, optional
        The area, in square meter, below which branching crossroads are collapsed.
        Collpase all crossraods if left to None.

    Returns
    -------
    GeoDataFrame of LineString

    Warning
    -------
    Detecting roundabouts beforehand is important as a branching crossroad
    may be an entrance to a roundabout. If roundabouts where provided when
    using :func:`detect_branching_crossroads` an attribute will link the
    crossroads to their relative roundabout. Those connected crossroads
    won't be collapsed by this algorithm but they will be collapsed by
    :func:`collapse_roundabouts`.

    See Also
    --------
    detect_roundabouts :
        Detect roundabouts inside the road network.
    detect_branching_crossroads :
        Detect branching crossroads inside the road network.
    collapse_roundabouts :
        Collapse roundabouts to a point.

    References
    ----------
    .. footbibliography::
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_ROAD = 'INPUT_ROAD'
    INPUT_BRANCHING_CROSSROADS = 'INPUT_BRANCHING_CROSSROADS'
    MAXIMUM_AREA = 'MAXIMUM_AREA'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CollapseBranchingCrossroads()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Collapse branching crossroads'

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
        return self.tr("Collapse branching crossroads to a point.\nThis algorithm proposed by Touya collapses detected branching crossroads below the provided area to a point on what is detected as the main road.\nCrossroads : polygons representing the faces of the network detected as branching crossroads. Crossroads connected to a roundabout won't be collapsed.\nMaximum_area : the area, in square meter, below which branching crossroads are collapsed. Collpase all crossraods if left to None.")
        
    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return PLUGIN_ICON

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
                self.INPUT_BRANCHING_CROSSROADS,
                self.tr('Input branching crossroads'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False
            )
        )          
                
        maximum_area = QgsProcessingParameterNumber(
            self.MAXIMUM_AREA,
                self.tr('Maximum area'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue= 1000
            )
        self.addParameter(maximum_area)	  

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Collapsed branching crossroads')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
      
        # Get the QGIS source from the parameters
        source = self.parameterAsSource(parameters, self.INPUT_ROAD, context)

        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # retrieve the branching crossroads layerand converts it to gdf
        bc = self.parameterAsSource(parameters, self.INPUT_BRANCHING_CROSSROADS, context)
        bc = gpd.GeoDataFrame.from_features(bc.getFeatures())

        # retrieve max_area parameter value
        max_area = self.parameterAsDouble(parameters, self.MAXIMUM_AREA, context)

        #CartAGen's algorithm
        cllpsed = collapse_branching_crossroads(gdf, bc, maximum_area=max_area)
        
        #try to convert the result to a list of dicts. If not possible, convert the initial road network instead
        try:
            cllpsed = cllpsed.to_dict('records')
        except AttributeError:
            cllpsed = gdf.to_dict('records')
           
        # Convert this list to a list of QgsFeature()
        res = list_to_qgis_feature(cllpsed)

        # Create the ouptput sink
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            fields=res[0].fields(),
            geometryType=QgsWkbTypes.LineString,
            crs=source.sourceCrs()
        )

        # Add features to the output sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)       

        return {
            self.OUTPUT: dest_id
        }