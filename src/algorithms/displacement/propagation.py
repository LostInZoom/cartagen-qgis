from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
    QgsFeature, QgsGeometry, QgsProcessingParameterDefinition,
    QgsProcessingException, QgsWkbTypes,
    QgsProcessingParameterEnum,    
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
    QgsProcessingParameterField
)    

# class PropagationCrowFlies (QgsProcessingAlgorithm):
    
#     """  
#     Propagate a displacement using the method “as the crow flies”.

#     Implementation of the displacement propagation algorithm “as the crow flies”, by Legrand et al. [1]. This function propagates the displacement defined by the movement of initiator objects to nearby movable objects, while respecting frozen objects that should not be moved.

#     Be careful, the initiators should be LineString, not MultiLineString objects.

#     Parameters:

#             objects (GeoDataFrame of Point or LineString) – The objects modified by the propagation.

#             initiator_start (LineString) – The origin of the propagation before displacement.

#             initiator_end (LineString) – The origin of the propagation after displacement.

#             frozen (GeoDataFrame of Point or LineString) – The objects that should not be modified by the propagation.

#             distance (float) – The distance around the initiator to propagate displacement. It corresponds to SizePZ in the paper by Legrand et al.

#             interval (float, optional) – Interval used for the interpolation during the initial displacement vector calculation.

#     Returns:

#         GeoDataFrame – Same as input but with displaced geometries
#     """

#     # Constants used to refer to parameters and outputs. They will be
#     # used when calling the algorithm from another algorithm, or when
#     # calling from the QGIS console.

#     OUTPUT='OUTPUT'
#     INPUT='INPUT'
#     INITIATOR_START='INITIATOR_START'
#     INITIATOR_END='INITIATOR_END'
#     FROZEN='FROZEN'
#     DISTANCE='DISTANCE'
#     INTERVAL='INTERVAL'

#     def name(self):
#         """
#         Returns the algorithm name, used for identifying the algorithm. This
#         string should be fixed for the algorithm, and must not be localised.
#         The name should be unique within each provider. Names should contain
#         lowercase alphanumeric characters only and no spaces or other
#         formatting characters.
#         """
#         return 'Propagation Crow Flies'

#     def displayName(self):
#         """
#         Returns the translated algorithm name, which should be used for any
#         user-visible display of the algorithm name.
#         """
#         return self.tr(self.name())

#     def group(self):
#         """
#         Returns the name of the group this algorithm belongs to. This string
#         should be localised.
#         """
#         return self.tr(self.groupId())

#     def groupId(self):
#         """
#         Returns the unique ID of the group this algorithm belongs to. This
#         string should be fixed for the algorithm, and must not be localised.
#         The group id should be unique within each provider. Group id should
#         contain lowercase alphanumeric characters only and no spaces or other
#         formatting characters.
#         """
#         return 'Lines Displacement'

#     def icon(self):
#         """
#         Should return a QIcon which is used for your provider inside
#         the Processing toolbox.
#         """
#         from cartagen4qgis import get_plugin_icon
#         return get_plugin_icon()

#     def shortDescription(self):
#         """
#         Returns an optional translated short description of the algorithm. This 
#         should be at most a single sentence, e.g. “Converts 2D features to 3D by 
#         sampling a DEM raster.”
#         """
#         first_line = self.shortHelpString().strip().splitlines()[2]
#         description = self.tr(first_line)
        
#         return(description)

#     def shortHelpString(self):
#         """
#         Returns a localised short helper string for the algorithm. This string
#         should provide a basic description about what the algorithm does and the
#         parameters and outputs associated with it..
#         """
        
#         helpstring = """
#         <b>/!\ Doesn't work with multipart geometry /!\</b>

#         Propagate a displacement using the method “as the crow flies”.
#         Implementation of the displacement propagation algorithm “as the crow flies”, by Legrand et al. This function propagates the displacement defined by the movement of initiator objects to nearby movable objects, while respecting frozen objects that should not be moved.
#         <h3> Parameters: </h3>
#         <ul>
#               <li> - <em>Initiator start </em> :  The origin of the propagation before displacement. </li>
#               <li> - <em>Initiator end </em> :  The origin of the propagation after displacement. </li>
#               <li> - <em>Frozen </em> :  The objects that should not be modified by the propagation. </li>
#               <li> - <em>Distance </em> :  The distance around the initiator to propagate displacement. It corresponds to SizePZ in the paper by Legrand et al. </li>
#               <li> - <em>Interval </em> :  Interval used for the interpolation during the initial displacement vector calculation. </li>
#         </ul>
#         For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.propagation_crow_flies.html#cartagen.propagation_crow_flies">help online</a>.   
#         """
        
#         return self.tr(helpstring)
    
#     def tr(self, string):
#         return QCoreApplication.translate('Processing', string)

#     def createInstance(self):
#         return PropagationCrowFlies()

#     def initAlgorithm(self, config):
#         """
#         Here we define the inputs and output of the algorithm, along
#         with some other properties.
#         """
                
#         # We add the input vector features source.
#         input = QgsProcessingParameterFeatureSource(
#                 self.INPUT,
#                 self.tr('The objects modified by the propagation :'),
#                 [QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine]
#             )
#         self.addParameter(input)
        
#         initiator_start = QgsProcessingParameterFeatureSource(
#             name=self.INITIATOR_START,
#             description="Initiator start :",
#             types=[QgsProcessing.TypeVectorLine]
#         )
#         self.addParameter(initiator_start)
            
#         initiator_end = QgsProcessingParameterFeatureSource(
#             name=self.INITIATOR_END,
#             description="Initiator end :",
#             types=[QgsProcessing.TypeVectorLine]
#         )
#         self.addParameter(initiator_end)
            
#         frozen = QgsProcessingParameterFeatureSource(
#             name=self.FROZEN,
#             description="Frozen :",
#             types=[QgsProcessing.TypeVectorLine],
#             optional=True
#         )
#         self.addParameter(frozen)
            
#         distance = QgsProcessingParameterNumber(
#             self.DISTANCE,
#             self.tr('Distance :'),
#             type=QgsProcessingParameterNumber.Double,
#             defaultValue=1,
#             optional=False
#         )
#         self.addParameter(distance)
        
#         interval = QgsProcessingParameterNumber(
#             self.INTERVAL,
#             self.tr('Interval :'),
#             type=QgsProcessingParameterNumber.Double,
#             defaultValue=2,
#             optional=False
#         )
#         interval.setFlags(interval.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
#         self.addParameter(interval)
        
#         # We add a feature sink in which to store our processed features (this
#         # usually takes the form of a newly created vector layer when the
#         # algorithm is run in QGIS).   
#         output = QgsProcessingParameterFeatureSink(
#                 self.OUTPUT,
#                 self.tr('Propagated Crow Flies'))
#         self.addParameter(output)

#     def processAlgorithm(self, parameters, context, feedback):
#         """
#         Here is where the processing itself takes place.
#         """
#         import geopandas as gpd
#         import pandas
#         from cartagen import propagation_crow_flies
#         from cartagen4qgis.src.tools import list_to_qgis_feature_2

#         # Retrieve the feature source and sink. The 'dest_id' variable is used
#         # to uniquely identify the feature sink, and must be included in the
#         # dictionary returned by the processAlgorithm function.
#         source = self.parameterAsSource(parameters, self.INPUT, context)
#         gdfO = gpd.GeoDataFrame.from_features(source.getFeatures())
        
#         # Retrieve the other parameters values
#         initiator_start = self.parameterAsSource(parameters, self.INITIATOR_START, context)
#         gdfS = gpd.GeoDataFrame.from_features(initiator_start.getFeatures())
#         gdfS = gdfS['geometry'][0]

#         initiator_end = self.parameterAsSource(parameters, self.INITIATOR_END, context)
#         gdfF = gpd.GeoDataFrame.from_features(initiator_end.getFeatures())
#         gdfF = gdfF['geometry'][0]

#         frozen = self.parameterAsSource(parameters, self.FROZEN, context)
#         if not frozen:
#             frozen=gpd.GeoDataFrame(geometry=[])

#         distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
#         interval = self.parameterAsDouble(parameters, self.INTERVAL, context)

#         # Actual algorithm
#         gdf_final = propagation_crow_flies (gdfO, initiator_start=gdfS,initiator_end=gdfF,frozen_objects=frozen,distance=distance,interval=interval)
#         res = gdf_final.to_dict('records')
#         res = list_to_qgis_feature_2(res, source.fields())
        
#         # Create the output sink    
#         (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
#                 context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
#         # Add a feature in the sink
#         sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
#         return {
#             self.OUTPUT: dest_id
#             }
    
class PropagationNetwork (QgsProcessingAlgorithm):
    
    """  
    Propagate a displacement along the network.

    This algorithm proposed by Lecordix et al. [1] propagate a geometry change inside a network along the whole network. The extremities of the network is always kept.

    Parameters:

            network (GeoDataFrame of LineString or List[LineString]) – The road network in which to propagate the change.

            index (int) – The index of the modified geometry.

            geometry (LineString) – The new modified geometry.

            propagation_distance (float, optional) – The maximum distance to limit the propagation. Lower value will modify more heavily closer lines.

            damping (float, optional) – The damping factor.

            tolerance (float, optional) – The tolerance to consider touching roads.

            inplace (bool, optional) – Whether to modify the GeoDataFrame in place.

    Returns:

        GeoDataFrame of LineString or List[LineString]
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    INDEX='INDEX'
    GEOMETRY='GEOMETRY'
    PROPAGATION_DISTANCE='PROPAGATION_DISTANCE'
    DAMPING='DAMPING'
    TOLERANCE='TOLERANCE'
    INPLACE='INPLACE'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Propagation Network'

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
        return 'Lines Displacement'

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        from cartagen4qgis import get_plugin_icon
        return get_plugin_icon()

    def shortDescription(self):
        """
        Returns an optional translated short description of the algorithm. This 
        should be at most a single sentence, e.g. “Converts 2D features to 3D by 
        sampling a DEM raster.”
        """
        first_line = self.shortHelpString().strip().splitlines()[0]
        description = self.tr(first_line)
        
        return(description)

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        helpstring = """
        Propagate a displacement along the network.
        This algorithm proposed by Lecordix et al. propagate a geometry change inside a network along the whole network. The extremities of the network is always kept.
        <h3> Parameters: </h3>
        <ul>
              <li> - <em>Index </em> :  The index of the modified geometry. </li>
              <li> - <em>Geometry </em> :  The new modified geometry. </li>
              <li> - <em>Propagation distance </em> :  The maximum distance to limit the propagation. Lower value will modify more heavily closer lines. </li>
              <li> - <em>Damping </em> :  The damping factor. </li>
              <li> - <em>Tolerance </em> :  The tolerance to consider touching roads. </li>
              <li> - <em>Inplace </em> :  Whether to modify the GeoDataFrame in place. </li>
        </ul>
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.propagation_network.html#cartagen.propagation_network">help online</a>.
            
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PropagationNetwork()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr(' The road network in which to propagate the change :'),
                [QgsProcessing.TypeVectorLine]
            )
        self.addParameter(input)
        
        index = QgsProcessingParameterNumber(
            self.INDEX,
            self.tr('Index :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=1,
            optional=False
        )
        self.addParameter(index)
            
        geometry = QgsProcessingParameterFeatureSource(
            name=self.GEOMETRY,
            description="Geometry :",
            types=[QgsProcessing.TypeVectorLine]
        )
        self.addParameter(geometry)
            
        propagation_distance = QgsProcessingParameterNumber(
            self.PROPAGATION_DISTANCE,
            self.tr('Propagation distance :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        propagation_distance.setFlags(propagation_distance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(propagation_distance)
        
        damping = QgsProcessingParameterNumber(
            self.DAMPING,
            self.tr('Damping :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.1,
            optional=False
        )
        damping.setFlags(damping.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(damping)
        
        tolerance = QgsProcessingParameterNumber(
            self.TOLERANCE,
            self.tr('Tolerance :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1e-06,
            optional=False
        )
        tolerance.setFlags(tolerance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(tolerance)
        
        inplace = QgsProcessingParameterBoolean(
            self.INPLACE,
            self.tr('Inplace ?'),
            defaultValue=False,
            optional=True
        )
        inplace.setFlags(inplace.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(inplace)
            
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Propagated Network'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import propagation_network
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values

        index = self.parameterAsInt(parameters, self.INDEX, context)
        geometry = self.parameterAsSource(parameters, self.GEOMETRY, context)
        gdfG = gpd.GeoDataFrame.from_features(geometry.getFeatures())
        gdfG = gdfG['geometry'][0]

        propagation_distance = self.parameterAsDouble(parameters, self.PROPAGATION_DISTANCE, context)
        if propagation_distance == 0:
            propagation_distance=None

        damping = self.parameterAsDouble(parameters, self.DAMPING, context)
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        inplace = self.parameterAsBoolean(parameters, self.INPLACE, context)

        # Actual algorithm
        gdf_final = propagation_network (gdf, index=index,geometry=gdfG,propagation_distance=propagation_distance,damping=damping,tolerance=tolerance,inplace=inplace)
        res = gdf_final.to_dict('records')
        res = list_to_qgis_feature_2(res, source.fields())
        
        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }