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

# class InflexionPoints (QgsProcessingAlgorithm):
    
#     """    
#     Detect inflexion points inside a curved line.

#     This algorithm extract inflexion points from a line using angles calculation. Micro inflexions are removed.

#     Parameters:

#             line (LineString) – The line to extract the inflexion points from.

#             min_dir (float, optional) – The minimum direction change (in degrees) between two consecutive inflexion points. This parameter allows to remove micro inflexions from the results. If set to 0, every micro-inflexions will be kept.

#     Returns:

#         list of int – A list of index of the line vertices considered to be inflexion points
#     """

#     # Constants used to refer to parameters and outputs. They will be
#     # used when calling the algorithm from another algorithm, or when
#     # calling from the QGIS console.

#     OUTPUT='OUTPUT'
#     INPUT='INPUT'
#     MIN_DIR='MIN_DIR'

#     def name(self):
#         """
#         Returns the algorithm name, used for identifying the algorithm. This
#         string should be fixed for the algorithm, and must not be localised.
#         The name should be unique within each provider. Names should contain
#         lowercase alphanumeric characters only and no spaces or other
#         formatting characters.
#         """
#         return 'Inflexion Points'

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
#         return 'Tools'

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
#         <b>/!\Doesn't work with multipart geometry/!\</b>

#         Detect inflexion points inside a curved line.

#         <h3> Parameters: </h3>
#         <ul>
#               <li> - <em>Mininimum directionn </em> :  The minimum direction change (in degrees) between two consecutive inflexion points. This parameter allows to remove micro inflexions from the results. If set to 0, every micro-inflexions will be kept. </li>
#         </ul>
#         For more see <a href="https://cartagen.readthedocs.io/en/latest/reference/cartagen.inflexion_points.html#cartagen.inflexion_points">help online</a>.
            
#         """
        
#         return self.tr(helpstring)
    
#     def tr(self, string):
#         return QCoreApplication.translate('Processing', string)

#     def createInstance(self):
#         return InflexionPoints()

#     def initAlgorithm(self, config):
#         """
#         Here we define the inputs and output of the algorithm, along
#         with some other properties.
#         """
                
#         # We add the input vector features source.
#         input = QgsProcessingParameterFeatureSource(
#                 self.INPUT,
#                 self.tr('The line to extract the inflexion points from :'),
#                 [QgsProcessing.TypeVectorLine]
#             )
#         self.addParameter(input)
        
#         min_dir = QgsProcessingParameterNumber(
#             self.MIN_DIR,
#             self.tr('Mininimum direction :'),
#             type=QgsProcessingParameterNumber.Double,
#             defaultValue=120,
#             optional=False
#         )
#         self.addParameter(min_dir)
        
#         # We add a feature sink in which to store our processed features (this
#         # usually takes the form of a newly created vector layer when the
#         # algorithm is run in QGIS).   
#         output = QgsProcessingParameterFeatureSink(
#                 self.OUTPUT,
#                 self.tr('Line with inflexion points'))
#         self.addParameter(output)

#     def processAlgorithm(self, parameters, context, feedback):
#         """
#         Here is where the processing itself takes place.
#         """
#         from shapely import Point
#         import geopandas as gpd
#         import pandas
#         from cartagen import inflexion_points

#         # Retrieve the feature source and sink. The 'dest_id' variable is used
#         # to uniquely identify the feature sink, and must be included in the
#         # dictionary returned by the processAlgorithm function.
#         source = self.parameterAsSource(parameters, self.INPUT, context)
#         gdf = gpd.GeoDataFrame.from_features(source.getFeatures())
#         fields = source.fields()
        
#         # Retrieve the other parameters values
#         min_dir = self.parameterAsDouble(parameters, self.MIN_DIR, context)

#         # Compute the number of steps to display within the progress bar and
#         # get features from source
#         total = 100.0 / source.featureCount() if source.featureCount() else 0
#         features = source.getFeatures()    
        
#         # Actual algorithm
#         inflexionPoints = []
#         for i in range(len(gdf)):
#             inflexionPoint = inflexion_points(list(gdf.geometry)[i], min_dir=min_dir)
#             inflexionPoints.append(inflexionPoint)

#             # Update the progress bar
#             feedback.setProgress(int(i * total))

#         #How to have the inflexion points from the lines 
#         listRes = []
#         for i, ligne in enumerate(inflexionPoints):
#             listeItem = []
#             print(f"ligne : {ligne}")
#             for point in ligne:
#                 print(f"point :{point}")
#                 listeItem.append(point.item())
#             pointsLignes =[]
#             for numero, point in enumerate(list(gdf.geometry)[i].coords):
#                 if numero in listeItem:
#                     point = Point(point)
#                     pointsLignes.append(point)
#             pointsLignes = gpd.GeoSeries(pointsLignes)
#             pointsLignes = pointsLignes.to_dict()
#             listRes.append(pointsLignes)
        
#         #Creation of the layer
#         geometries = []
#         for i in range(0, len(listRes)):
#             for dic in listRes:
#                 for point in dic:
#                     geometry = dic[point]
#                     feature = QgsFeature() #create the QgsFeature() object
#                     feature.setFields(fields) #set its fields (name and types) thanks to the QgsFeature.fields() object
#                     feature.setGeometry(QgsGeometry.fromWkt(geometry.wkt))
#                     geometries.append(feature)
#                     print(f"geometries :{geometries}")
        
#         # Create the output sink    
#         (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
#                 context, fields, QgsWkbTypes.Point, source.sourceCrs())
        
#         # Add a feature in the sink
#         sink.addFeatures(geometries, QgsFeatureSink.FastInsert)
        
#         return {
#             self.OUTPUT: dest_id
#             }