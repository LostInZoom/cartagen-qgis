import geopandas as gpd
from shapely.wkt import loads
from qgis.core import QgsFeature, QgsGeometry, QgsField, QgsFields
from qgis.PyQt.QtCore import QVariant,QDateTime, QDate

def qgis_source_to_geodataframe(source):
    """
    Converts a QGIS source to a geopandas GeoDataFrame.
    """
    crs = source.sourceCrs().authid()

    features = source.getFeatures()
    f = []
    for feature in features:
      
        try:
            entity = feature.__geo_interface__["properties"]
            entity['geometry'] = loads(feature.geometry().asWkt())
            f.append(entity)
        except NameError:
            pass
    if len(f) > 0: 
        gdf = gpd.GeoDataFrame(f, crs=crs)
    else:
        gdf = gpd.GeoDataFrame(columns=['geometry'], geometry='geometry')
    return gdf

def list_to_qgis_feature(dicts):
    """
    Converts a list of dicts with attributes and geometry to a list of qgis features.
    """
    # gdf = gpd.GeoDataFrame(dicts, crs)
    # return QgsVectorLayer(gdf.to_json())
    # print(type(dicts[0][list(dicts[0].keys())[36]]))
    # print(type(dicts[0][list(dicts[0].keys())[37]]))
    # print(dicts[0][list(dicts[0].keys())[38]])
    # print(dicts[0][list(dicts[0].keys())[39]])
    features = []
    field_list = []
    for j in range(len(dicts[0].keys())):
        if list(dicts[0].keys())[j] != 'geometry':
     
            if isinstance(dicts[0][list(dicts[0].keys())[j]], str):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.String))
                #print("ici5")
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], int):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.LongLong))
                #print("ici4")
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], float):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.Double))
                #print("ici3")
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], QDateTime):     
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.DateTime))
                #print("ici2")
            elif  isinstance(dicts[0][list(dicts[0].keys())[j]], QDate):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.Date))
                #print("ici1")
            
            else:
                count = 0
                try:
                    while not dicts[count][list(dicts[count].keys())[j]]:
                        count += 1
                        if isinstance(dicts[count][list(dicts[count].keys())[j]], str):
                            field_list.append(QgsField(list(dicts[count].keys())[j], QVariant.String))
                
                        elif isinstance(dicts[count][list(dicts[count].keys())[j]], int):
                            field_list.append(QgsField(list(dicts[count].keys())[j], QVariant.LongLong))
           
                        elif isinstance(dicts[count][list(dicts[count].keys())[j]], float):
                            field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.Double))
                            
                        elif isinstance(dicts[count][list(dicts[count].keys())[j]], QDateTime):                       
                            field_list.append(QgsField(list(dicts[count].keys())[j], QVariant.DateTime))
                
                        elif isinstance(dicts[count][list(dicts[count].keys())[j]], QDate):
                             field_list.append(QgsField(list(dicts[count].keys())[j], QVariant.Date))
                except IndexError:
                   
                    field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.String))
              
        else:
            pass

    fields = QgsFields()
    # Ajouter chaque QgsField à l'instance de QgsFields
    for field in field_list:
        fields.append(field)

    for d in dicts:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(d['geometry'].wkt))
        feature.setFields(fields)
        for i in range(len(d.keys())):
            if list(d.keys())[i] != 'geometry':
                if d[list(d.keys())[i]] == d[list(d.keys())[i]]:
                    feature.setAttribute(list(d.keys())[i], d[list(d.keys())[i]])
                else:
                    feature.setAttribute(list(d.keys())[i], None)
        features.append(feature)

    return features

def qgis_source_to_geodataframe_2(source):
    """ 
    Converts a QGIS source to a geopandas GeoDataFrame and keep attributes.
    """
    crs = source.sourceCrs().authid()

    features = source.getFeatures()
    f = []
    for feature in features:
        entity = {}
        entity['geometry'] = loads(feature.geometry().asWkt())
        
        
        for field in feature.fields():
            entity[field.name()] = feature[field.name()]
            
        f.append(entity)
    gdf = gpd.GeoDataFrame(f, crs=crs)
    print(gdf.nature)
    return gdf
  
def list_to_qgis_feature_2(dicts,fields):
    features = []
    for d in dicts:
        feature = QgsFeature()
        feature.setFields(fields)
        for i in range(len(fields)):
            if d[fields[i].name()] == d[fields[i].name()]:
                feature.setAttribute(fields[i].name(), d[fields[i].name()])
            else:
                feature.setAttribute(fields[i].name(), None)
        feature.setGeometry(QgsGeometry.fromWkt(d['geometry'].wkt))
        features.append(feature)  

    return features
