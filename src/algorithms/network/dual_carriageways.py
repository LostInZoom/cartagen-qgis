# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CartAGen4QGIS
                                 A QGIS plugin
 Cartographic generalization
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-06-18
        copyright            : (C) 2024 by Guillaume Touya, Justin Berli & Paul Bourcier
        email                : guillaume.touya@ign.fr
 ***************************************************************************/
"""

__author__ = 'Guillaume Touya, Justin Berli & Paul Bourcier'
__date__ = '2024-06-18'
__copyright__ = '(C) 2024 by Guillaume Touya, Justin Berli & Paul Bourcier'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsFields,
)
from qgis.utils import iface
from qgis.PyQt.QtCore import QVariant

from qgis.PyQt.QtWidgets import QMessageBox

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
    QgsProcessingParameterString,
    QgsProcessingParameterField
)

from cartagen.enrichment import detect_dual_carriageways
from cartagen import collapse_dual_carriageways

from cartagen4qgis import PLUGIN_ICON
from cartagen4qgis.src.tools import *

import geopandas

class DetectDualCarriageways(QgsProcessingAlgorithm):
    """
  Detect dual carriageways based on geometric properties.

    This algorithm proposed by Touya :footcite:p:`touya:2010`
    detects the network faces as road separator (*i.e.* separation between
    dual carriageways) when the polygon meets the geometric requirements.
    Those values can be tweaked to fine-tune the detection, but complex interchange will
    nonetheless cause wrong characterization.

    Parameters
    ----------
    roads : GeoDataFrame of LineString
        Road network to analyze.
    importance : str, optional
        The attribute name of the data on which road importance is based.
        Default value is set to None which means every road is taken for the network face calculation.
    value : int, optional
        Maximum value of the importance attribute.
        Roads with an importance higher than this value will not be taken.
    concavity : float, optional
        Maximum concavity.
    elongation : float, optional
        Minimum elongation.
    compactness : float, optional
        Maximum compactness.
    area : float, optional
        Area factor to detect very long motorways.
    width : float, optional
        Maximum width of the the :func:`minimum_rotated_rectangle <shapely.minimum_rotated_rectangle>`.
    huber : int, optional
        Huber width for long motorways.

    Notes
    -----
    - **concavity** is the area of the polygon divided by the area of its convex hull.
    - **elongation** is the length of the :func:`minimum_rotated_rectangle <shapely.minimum_rotated_rectangle>`
      divided by its width.
    - **compactness** is calculated using :math:`(4·pi·area)/(perimeter^2)`
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    IMPORTANCE = 'IMPORTANCE'
    VALUE = 'VALUE'
    CONCAVITY = 'CONCAVITY'
    ELONGATION = 'ELONGATION' 
    COMPACTNESS = 'COMPACTNESS'
    AREA = 'AREA'
    WIDTH = 'WIDTH'
    HUBER = 'HUBER' 

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DetectDualCarriageways()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Detect dual carriageways'

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
        return self.tr("Detect dual carriageways based on geometric properties.\nThis algorithm proposed by Touya detects the network faces as road separator (*i.e.* separation between dual carriageways) when the polygon meets the geometric requirements. Those values can be tweaked to fine-tune the detection, but complex interchange will nonetheless cause wrong characterization.\nImportance : the attribute name of the data on which road importance is based. Default value is set to None which means every road is taken for the network face calculation.\nValue : maximum value of the importance attribute. Roads with an importance higher than this value will not be taken.\nConcavity : maximum concavity. (concavity is the area of the polygon divided by the area of its convex hull)\nElongation : minimum elongation. (elongation is the length of the minimum rotated rectangle divided by its width)\nCompactness : maximum compactness. (compactness is calculated using (4*pi*area)/(perimeter^2))\nArea : area factor to detect very long motorways.\nWidth : maximum width of the the minimum rotated rectangle.\nHuber : Huber width for long motorways")
        
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

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input road network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
  		        
       	importance = QgsProcessingParameterString(
            self.IMPORTANCE,
            self.tr('Importance attribute name'),
            optional=True,
            defaultValue = 'None'
        )    
        importance.setFlags(importance.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(importance)	     
	

        value = QgsProcessingParameterNumber(
            self.VALUE,
            self.tr('Maximum value of the importance attribute'),
            type=QgsProcessingParameterNumber.Integer,
            optional=True,
            defaultValue = 99
        )
        value.setFlags(value.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(value)

        concavity = QgsProcessingParameterNumber(
            self.CONCAVITY,
            self.tr('Maximum concavity'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            defaultValue = 0.85
        )
        concavity.setFlags(concavity.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(concavity)

        elongation = QgsProcessingParameterNumber(
            self.ELONGATION,
            self.tr('Maximum elongation'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            defaultValue = 6
        )
        elongation.setFlags(elongation.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(elongation)

        compactness = QgsProcessingParameterNumber(
            self.COMPACTNESS,
            self.tr('Maximum compactness'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            defaultValue = 0.12
        )
        compactness.setFlags(compactness.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(compactness)

        area = QgsProcessingParameterNumber(
            self.AREA,
            self.tr('Area factor to detect very long motorways.'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            defaultValue = 60000
        )
        area.setFlags(area.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(area)

        width = QgsProcessingParameterNumber(
            self.WIDTH,
            self.tr('Maximum width of the minimum rotated rectangle'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            defaultValue = 20
        )
        width.setFlags(width.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(width)

        huber = QgsProcessingParameterNumber(
            self.HUBER,
            self.tr('Huber width for long motorways'),
            type=QgsProcessingParameterNumber.Integer,
            optional=True,
            defaultValue = 16
        )
        huber.setFlags(huber.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(huber)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Detected dual carriageways')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # Get the QGIS source from the parameters
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        #layer = QgsVectorLayer("Point", "temp", "memory")
        #pr = layer.dataProvider()
        #pr.addAttributes([QgsField("deadend", QVariant.Bool),
		  #QgsField("face",  QVariant.Int),
                  #QgsField("deid",  QVariant.Int),
                  #QgsField("connected", QVariant.Bool),
                  #QgsField("root", QVariant.Bool),
                  #QgsField("hole", QVariant.Bool)])
        #layer.updateFields()

		
        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = qgis_source_to_geodataframe(source)
        records = gdf.to_dict('records')
        count = len(records)

         # Compute the number of steps to display within the progress bar and
        total = 100.0 / count if count > 0 else 0
        
        # Retrieve parameters
        importance = self.parameterAsString(parameters, self.IMPORTANCE, context)
        value = self.parameterAsInt(parameters, self.VALUE, context)
        concavity = self.parameterAsDouble(parameters, self.CONCAVITY, context)
        elongation = self.parameterAsDouble(parameters, self.ELONGATION, context)
        compactness = self.parameterAsDouble(parameters, self.COMPACTNESS, context)
        area = self.parameterAsDouble(parameters, self.AREA, context)
        width = self.parameterAsDouble(parameters, self.WIDTH, context)
        huber = self.parameterAsInt(parameters, self.HUBER, context)

        if importance == 'None':
            importance = None
        if value == 99:
            value = None

        # Actual algorithm
        dc = detect_dual_carriageways(gdf, importance = importance, value = value, concavity = concavity,
        elongation = elongation, compactness = compactness, area = area, width = width, huber = huber)
        
        #try:
        dc = dc.to_dict('records')
            # gdf_final = gpd.GeoDataFrame(dc, crs = source.sourceCrs().authid())
            # layer_final = QgsVectorLayer(gdf_final.to_json())
        # except AttributeError:
        #     raise Exception("No dual cariageways detected, try changing parameters")
            # result = QgsFeature() 

            # dc = [{'area':None,'perimeter':None, 'concavity':None,'elongation':None,'compactness':None,'length':None,'width':None,'huber':None,'cid':None,'geometry':None}]
            # layer_final = QgsVectorLayer("Polygon","layer_final","memory")
            # pr = layer_final.dataProvider() # need to create a data provider
            # pr.addAttributes([QgsField("area",  QVariant.Double)]) # define/add field data type
            # pr.addAttributes([QgsField("perimeter",  QVariant.Double)])
            # pr.addAttributes([QgsField("concavity",  QVariant.Double)])
            # pr.addAttributes([QgsField("elongation",  QVariant.Double)])
            # pr.addAttributes([QgsField("compactness",  QVariant.Double)])
            # pr.addAttributes([QgsField("length",  QVariant.Double)])
            # pr.addAttributes([QgsField("width",  QVariant.Double)])
            # pr.addAttributes([QgsField("huber",  QVariant.Double)])
            # pr.addAttributes([QgsField("cid",  QVariant.Int)])
            # layer_final.updateFields() # tell the vector layer to fetch changes from the provider

        
        # # Créer une liste de QgsFeature
        # features = []
        # fields = layer_final.fields()

        # for entity in dc:
        #     feature = QgsFeature()
        #     feature.setFields(fields)
        #     feature.setAttribute('area', entity['area'])
        #     feature.setAttribute('perimeter', entity['perimeter'])
        #     feature.setAttribute('concavity', entity['concavity'])
        #     feature.setAttribute('elongation', entity['elongation'])
        #     feature.setAttribute('compactness', entity['compactness'])
        #     feature.setAttribute('length', entity['length'])
        #     feature.setAttribute('width', entity['width'])
        #     feature.setAttribute('huber', entity['huber'])
        #     feature.setAttribute('cid', entity['cid'])

        #     # Si votre entité a une géométrie (par exemple, des coordonnées x et y)
        #     geom = QgsGeometry.fromWkt(str(entity['geometry']))
        #     feature.setGeometry(geom)
                
        #     features.append(feature)
        
        if len(dc) == 0:
            fields = QgsFields()
            fields.append(QgsField("area", QVariant.Double))
            fields.append(QgsField("perimeter", QVariant.Double))
            fields.append(QgsField("concavity", QVariant.Double))
            fields.append(QgsField("elongation", QVariant.Double))
            fields.append(QgsField("compactness", QVariant.Double))
            fields.append(QgsField("length", QVariant.Double))
            fields.append(QgsField("width", QVariant.Double))
            fields.append(QgsField("huber", QVariant.Double))
            fields.append(QgsField("cid",  QVariant.Int))
            
            res = [QgsFeature(fields)]

            QMessageBox.warning(None, "Warning", "No dual carriageways detected, output layer is empty.")

        else:    
            gdf_final = gpd.GeoDataFrame(dc, crs = source.sourceCrs().authid())
            res = gdf_final.to_dict('records')
            res = list_to_qgis_feature(res)

        (sink, dest_id) = self.parameterAsSink(
                parameters, self.OUTPUT, context,
                fields=res[0].fields(),
                geometryType=QgsWkbTypes.Polygon,
                crs=source.sourceCrs()
            )
            
        sink.addFeatures(res, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT: dest_id
        }
        

class CollapseDualCarriageways(QgsProcessingAlgorithm):
    """
     Collapse dual carriageways using a TIN skeleton.

    This algorithm proposed by Thom :footcite:p:`thom:2005`
    collapses the network faces considered as dual carriageways
    using a skeleton calculated from a Delaunay triangulation.

    Parameters
    ----------
    roads : GeoDataFrame of LineString
        The road network.
    carriageways : GeoDataFrame of Polygon
        The polygons representing the faces of the network detected as dual carriageways.
    sigma : float, optional
        If not None, apply a gaussian smoothing to the collapsed dual carriageways to
        avoid jagged lines that can be created during the TIN skeleton creation.
    propagate_attributes : list of str, optional
        Propagate the provided list of column name to the resulting network.
        The propagated attribute is the one from the longest line.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_ROAD = 'INPUT_ROAD'
    INPUT_CARRIAGEWAYS = 'INPUT_CARRIAGEWAYS'
    SIGMA = 'SIGMA'
    PROPAGATE_ATTRIBUTES = 'PROPAGATE_ATTRIBUTES'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CollapseDualCarriageways()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Collapse dual carriageways'

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
        return self.tr("Collapse dual carriageways using a TIN skeleton.\nThis algorithm proposed by Thom collapses the network faces considered as dual carriageways using a skeleton calculated from a Delaunay triangulation.\nCarriageways : the polygons representing the faces of the network detected as dual carriageways.\nSigma : if not None, apply a gaussian smoothing to the collapsed dual carriageways to avoid jagged lines that can be created during the TIN skeleton creation.\nPropagate_attributes : propagate the provided list of column name to the resulting network. The propagated attribute is the one from the longest line.")
        
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
        input_road = QgsProcessingParameterFeatureSource(
                self.INPUT_ROAD,
                self.tr('Input road network'),
                [QgsProcessing.TypeVectorLine]
            )
        self.addParameter(input_road)

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_CARRIAGEWAYS,
                self.tr('Input dual carriageways'),
                [QgsProcessing.TypeVectorPolygon],
                optional=False
            )
        )          
                
       	sigma = QgsProcessingParameterNumber(
            self.SIGMA,
                self.tr('Sigma value'),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                defaultValue= 0
            )
        self.addParameter(sigma)	 

        self.addParameter(QgsProcessingParameterField(self.PROPAGATE_ATTRIBUTES,
            self.tr('Attributes to propagate'),
            None, 'INPUT_ROAD', QgsProcessingParameterField.Any, True, optional = True))

    

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

        (sink, dest_id) = self.parameterAsSink(
                parameters, self.OUTPUT, context,
                fields=source.fields(),
                geometryType=QgsWkbTypes.LineString,
                crs=source.sourceCrs()
            )
        # Convert the source to GeoDataFrame, get the list of records and the number of entities
        gdf = qgis_source_to_geodataframe(source)
        records = gdf.to_dict('records')
        count = len(records)
        
        gdf = geopandas.GeoDataFrame(records)
    
        # crs = source.sourceCrs().authid()

        # features = source.getFeatures()
        # f = []
        # for feature in features:
        #     entity = feature.__geo_interface__["properties"]
           
        #     entity['geometry'] = loads(feature.geometry().asWkt())
        #     f.append(entity)

        # gdf = geopandas.GeoDataFrame(f, crs=crs)
       

         # Compute the number of steps to display within the progress bar and
        total = 100.0 / count if count > 0 else 0
        
        dc = self.parameterAsSource(parameters, self.INPUT_CARRIAGEWAYS, context)
        dc = qgis_source_to_geodataframe(dc)

        sigma = self.parameterAsDouble(parameters, self.SIGMA, context)
        if sigma == 0:
            sigma = None
        attr =  self.parameterAsFields(parameters, self.PROPAGATE_ATTRIBUTES, context)
        
        cllpsed = collapse_dual_carriageways(gdf, dc, sigma=sigma, propagate_attributes=attr)
      

        try:
            cllpsed = cllpsed.to_dict('records')
            
            # for dico in cllpsed:
            #     for attr in dico.keys():
            #         if dico[attr] != dico[attr]:
            #             if not attr == 'fid': 
            #                 print("ici")
            #                 dico[attr] = QDateTime(1999, 9, 29, 19, 19, 19, 199)
            # print(type(cllpsed[0]['fid']))
            #gdf_final = gpd.GeoDataFrame(cllpsed, crs = source.sourceCrs().authid())
            #layer_final = QgsVectorLayer(gdf_final.to_json())
        except AttributeError:
            cllpsed = gdf.to_dict('records')
            #gdf_final = gpd.GeoDataFrame(cllpsed, crs = source.sourceCrs().authid())
            #layer_final = QgsVectorLayer(gdf_final.to_json())

    
        # Créer une liste de QgsFeature
        #features = []
        
        res = list_to_qgis_feature_2(cllpsed,source.fields())


        # for entity in cllpsed:
        #     feature = QgsFeature()
        #     feature.setFields(fields)
        #     for i in range(len(fields)):
        #         # if entity[fields[i].name()] != entity[fields[i].name()]:
        #         #     entity[fields[i].name()] = None
                
               
        #         #     except:
        #         #         entity[fields[i].name()] = True|feature.setAttribute(fields[i].name(), entity[fields[i].name()])    
        #         # # if isinstance(entity[fields[i].name()], QDateTime):
        #         #     if entity[fields[i].name()] == str('nan'):
        #         #         print('ici')
        #         #         entity[fields[i].name()] = 0 
                
        #         feature.setAttribute(fields[i].name(), entity[fields[i].name()])
            
        #     geom = QgsGeometry.fromWkt(str(entity['geometry']))
        #     feature.setGeometry(geom)
                
        #     features.append(feature)
            
        sink.addFeatures(res, QgsFeatureSink.FastInsert)       

        return {
            self.OUTPUT: dest_id
        }