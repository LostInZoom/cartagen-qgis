from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm,
    QgsFeature, QgsGeometry, QgsProcessingParameterDefinition,
    QgsProcessingException, QgsWkbTypes,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
    QgsProcessingParameterField
)    

class TypifyMatching (QgsProcessingAlgorithm):
    """   
    Typify buildings using the matching-based algorithm for web mapping.

    This algorithm was proposed by Li et al. and replace tight groups of buildings with a single representative building.

    The algorithm follows three main steps: First, it finds the number of buildings using improved radical law. Second, it calculates the position and representation through iterative merging. Finally, building sizes are harmonized.

    Parameters:

            buildings (GeoDataFrame of Polygon or MultiPolygon) – The buildings to typify

            initial_scale (int, optional) – Source map scale denominator (default: 25000)

            final_scale (int, optional) – Target map scale denominator (default: 50000)

            ratio (float, optional) – Ratio between source and target number of buildings (e.g., 0.5 to reduce by half) If None, will be computed from initial_scale and final_scale

            road_network (GeoDataFrame of LineString, optional) – Road network for spatial partitioning. If None, simple grid partitioning is used

            attributes (List[str], optional) – List of attribute names to transfer from largest building in each cluster

            distance (float, optional) – Minimum separate distance for building harmonization (in map units)

    Returns:

        GeoDataFrame of Polygon or MultiPolygon – Typified buildings with transferred attributes
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    INITIAL_SCALE='INITIAL_SCALE'
    FINAL_SCALE='FINAL_SCALE'
    RATIO='RATIO'
    ROAD_NETWORK='ROAD_NETWORK'
    ATTRIBUTES='ATTRIBUTES'
    DISTANCE='DISTANCE'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Typify Matching'

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
        Typify buildings using the matching-based algorithm for web mapping.
        This algorithm was proposed by Li et al. and replace tight groups of buildings with a single representative building.
        <h3> Parameters: </h3>
        <ul>
          <li> - <em>Initial scale </em> :  Source map scale denominator (default: 25000) </li>
          <li> - <em>Final scale </em> :  Target map scale denominator (default: 50000) </li>
          <li> - <em>Ratio </em> :  Ratio between source and target number of buildings (e.g., 0.5 to reduce by half) If None, will be computed from initial_scale and final_scale </li>
          <li> - <em>Road network </em> :  Road network for spatial partitioning. If None, simple grid partitioning is used </li>
          <li> - <em>Attributes </em> :  List of attribute names to transfer from largest building in each cluster </li>
          <li> - <em>Distance </em> :  Minimum separate distance for building harmonization (in map units) </li>
        </ul>
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.typify_buildings_matching.html#cartagen.typify_buildings_matching">help online</a>.
            
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TypifyMatching()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The buildings to typify :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        initial_scale = QgsProcessingParameterNumber(
            self.INITIAL_SCALE,
            self.tr('Initial scale :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=25000,
            optional=False
        )
        self.addParameter(initial_scale)
            
        final_scale = QgsProcessingParameterNumber(
            self.FINAL_SCALE,
            self.tr('Final scale :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=50000,
            optional=False
        )
        self.addParameter(final_scale)
            
        ratio = QgsProcessingParameterNumber(
            self.RATIO,
            self.tr('Ratio :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        ratio.setFlags(ratio.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(ratio)
        
        road_network = QgsProcessingParameterFeatureSource(
            name=self.ROAD_NETWORK,
            description="Road network :",
            types=[QgsProcessing.TypeVectorLine],
            optional=True
        )
        road_network.setFlags(road_network.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(road_network)
            
        attribute = QgsProcessingParameterField(
            self.ATTRIBUTES,
            self.tr('Attributes to propagate :'),
            None, 
            'INPUT', 
            QgsProcessingParameterField.Any,
            True,
            optional = True
        )
        attribute.setFlags(attribute.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(attribute)
            
        distance = QgsProcessingParameterNumber(
            self.DISTANCE,
            self.tr('Distance :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=20.0,
            optional=False
        )
        distance.setFlags(distance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(distance)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Typified Matching'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import typify_buildings_matching
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values
        initial_scale = self.parameterAsInt(parameters, self.INITIAL_SCALE, context)
        final_scale = self.parameterAsInt(parameters, self.FINAL_SCALE, context)
        ratio = self.parameterAsDouble(parameters, self.RATIO, context)
        road_network = self.parameterAsSource(parameters, self.ROAD_NETWORK, context)
        attributes = self.parameterAsFields(parameters, self.ATTRIBUTES, context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
        
        # Actual algorithm
        gdf_final = typify_buildings_matching(gdf, initial_scale=initial_scale, final_scale=final_scale, ratio=ratio, road_network=road_network, attributes=attributes, distance=distance)
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
    
class TypifyBurghardtCecconi (QgsProcessingAlgorithm):

    """
            
    Typify buildings using the Burghardt-Cecconi algorithm.

    This algorithm was proposed by Burghardt & Cecconi [1] and progressively merges pairs of buildings by collapsing the shortest edge of a constrained Delaunay triangulation built on building centroids, until the target number of buildings is reached and all remaining neighbours are separated by at least the minimum legible distance at the target scale.

    The algorithm follows four main steps:

        Pre-generalisation - buildings smaller than an elimination threshold are removed; buildings smaller than the minimum representable area at the target scale are enlarged via homothety.

        Constrained triangulation - a Delaunay triangulation is built on building centroids; edges that cross roads are removed; each edge carries two weights: a density-weighted score used for ordering merges, and the raw geometric distance used for the separation stop criterion.

        Iterative typification - the shortest density-weighted edge is repeatedly collapsed: the two adjacent buildings are replaced by a new representative building whose position is the area-weighted barycentre of the merged group and whose shape is derived from the smallest surrounding rectangle of the largest constituent building, scaled to the average area of the group.

        Attribute transfer - selected attributes are copied from the largest building in each merged group to the representative building.

    Parameters:

            buildings (GeoDataFrame of Polygon or MultiPolygon) – Input buildings to typify. Each row must have a valid polygon geometry.

            initial_scale (int, optional) – Denominator of the source map scale (default: 25 000).

            final_scale (int, optional) – Denominator of the target map scale (default: 50 000).

            ratio (float, optional) – Explicit reduction ratio for the number of buildings (e.g. 0.5 halves the count). When supplied, initial_scale and final_scale are ignored for the target-count calculation. Must be in (0, 1].

            road_network (GeoDataFrame of LineString, optional) – Road network used to remove triangulation edges that cross roads. When None, no road-based edge filtering is applied.

            attributes (list of str, optional) – Column names to transfer from the largest building in each merged group to the output representative building. Columns absent from buildings are silently ignored.

            min_area (float, optional) – Minimum building footprint area in ground units squared (e.g. m² for a metric CRS). Buildings below this threshold are enlarged by homothety. When None, defaults to (0.2 mm * final_scale/1000)^2, i.e. the ground area corresponding to a 0.04 mm² symbol at the target scale. Set to 0 to disable enlargement.

            elimination_area (float, optional) – Buildings whose area is strictly below this value are deleted before typification starts. When None, defaults to (0.1 mm * final_scale/1000)^2, i.e. truly sub-pixel footprints. Set to 0 to disable elimination entirely.

            min_separation (float, optional) – Minimum desired separation between neighbouring building footprints in ground units. Typification continues until all remaining triangulation raw distances exceed this value, in addition to the target-count criterion. When None, defaults to 0.2 mm * final_scale/1000.

            density_weighting (bool, optional) – When True (default), edges are ordered by sqrt(local_density) * distance so that buildings in dense clusters are merged first. The raw geometric distance is always used for the stop criterion regardless of this flag.

    Returns:

        GeoDataFrame of Polygon – Typified buildings. The result contains:

            geometry - representative polygon at the target scale;

            all columns listed in attributes (values from the largest constituent building in each merged group);

            n_merged - number of original buildings merged into this representative.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    INITIAL_SCALE='INITIAL_SCALE'
    FINAL_SCALE='FINAL_SCALE'
    RATIO='RATIO'
    ROAD_NETWORK='ROAD_NETWORK'
    ATTRIBUTES='ATTRIBUTES'
    MIN_AREA='MIN_AREA'
    ELIMINATION_AREA='ELIMINATION_AREA'
    MIN_SEPARATION='MIN_SEPARATION'
    DENSITY_WEIGHTING='DENSITY_WEIGHTING'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Typify Burghardt Cecconi'

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
        Typify buildings using the Burghardt-Cecconi algorithm.
        This algorithm was proposed by Burghardt & Cecconi [1] and progressively merges pairs of buildings by collapsing the shortest edge of a constrained Delaunay triangulation built on building centroids, until the target number of buildings is reached and all remaining neighbours are separated by at least the minimum legible distance at the target scale. The algorithm follows four main steps: Pre-generalisation - buildings smaller than an elimination threshold are removed; buildings smaller than the minimum representable area at the target scale are enlarged via homothety. Constrained triangulation - a Delaunay triangulation is built on building centroids; edges that cross roads are removed; each edge carries two weights: a density-weighted score used for ordering merges, and the raw geometric distance used for the separation stop criterion. Iterative typification - the shortest density-weighted edge is repeatedly collapsed: the two adjacent buildings are replaced by a new representative building whose position is the area-weighted barycentre of the merged group and whose shape is derived from the smallest surrounding rectangle of the largest constituent building, scaled to the average area of the group.
        <h3> Parameters: </h3>
        <ul>
          <li> - <em>Initial scale </em> :  Denominator of the source map scale (default: 25 000). </li>
          <li> - <em>Final scale </em> :  Denominator of the target map scale (default: 50 000). </li>
          <li> - <em>Ratio </em> :  Explicit reduction ratio for the number of buildings (e.g. 0.5 halves the count). When supplied, initial_scale and final_scale are ignored for the target-count calculation. Must be in (0, 1]. </li>
          <li> - <em>Road network </em> :  Road network used to remove triangulation edges that cross roads. When None, no road-based edge filtering is applied. </li>
          <li> - <em>Attributes </em> :  Column names to transfer from the largest building in each merged group to the output representative building. Columns absent from buildings are silently ignored. </li>
          <li> - <em>Min area </em> :  Minimum building footprint area in ground units squared (e.g. m² for a metric CRS). Buildings below this threshold are enlarged by homothety. When None, defaults to (0.2 mm * final_scale/1000)^2, i.e. the ground area corresponding to a 0.04 mm² symbol at the target scale. Set to 0 to disable enlargement. </li>
          <li> - <em>Elimination area </em> :  Buildings whose area is strictly below this value are deleted before typification starts. When None, defaults to (0.1 mm * final_scale/1000)^2, i.e. truly sub-pixel footprints. Set to 0 to disable elimination entirely. </li>
          <li> - <em>Min separation </em> :  Minimum desired separation between neighbouring building footprints in ground units. Typification continues until all remaining triangulation raw distances exceed this value, in addition to the target-count criterion. When None, defaults to 0.2 mm * final_scale/1000. </li>
          <li> - <em>Density weighting </em> :  When True (default), edges are ordered by sqrt(local_density) * distance so that buildings in dense clusters are merged first. The raw geometric distance is always used for the stop criterion regardless of this flag. </li>
        </ul>
        
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.typify_buildings_burghardt_cecconi.html#cartagen.typify_buildings_burghardt_cecconi">help online</a>.
            
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TypifyBurghardtCecconi()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr(' Input buildings to typify Each row must have a valid polygon geometry :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        initial_scale = QgsProcessingParameterNumber(
            self.INITIAL_SCALE,
            self.tr('Initial scale :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=25000,
            optional=False
        )
        self.addParameter(initial_scale)
            
        final_scale = QgsProcessingParameterNumber(
            self.FINAL_SCALE,
            self.tr('Final scale :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=50000,
            optional=False
        )
        self.addParameter(final_scale)
            
        ratio = QgsProcessingParameterNumber(
            self.RATIO,
            self.tr('Ratio :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        ratio.setFlags(ratio.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(ratio)
        
        road_network = QgsProcessingParameterFeatureSource(
            name=self.ROAD_NETWORK,
            description="Road network :",
            types=[QgsProcessing.TypeVectorLine],
            optional=True
        )
        road_network.setFlags(road_network.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(road_network)
            
        attributes = QgsProcessingParameterField(
            self.ATTRIBUTES,
            self.tr('Attributes to propagate :'),
            None, 
            'INPUT', 
            QgsProcessingParameterField.Any,
            True,
            optional = True
        )
        attributes.setFlags(attributes.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(attributes)
            
        min_area = QgsProcessingParameterNumber(
            self.MIN_AREA,
            self.tr('Min area :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        min_area.setFlags(min_area.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(min_area)
        
        elimination_area = QgsProcessingParameterNumber(
            self.ELIMINATION_AREA,
            self.tr('Elimination area :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        elimination_area.setFlags(elimination_area.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(elimination_area)
        
        min_separation = QgsProcessingParameterNumber(
            self.MIN_SEPARATION,
            self.tr('Min separation :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )
        min_separation.setFlags(min_separation.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(min_separation)
        
        density_weighting = QgsProcessingParameterBoolean(
            self.DENSITY_WEIGHTING,
            self.tr('Density weighting ?'),
            defaultValue=True,
            optional=False
        )
        density_weighting.setFlags(density_weighting.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(density_weighting)
            
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Typified Burghardt-Cecconi'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import typify_buildings_burghardt_cecconi
        from cartagen4qgis.src.tools import list_to_qgis_feature

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values

        initial_scale = self.parameterAsInt(parameters, self.INITIAL_SCALE, context)
        final_scale = self.parameterAsInt(parameters, self.FINAL_SCALE, context)
        ratio = self.parameterAsDouble(parameters, self.RATIO, context)
        if ratio == 0.0 :
            ratio = None
        road_network = self.parameterAsSource(parameters, self.ROAD_NETWORK, context)
        attributes = self.parameterAsSource(parameters, self.ATTRIBUTES, context)
        min_area = self.parameterAsDouble(parameters, self.MIN_AREA, context)
        elimination_area = self.parameterAsDouble(parameters, self.ELIMINATION_AREA, context)
        min_separation = self.parameterAsDouble(parameters, self.MIN_SEPARATION, context)
        density_weighting = self.parameterAsBoolean(parameters, self.DENSITY_WEIGHTING, context)

        # Actual algorithm
        gdf_final = typify_buildings_burghardt_cecconi (gdf, initial_scale=initial_scale,final_scale=final_scale,ratio=ratio,road_network=road_network,attributes=attributes,min_area=min_area,elimination_area=elimination_area,min_separation=min_separation,density_weighting=density_weighting)
        res = gdf_final.to_dict('records')
        res = list_to_qgis_feature(res)

        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }