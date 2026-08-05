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

class BeamsDisplacement (QgsProcessingAlgorithm):
    """
            
    Displace lines using the elastic beams algorithm.

    This algorithm was proposed by Mats Bader during his PhD supervised by Mathieu Barrault and Robert Weibel. The algorithm models each polyline as an elastic beam and computes displacements based on internal beam forces and external proximity forces from other polylines. The forces are computed based on proximity between those line features.

    Parameters:

            lines (GeoDataFrame of LineString) – The lines to displace.

            distance (float) – The minimum distance that should separate each line in the output.

            E (float, optional) – Modulus of elasticity (material constant).

            A (float, optional) – Cross-sectional area of the beam.

            I (float, optional) – Moment of inertia of the beam.

            gamma (float, optional) – Time step / inertia factor.

            mu (float, optional) – Force multiplier.

            preserve_extremities (bool, optional) – Fix the first and last vertex of line if set to True.

            iterations (int, optional) – Number of iterations for convergence.

            verbose (bool, optional) – If True, prints iteration details.

    Returns:

        GeoDataFrame of LineString

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    DISTANCE='DISTANCE'
    E='E'
    A='A'
    I='I'
    GAMMA='GAMMA'
    MU='MU'
    PRESERVE_EXTREMITIES='PRESERVE_EXTREMITIES'
    ITERATIONS='ITERATIONS'
    VERBOSE='VERBOSE'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Beams Displacement'

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
        first_line = self.shortHelpString().strip().splitlines()[3]
        description = self.tr(first_line)
        
        return(description)

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        helpstring = """
        <b> /!\ Doesn't work with multipart geometry /!\ </b> 
        <b> /!\ Only process a couple lines at time /!\ </b> 
        
        Displace lines using the elastic beams algorithm.
        This algorithm was proposed by Mats Bader during his PhD supervised by Mathieu Barrault and Robert Weibel. The algorithm models each polyline as an elastic beam and computes displacements based on internal beam forces and external proximity forces from other polylines. The forces are computed based on proximity between those line features.
        
        <h3> Parameters: </h3>
        <ul>
            <li> - <em>Distance </em> :  The minimum distance that should separate each line in the output. </li>
            <li> - <em>E </em> :  Modulus of elasticity (material constant). </li>
            <li> - <em>A </em> :  Cross-sectional area of the beam. </li>
            <li> - <em>I </em> :  Moment of inertia of the beam. </li>
            <li> - <em>Gamma </em> :  Time step / inertia factor. </li>
            <li> - <em>Mu </em> :  Force multiplier. </li>
            <li> - <em>Preserve extremities </em> :  Fix the first and last vertex of line if set to True. </li>
            <li> - <em>Iterations </em> :  Number of iterations for convergence. </li>
            <li> - <em>Verbose </em> :  If True, prints iteration details. </li>
        </ul>
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.beams_displacement.html#cartagen.beams_displacement">help online</a>.
            
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BeamsDisplacement()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr(' The lines to displace :'),
                [QgsProcessing.TypeVectorLine]
            )
        self.addParameter(input)
        
        distance = QgsProcessingParameterNumber(
            self.DISTANCE,
            self.tr('Distance :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=50,
            optional=False
        )
        self.addParameter(distance)
        
        
        iterations = QgsProcessingParameterNumber(
            self.ITERATIONS,
            self.tr('Iterations :'),
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=100,
            optional=False
        )
        self.addParameter(iterations)

        a = QgsProcessingParameterNumber(
            self.A,
            self.tr('A :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional=False
        )
        a.setFlags(a.flags() | QgsProcessingParameterDefinition.FlagAdvanced)        
        self.addParameter(a)
        
        e = QgsProcessingParameterNumber(
            self.E,
            self.tr('E :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional=False
        )
        e.setFlags(e.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(e)

        i = QgsProcessingParameterNumber(
            self.I,
            self.tr('I :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional=False
        )
        i.setFlags(i.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(i)
        
        gamma = QgsProcessingParameterNumber(
            self.GAMMA,
            self.tr('Gamma :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.5,
            optional=False
        )
        gamma.setFlags(gamma.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(gamma)
        
        mu = QgsProcessingParameterNumber(
            self.MU,
            self.tr('Mu :'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.1,
            optional=False
        )
        mu.setFlags(mu.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(mu)
        
        preserve_extremities = QgsProcessingParameterBoolean(
            self.PRESERVE_EXTREMITIES,
            self.tr('Preserve extremities ?'),
            defaultValue=True,
            optional=False
        )
        preserve_extremities.setFlags(preserve_extremities.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(preserve_extremities)
            
            
        verbose = QgsProcessingParameterBoolean(
            self.VERBOSE,
            self.tr('Verbose ?'),
            defaultValue=True,
            optional=False
        )
        self.addParameter(verbose)
        verbose.setFlags(verbose.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Displaced Beams'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import beams_displacement
        from cartagen4qgis.src.tools import list_to_qgis_feature

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
        e = self.parameterAsDouble(parameters, self.E, context)
        a = self.parameterAsDouble(parameters, self.A, context)
        i = self.parameterAsDouble(parameters, self.I, context)
        gamma = self.parameterAsDouble(parameters, self.GAMMA, context)
        mu = self.parameterAsDouble(parameters, self.MU, context)
        preserve_extremities = self.parameterAsBoolean(parameters, self.PRESERVE_EXTREMITIES, context)
        iterations = self.parameterAsInt(parameters, self.ITERATIONS, context)
        verbose = self.parameterAsBoolean(parameters, self.VERBOSE, context)

        # Actual algorithm
        gdf_final = beams_displacement (gdf, distance=distance,E=e,A=a,I=i,gamma=gamma,mu=mu,preserve_extremities=preserve_extremities,iterations=iterations,verbose=verbose)
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