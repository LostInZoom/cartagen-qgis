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

class MakePlanar (QgsProcessingAlgorithm):
    
    """          
    Make the network planar and keep the relationship between sections.

    This function fully merges the input network and reconstruct a planar network, i.e, a network having its edges intersect only at their endpoints. As an example, a road network will lose its tunnels and bridges as topological features and merging lanes will split the main road it merges into.

    This function is also suitable for river networks as it preserves the direction of the LineStrings.

    Parameters:

        network (GeoDataFrame of LineString) – The network to make planar.
    Returns:

        GeoDataFrame of LineString
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Make Network Planar'

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
        return 'Tools'

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
        first_line = self.shortHelpString().strip().splitlines()[2]
        description = self.tr(first_line)
        
        return(description)

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        helpstring = """
        <b>/!\Doesn't work with multipart geometry/!\</b>

        Make the network planar and keep the relationship between sections.
        This function fully merges the input network and reconstruct a planar network, i.e, a network having its edges intersect only at their endpoints. As an example, a road network will lose its tunnels and bridges as topological features and merging lanes will split the main road it merges into. This function is also suitable for river networks as it preserves the direction of the LineStrings.
        
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.make_planar.html#cartagen.make_planar">help online</a>.
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MakePlanar()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The network to make planar :'),
                [QgsProcessing.TypeVectorLine]
            )
        self.addParameter(input)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Network made planar'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import geopandas as gpd
        import pandas
        from cartagen import make_planar
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Actual algorithm
        gdf_final = make_planar (gdf)
        res = gdf_final.to_dict('records')
        for i in res:
            print(f"i.{i}")

        res = list_to_qgis_feature_2(res, source.fields())
        
        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }