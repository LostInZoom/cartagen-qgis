import geopandas as gpd
from shapely.wkt import loads
from qgis.core import QgsFeature, QgsGeometry, QgsField, QgsFields
from qgis.PyQt.QtCore import QVariant, QDateTime, QDate

def qgis_source_to_geodataframe(source):
    """
    Converts a QGIS source to a geopandas GeoDataFrame.
    THIS CAUSES ISSUES WITH QGIS 
    """    
    features = source.getFeatures()
    f = []
    for feature in features:
        entity = { 'geometry': loads(feature.geometry().asWkt()) }
        fields = feature.fields()
        for field in fields:
            name = field.name()
            entity[name] = feature.attribute(name)
        f.append(entity)

    if len(f) > 0:
        return gpd.GeoDataFrame(f, crs=source.sourceCrs().authid())
    else:
        return None

def list_to_qgis_feature(dicts):
    """
    Converts a list of dicts with attributes and geometry to a list of qgis features.
    Can be heavy if there are a lot of keys and empty values in your dictionnary. If you are able to
    provide a QgsFeature.fields() object, consider using the list_to_qgis_feature_2 instead.
    """
    features = []
    field_list = []
    for j in range(len(dicts[0].keys())): #i.e for each key of your first dict
        if list(dicts[0].keys())[j] != 'geometry': #if the current key is not called 'geometry'
     
            if isinstance(dicts[0][list(dicts[0].keys())[j]], str):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.String))
                #if the first value of the key is a str, append the field list with the name of the key and the type Qvariant
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], int):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.LongLong))
                #same with int
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], float):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.Double))
                #same with float
            elif isinstance(dicts[0][list(dicts[0].keys())[j]], QDateTime):     
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.DateTime))
                #same with DateTime
            elif  isinstance(dicts[0][list(dicts[0].keys())[j]], QDate):
                field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.Date))
                #same with date
            
            else: #if none of those type are found (it can means that the value of the key has no value)
                count = 0
                try: #try to test the value type for the same key but it the next dict (i.e next feature)
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
                    #if none of those type are found again, append a Qvariant.String field
                    field_list.append(QgsField(list(dicts[0].keys())[j], QVariant.String))
              
        else: #don't append the field list if the key is "geometry"
            pass

    fields = QgsFields()
    for field in field_list: #append the fields from the field list into a QgsFields() object
        fields.append(field)

    for d in dicts: #for each dict from the list
        feature = QgsFeature() #create a QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(d['geometry'].wkt)) #append its geometry
        feature.setFields(fields) #apend its fields (name + type)
        for i in range(len(d.keys())): # for each key of the dict
            if list(d.keys())[i] != 'geometry': #if the key is not 'geometry"
                if d[list(d.keys())[i]] == d[list(d.keys())[i]]: #if the key value is not a NaN
                    feature.setAttribute(list(d.keys())[i], d[list(d.keys())[i]]) #append the value of the key to the feature
                else:
                    feature.setAttribute(list(d.keys())[i], None) #append a None
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
    """
    Converts a list of dicts with attributes and geometry to a list of qgis features. 
    Less heavy than the first function, it is useful when you can provide a QgsFeature.fields() objects
    """
    features = []
    for d in dicts: #for each dict of the list of dicts (i.e each feature)
        feature = QgsFeature() #create the QgsFeature() object
        feature.setFields(fields) #set its fields (name and types) thanks to the QgsFeature.fields() object
        for i in range(len(fields)): #for each field
            if d[fields[i].name()] == d[fields[i].name()]: #if the key value of the dict is not a NaN
                feature.setAttribute(fields[i].name(), d[fields[i].name()]) #append the feature with the value of the key
            else:
                feature.setAttribute(fields[i].name(), None) #else set None
        feature.setGeometry(QgsGeometry.fromWkt(d['geometry'].wkt))
        features.append(feature)  

    return features
