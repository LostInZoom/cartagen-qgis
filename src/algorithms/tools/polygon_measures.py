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

class PolygonElongation (QgsProcessingAlgorithm):
    
    """                
    Calculate the elongation of a polygon.

    This function calculates the elongation of a polygon using the minimum_rotated_rectangle. It is the ratio between the length and the width of this rectangle.

    Parameters:

        polygon (Polygon) – The polygon to calculated the elongation from.
    Returns:

        float

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
        return 'Polygon Elongation'

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
        <b> /!\ Doesn't work with multipart geometry /!\ </b>

        Calculate the elongation of a polygon.
        This function calculates the elongation of a polygon using the minimum_rotated_rectangle. It is the ratio between the length and the width of this rectangle.

        Results are displayed in the attribute table.
        
        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.polygon_elongation.html#cartagen.polygon_elongation">help online</a>.
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonElongation()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The polygon to calculate the elongation from :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Polygons with Elongation'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        import geopandas as gpd
        import pandas
        from cartagen import polygon_elongation
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        # Define the fields (get the source fields and a add some fields)
        fields = source.fields()
        fields.append(QgsField("ELONGATION", QVariant.Double))

        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        # Actual algorithm
        dp = gdf.copy()
        for i in range(len(gdf)):
            dp.loc[i,'ELONGATION'] = polygon_elongation(list(gdf.geometry)[i])

            # Update the progress bar
            feedback.setProgress(int(i * total))
        
        res = dp.to_dict('records')
        res = list_to_qgis_feature_2(res, fields)

        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }
    
class PolygonCompactness (QgsProcessingAlgorithm):
    
    """          
    Calculate the compactness of a polygon.

    This function calculates the compactness of a polygon using the Miller index. This index gives a maximum value of 1 for circles.

    The Miller index is calculated using
    (4 ·pi ·area)/(perimeter^2)

    Parameters:

        polygon (Polygon) – The polygon to calculated the compactness from.
    Returns:

        float

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
        return 'Polygon Compactness'

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
        <b> /!\ Doesn't work with multipart geometry /!\ </b>

        Calculate the compactness of a polygon.
        This function calculates the compactness of a polygon using the Miller index. This index gives a maximum value of 1 for circles. The Miller index is calculated using (4 ·pi ·area)/(perimeter^2)
        
        Results are displayed in the attribute table.

        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.polygon_compactness.html#cartagen.polygon_compactness">help online</a>.  
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonCompactness()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The polygon to calculated the compactness from :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Polygons with Compactness'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        import geopandas as gpd
        import pandas
        from cartagen import polygon_compactness
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        # Define the fields (get the source fields and a add some fields)
        fields = source.fields()
        fields.append(QgsField("COMPACTNESS", QVariant.Double))

        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        # Actual algorithm
        dp = gdf.copy()
        for i in range(len(gdf)):
            dp.loc[i,'COMPACTNESS'] = polygon_compactness(list(gdf.geometry)[i])

            # Update the progress bar
            feedback.setProgress(int(i * total))
        
        res = dp.to_dict('records')
        res = list_to_qgis_feature_2(res, fields)
        
        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }

class PolygonConcavity (QgsProcessingAlgorithm):
    
    """   
    Calculate the concavity of a polygon.

    This function calculates the concavity of a polygon as its area divided by the area of its convex hull.

    Parameters:

        polygon (Polygon) – The polygon to calculated the concavity from.
    Returns:

        float

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
        return 'Polygon Concavity'

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
        <b> /!\ Doesn't work with multipart geometry /!\ </b>

        Calculate the concavity of a polygon.
        This function calculates the concavity of a polygon as its area divided by the area of its convex hull.
        
        Results are displayed in the attribute table.

        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.polygon_concavity.html#cartagen.polygon_concavity">help online</a>.    
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonConcavity()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The polygon to calculated the concavity from :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Polygons with Concavity'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        import geopandas as gpd
        import pandas
        from cartagen import polygon_concavity
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)

        # Define the fields (get the source fields and a add some fields)
        fields = source.fields()
        fields.append(QgsField("CONCAVITY", QVariant.Double))

        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0

        # Actual algorithm
        dp = gdf.copy()
        for i in range(len(gdf)):
            dp.loc[i,'CONCAVITY'] = polygon_concavity(list(gdf.geometry)[i])

            # Update the progress bar
            feedback.setProgress(int(i * total))
        
        res = dp.to_dict('records')
        res = list_to_qgis_feature_2(res, fields)
        
        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }
    
class PolygonOrientation (QgsProcessingAlgorithm):
    
    """         
    Calculate the orientation of a polygon.

    This function calculates the orientation of a polygon using different methods. By default, it uses the orientation of the long side of the minimum bounding rectangle.

    Parameters:

            polygon (Polygon) – The polygon to calculate the orientation from.

            method (str, optional) –

            The method to calculate the orientation:

                ’primary’ calculates the orientation of the longest side of the provided polygon.

                ’mbr’ calculates the orientation of the long side of the minimum rotated bounding rectangle.

                ’mbtr’ calculates the orientation of the long side of the minimum rotated bounding touching rectangle. It is the same as the mbr but the rectangle and the polygon must have at least one side in common.

                ’swo’ or statistical weighted orientation described in Duchêne, [1] calculates the orientation of a polygon using the statistical weighted orientation. This method relies on the length and orientation of the longest and second longest segment between two vertexes of the polygon.

    Returns:

        float

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT='OUTPUT'
    INPUT='INPUT'
    METHOD='METHOD'

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Polygon Orientation'

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
        <b> /!\ Doesn't work with multipart geometry /!\ </b>

        Calculate the orientation of a polygon.
        This function calculates the orientation of a polygon using different methods. By default, it uses the orientation of the long side of the minimum bounding rectangle. Parameters: The method to calculate the orientation: ’primary’ calculates the orientation of the longest side of the provided polygon. ’mbr’ calculates the orientation of the long side of the minimum rotated bounding rectangle. ’mbtr’ calculates the orientation of the long side of the minimum rotated bounding touching rectangle. It is the same as the mbr but the rectangle and the polygon must have at least one side in common.
        
        Results are displayed in the attribute table.

        <h3> Parameters: </h3>
        <ul>
                <li> - <em>Method </em> : The method to calculate the orientation: </li>
                <ul>
                    <li>. ’primary’ calculates the orientation of the longest side of the provided polygon.</li>

                    <li>. ’mbr’ calculates the orientation of the long side of the minimum rotated bounding rectangle.</li>

                    <li>. ’mbtr’ calculates the orientation of the long side of the minimum rotated bounding touching rectangle. It is the same as the mbr but the rectangle and the polygon must have at least one side in common.</li>

                    <li>. ’swo’ or statistical weighted orientation described in Duchêne, calculates the orientation of a polygon using the statistical weighted orientation. This method relies on the length and orientation of the longest and second longest segment between two vertexes of the polygon.</li>
                </ul>
        </ul>

        For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.polygon_orientation.html#cartagen.polygon_orientation">help online</a>.
        """
        
        return self.tr(helpstring)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonOrientation()

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        # We add the input vector features source.
        input = QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('The polygon to calculate the orientation from :'),
                [QgsProcessing.TypeVectorPolygon]
            )
        self.addParameter(input)
        
        methods = ['primary', 'mbr', 'mbtr', 'swo']
        method = QgsProcessingParameterEnum(
                self.METHOD,
                self.tr('Method :'),
                methods,
                defaultValue = "primary"
            )
        self.addParameter(method)
                
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).   
        output = QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Polygons with Orientation'))
        self.addParameter(output)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        import geopandas as gpd
        import pandas
        from cartagen import polygon_orientation
        from cartagen4qgis.src.tools import list_to_qgis_feature_2

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Define the fields (get the source fields and a add some fields)
        fields = source.fields()
        fields.append(QgsField("ORIENTATION", QVariant.Double))

        gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
        
        # Retrieve the other parameters values

        methods = ['primary', 'mbr', 'mbtr', 'swo']
        method = self.parameterAsEnum(parameters, self.METHOD, context)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        # Actual algorithm
        dp = gdf.copy()
        for i in range(len(gdf)):
            dp.loc[i,'ORIENTATION'] = polygon_orientation (list(gdf.geometry)[i], method=methods[method])

            # Update the progress bar
            feedback.setProgress(int(i * total))

        res = dp.to_dict('records')
        res = list_to_qgis_feature_2(res,fields)
        
        # Create the output sink    
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, res[0].fields(), source.wkbType(), source.sourceCrs())
        
        # Add a feature in the sink
        sink.addFeatures(res, QgsFeatureSink.FastInsert)
        
        return {
            self.OUTPUT: dest_id
            }