
# coding: utf-8

# In[35]:


import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import sys  
reload(sys)  
sys.setdefaultencoding('utf-8')

#import cerberus

#import schema

#OSM_PATH = "map_sample.osm"
OSM_PATH = "map.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = {
    'node': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'lat': {'required': True, 'type': 'float', 'coerce': float},
            'lon': {'required': True, 'type': 'float', 'coerce': float},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'node_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    },
    'way': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'way_nodes': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'node_id': {'required': True, 'type': 'integer', 'coerce': int},
                'position': {'required': True, 'type': 'integer', 'coerce': int}
            }
        }
    },
    'way_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    }
}


# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


expected_str = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Northeast","Northwest","Southwest","Southeast", "East","South","West","North",
            "Close", "Cove","Circle","Terrace","Way","Trace","Walk","Highway","View","Spring","Plaza","Bend"]
mapping_dir = { "N": "North",
                "E": "East",
                "S": "South",
                "W": "West",
                "N.": "North",
                "E.": "East",
                "S.": "South",
                "W.": "West",
               }
mapping_str = { "St ": "Street",
                "St.": "Street",
                "Ave": "Avenue",
                "Ave.": "Avenue",
                "Rd.": "Road",
                "Blvd": "Boulevard",
                "NE": "Northeast",
                "NorthEast": "Northeast",
                "NW": "Northwest",
                "NorthWest": "Northwest",
                "N.W.": "Northwest",
                "Pkwy": "Parkway",
                "Pl": "Place",
                "Rd": "Road",
                "RD": "Road",
                "Road,": "Road",
                "SE": "Southeast",
                "SE,": "Southeast",
                "S.E.": "Southeast",
                "SW": "Southwest",
                "SPG":"Spring",
                "St":"Street",
                "BLF":"Bluff",
                "dr":"Drive",
                "Dr":"Drive",
                "way":"Way",
                "Sq":"Square",
                "SHR":"Shore",
                "Ln":"Lane",
                "Hwy":"Highway",
                "Ct.":"Court",
                "BND":"Bend",
                "Av": "Avenue"
               }

street_audit = defaultdict(set)


expected_st = ["GA"]
mapping_st = { "Georgia": "GA",
               "ga":"GA"
             }


expected_city = ['Atlanta',
     'Avondale Estates',
     'Brookhaven',
     'Chamblee',
     'Clarkston',
     'Decatur',
     'Dekalb',
     'Doraville',
     'East Point',
     'Ellenwood',
     'Forest Park',
     'Hapeville',
     'Mableton',
     'Marietta',
     'Sandy Springs',
     'Scottdale',
     'Smyrna',
     'Stone Mountain',
     'Tucker',
     'Union City',
     'College Park',
     'Norcross',
     'Lake City',
     'Conley',
     'Sandersville'
    ]

mapping_city = { "Arlanta": "Atlanta",
                 "Atlanta, Georgia": "Atlanta",
                 "ATLANTA": "Atlanta",
                 "Atlanta GA": "Atlanta",
                 "atlanta": "Atlanta",
                 "decatur": "Decatur",
                 "Sandersville, GA": "Sandersville"
          }

city_audit = set()

def audit_street(street_name):
    update = False
    words = street_name.split()
    last = words[len(words)-1]
    if last not in expected_str:
        street_audit[last].add(street_name)
        update = True
    return update

def update_street(name):   
    words = name.split()
    if words[0] in mapping_dir:
        words[0]=mapping_dir[words[0]]
    for w in range(1,len(words)):
        if words[w] in mapping_str:            
            if words[w-1].lower() not in ['suite', 'ste.', 'ste']: 
                words[w] = mapping_str[words[w]] 
    name = " ".join(words)
    return name
    

def audit_state(state):
    update = False
    if state not in expected_st:
        update = True
    return update

def update_state(name):
    if name in mapping_st:
        name = mapping_st[name]
    return name

def audit_city(city):
    update = False
    if city not in expected_city:
        city_audit.add(city)
        update = True
    return update

def update_city(name):

    if name in mapping_city:
        name = mapping_city[name]
    return name

def audit_postcode(postal_code):
    update = False
    if len(postal_code)>5 or postal_code[:2] != '30':
        update = True
    return update

postcode_re = re.compile(r'30\d{3}', re.IGNORECASE)
def update_postcode(name):
    m = postcode_re.search(name)
    if m:
        new = m.group()
        name = new
    else:
        name = None
    return name

number_re = re.compile(r'^[0-9]*$', re.IGNORECASE)
def audit_housenumber(housenumber):
    #print housenumber
    update = False
    m = number_re.search(housenumber)
    if not m:
        update = True
    #print update
    return update

number_begin_re = re.compile(r'^[0-9]*', re.IGNORECASE)
def update_housenumber(name):
    m = number_begin_re.search(name)
    new = m.group()
    name = new
    return name


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    node_tag_attribs = {}
    way_attribs = {}
    way_nodes_attribs = {}
    way_tag_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    # YOUR CODE HERE
    #print node_attr_fields
    #print element.tag
    if element.tag == 'node':
        for field in node_attr_fields:
            
            if field == "id":
                value = int(element.attrib[field])
            elif field == "lat":
                value = float(element.attrib[field])
            elif field == "lon":
                value = float(element.attrib[field])
            elif field == "user":
                value = str(element.attrib[field])
            elif field == "uid":
                value = int(element.attrib[field])
            elif field == "version":
                value = int(element.attrib[field])
            elif field == "changeset":
                value = int(element.attrib[field])
            elif field == "timestamp":
                value = str(element.attrib[field])
                
            node_attribs[field] = value
            
        for x in element.iter("tag"):
            
            if problem_chars.search(x.attrib['k']):
               break
            
            node_tag_attribs['id']=node_attribs['id']
            
            if ":" in x.attrib['k']:
                pos = x.attrib['k'].find(":")
                node_tag_attribs['type']=x.attrib['k'][:pos]
                node_tag_attribs['key']=x.attrib['k'][(pos+1):]
                
            else:
                node_tag_attribs['type']=default_tag_type
                node_tag_attribs['key']=x.attrib['k']
            
            # Audit starts here and update follows
            updated_value = None
            if node_tag_attribs['type'] == "addr" and node_tag_attribs['key']=="street":
                update = audit_street(x.attrib['v'])
                if update:
                    updated_value = update_street(x.attrib['v'])
            if node_tag_attribs['type'] == "addr" and node_tag_attribs['key']=="state":
                update = audit_state(x.attrib['v'])
                if update:
                    updated_value = update_state(x.attrib['v'])
            if node_tag_attribs['type'] == "addr" and node_tag_attribs['key']=="city":
                update = audit_city(x.attrib['v'])
                if update:
                    updated_value = update_city(x.attrib['v'])
            if node_tag_attribs['type'] == "addr" and node_tag_attribs['key']=="postcode":
                update = audit_postcode(x.attrib['v'])
                if update:
                    updated_value = update_postcode(x.attrib['v'])
            if node_tag_attribs['type'] == "addr" and node_tag_attribs['key']=="housenumber":
                update = audit_housenumber(x.attrib['v'])
                if update:
                    updated_value = update_housenumber(x.attrib['v'])
                    
            if updated_value:
                node_tag_attribs['value']=updated_value
            else:
                node_tag_attribs['value']=x.attrib['v']
                
                  
            tags.append(node_tag_attribs.copy())
        
            
    if element.tag == 'way':
        for field in way_attr_fields:
            way_attribs[field] = element.attrib[field]
        for x in element.iter("tag"):
            #print 'way tag'
            if problem_chars.search(x.attrib['k']):
                break
            way_tag_attribs['id']=way_attribs['id']
            if ":" in x.attrib['k']:
                pos = x.attrib['k'].find(":")
                way_tag_attribs['type']=x.attrib['k'][:pos]
                way_tag_attribs['key']=x.attrib['k'][(pos+1):]
            else:
                way_tag_attribs['type']=default_tag_type
                way_tag_attribs['key']=x.attrib['k']
            
            # Audit starts here and update follows
            updated_value = None
            if way_tag_attribs['type'] == "addr" and way_tag_attribs['key']=="street":
                update = audit_street(x.attrib['v'])
                if update:
                    updated_value = update_street(x.attrib['v'])
            if way_tag_attribs['type'] == "addr" and way_tag_attribs['key']=="state":
                update = audit_state(x.attrib['v'])
                if update:
                    updated_value = update_state(x.attrib['v'])
            if way_tag_attribs['type'] == "addr" and way_tag_attribs['key']=="city":
                update = audit_city(x.attrib['v'])
                if update:
                    updated_value = update_city(x.attrib['v'])
            if way_tag_attribs['type'] == "addr" and way_tag_attribs['key']=="postcode":
                update = audit_postcode(x.attrib['v'])
                if update:
                    updated_value = update_postcode(x.attrib['v'])
            if way_tag_attribs['type'] == "addr" and way_tag_attribs['key']=="housenumber":
                update = audit_housenumber(x.attrib['v'])
                if update:
                    updated_value = update_housenumber(x.attrib['v'])
                
            if updated_value:
                way_tag_attribs['value']=updated_value
            else:
                way_tag_attribs['value']=x.attrib['v']
                
            tags.append(way_tag_attribs.copy())
        
        i = 0
        for x in element.iter("nd"):
            
            way_nodes_attribs['id']=way_attribs['id']
            way_nodes_attribs['node_id']=x.attrib['ref']
            way_nodes_attribs['position'] = i
            i += 1
            
            way_nodes.append(way_nodes_attribs.copy())
            
        
    
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        
#        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    #print el['node']
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
    #pprint.pprint(dict(street_audit))
    #print city_audit


# In[ ]:




