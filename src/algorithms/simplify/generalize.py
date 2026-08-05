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

class GeneralizeAreaPatches (QgsProcessingAlgorithm):
    
    """   
    Generalise area patches using enlargement and contraction.

    This algorithm, proposed by Müller and Wang, simplifies area patches by enlarging or contracting them according to their relative size, then eliminating, reselecting, merging, displacing, and simplifying the survivors.

    This algorithm can be used for patches of vegetation for example, but also for islands, or any areal geographic entities.

    Parameters:

            polygons (GeoDataFrame of Polygon or MultiPolygon) – Input patches in projected coordinates (metres). MultiPolygon rows are supported and are reassembled after generalisation.

            scaling (float) – User-defined maximum blanket width in mm on the source map (= t* in eq. 2). Internally converted to ground units as scaling × 1e-3 × initial_scale.

            initial_scale (int) – Denominator of the source map scale (M_s). Default 25 000.

            final_scale (int) – Denominator of the target map scale (M_t). Default 50 000.

            level (int {1, 2, 3, 4}) – Radical-law selection model (I–IV in the paper). Lower values are more selective (fewer patches retained); higher values are less selective. The reselect loop may adjust this automatically.

            closeness (float or None) – Distance threshold in ground units. Patches closer than this value are subject to spatial constraints (see step 6). None disables the spatial-constraint step entirely.

            max_reselect_iterations (int) – Maximum number of reselect feedback iterations (default 5).

            area_tolerance (float) – Fractional tolerance on total patch area for the reselect loop (e.g. 0.05 = 5 %).

    Returns:

        GeoDataFrame – Generalised patches with Polygon or MultiPolygon geometries and an updated area column, in the same CRS as the input.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    SCALING='SCALING'
    INITIAL_SCALE='INITIAL_SCALE'
    FINAL_SCALE='FINAL_SCALE'
    LEVEL='LEVEL'
    CLOSENESS='CLOSENESS'
    MAX_RESELECT_ITERATIONS='MAX_RESELECT_ITERATIONS'
    AREA_TOLERANCE='AREA_TOLERANCE'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Generalize Area Patches'

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
        return 'Simplify lines and patches'

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
        Generalise area patches using enlargement and contraction.
        This algorithm, proposed by Müller and Wang, simplifies area patches by enlarging or contracting them according to their relative size, then eliminating, reselecting, merging, displacing, and simplifying the survivors.
        
        <b>MultiPolygon rows are supported and are reassembled after generalisation</b>
        <h3> Parameters: </h3>
        <ul>
              <li> - <em>Scaling </em> :  User-defined maximum blanket width in mm on the source map (= t* in eq. 2). Internally converted to ground units as scaling × 1e-3 × initial_scale. </li>
              <li> - <em>Initial scale </em> :  Denominator of the source map scale (M_s). Default 25 000. </li>
              <li> - <em>Final scale </em> :  Denominator of the target map scale (M_t). Default 50 000. </li>
              <li> - <em>Level </em> :  Radical-law selection model (I–IV in the paper). Lower values are more selective (fewer patches retained); higher values are less selective. The reselect loop may adjust this automatically. </li>
              <li> - <em>Closeness </em> :  Distance threshold in ground units. Patches closer than this value are subject to spatial constraints (see step 6). None disables the spatial-constraint step entirely. </li>
              <li> - <em>Max reselect iterations </em> :  Maximum number of reselect feedback iterations (default 5). </li>
              <li> - <em>Area tolerance </em> :  Fractional tolerance on total patch area for the reselect loop (e.g. 0.05 = 5 %). </li>
        </ul>
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.generalize_area_patches.html#cartagen.generalize_area_patchest">help online</a>.
            
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeneralizeAreaPatches()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr(' Input patches in projected coordinates (metres) :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        scaling = QgsProcessingParameterNumber(
            self.SCALING,
            self.tr('Scaling :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0,
            optional=False
        )
        self.addParameter(scaling)
        
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

        levels = ['1','2','3','4']
        level = QgsProcessingParameterEnum(
                self.LEVEL,
                self.tr('Level :'),
                levels,
                defaultValue=0
            )
        level.setFlags(level.flags() | QgsProcessingParameterDefinition.FlagAdvanced)        
        self.addParameter(level)            
            
        closeness = QgsProcessingParameterNumber(
            self.CLOSENESS,
            self.tr('Closeness :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=None,
            optional=True
        )        
        closeness.setFlags(closeness.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(closeness)
            
        max_reselect_iterations = QgsProcessingParameterNumber(
            self.MAX_RESELECT_ITERATIONS,
            self.tr('Max reselect iterations :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=5,
            optional=False
        )
        max_reselect_iterations.setFlags(max_reselect_iterations.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(max_reselect_iterations)
            
        area_tolerance = QgsProcessingParameterNumber(
            self.AREA_TOLERANCE,
            self.tr('Area tolerance :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.05,
            optional=False
        )        
        area_tolerance.setFlags(area_tolerance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(area_tolerance)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Generalized Area Patches'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import generalize_area_patches
        from cartagen4qgis.src.tools import list_to_qgis_feature

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values
        scaling = self.parameterAsDouble(parameters, self.SCALING, context)
        initial_scale = self.parameterAsInt(parameters, self.INITIAL_SCALE, context)
        final_scale = self.parameterAsInt(parameters, self.FINAL_SCALE, context)
        levels=[1,2,3,4]
        level = self.parameterAsEnum(parameters, self.LEVEL, context)
        closeness = self.parameterAsDouble(parameters, self.CLOSENESS, context)
        if closeness == 0:
            closeness=None
        max_reselect_iterations = self.parameterAsInt(parameters, self.MAX_RESELECT_ITERATIONS, context)
        area_tolerance = self.parameterAsDouble(parameters, self.AREA_TOLERANCE, context)

        # Actual algorithm
        gdf_final = generalize_area_patches (gdf, scaling=scaling,initial_scale=initial_scale,final_scale=final_scale,level=levels[level],closeness=closeness,max_reselect_iterations=max_reselect_iterations,area_tolerance=area_tolerance)
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