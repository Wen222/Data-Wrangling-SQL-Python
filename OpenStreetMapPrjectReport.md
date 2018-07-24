
# OpenStreetMap Data Case Study

### Map Area
Atlanta, GA, United States

- https://www.openstreetmap.org/relation/119557

Atlanta is my favorate city in the US. I'd like to take this opportunity to explore this area and contribute to its improvement on OpenStreetMap.org. The dataset was downloaded through openpass API, and the exported data cover the entire Atlanta area.  

## Problems Encountered in the Map
After initially downloading a small sample size of the Atlanta area and running it against a provisional data.py file, I noticed five main problems with the data, which I will discuss in the following order:

- Overabbreviated street names
- Inconsistent state names
- Inconsistent/incorrect postal codes
- Incorrect format of contact phone number
- Incorrect format of other contact information
- Incorrect city names ("Artlanta")
- Incorrect data type of housenumber 
- Inconsistent notations for housenumbers and building levels

### Overabbreviated Street Names
Once the sample data were saved as .csv files, some basic filtering and checking revealed street name abbreviations and postal code inconsistencies. To correct street names, I iterated over each word in an address, correcting them to their respective mappings using the following function:

```python
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
``` 

This updated all substrings in problematic address strings, such that:

"St Charles Ave NE" becomes:  <br \>
"St Charles Avenue Northeast."

The loop starts from index 1 to prevent substituting the first "St" with "Street" in the address. It also consider the case that an addresss starting with "N" or "S" so that these abbreviations can be cleaned.

### Postal Codes
Postal code strings have a different sort of problem. There are both incorrect (e.g., "300313") and inconsistent (e.g., "30329-3929", "GA 30307") postal codes. For more consistent queries, all leading and trailing characters before and after the main 5-digit zip code are trimmed using the following function.

```python
postcode_re = re.compile(r'30\d{3}', re.IGNORECASE)
def update_postcode(name):
    m = postcode_re.search(name)
    if m:
        new = m.group()
        name = new
    else:
        name = None
    return name
```

### Incorrect City Names
Auditing results of the city names shows that all the cities in the sample data are within the selected area. One typo of the city name was found: "Artlanta" should be "Atlanta." This has been corrected using similar update function as shown above.

### Inconsistent State Names
State names have the inconsistent problem. All the state names were standardized to "GA" using similar update function as above.

### House Numbers Standarization
Auditing results of house numbers show inconsistent format of the numbers, such as "308I", "783-1618", and "2325 #10." House numbers are normally integer numbers, so they were standardized to integer numbers using the following function:

```python

number_begin_re = re.compile(r'^[0-9]*', re.IGNORECASE)

def update_name(name):
    m = number_begin_re.search(name)
    new = m.group()
    name = new
    return name
```

A house number is audit by a all-number regular expression (r'^[0-9]*$'). Another regular experssion(r'^[0-9]*') was used to trim the leading all-number substring as the fixed house numbers.

## Data Overview and Additional Ideas
This section contains basic statistics about the dataset, the SQL queries used to gather them, and some additional ideas about the data in context.

### File sizes
```
map.osm ......... 558.6 MB 
Atlanta.db .......... 312.7 MB 
nodes.csv ............. 227.6 MB 
nodes_tags.csv ........ 4.3 MB 
ways.csv .............. 20.1 MB 
ways_tags.csv ......... 35.9 MB 
ways_nodes.cv ......... 63.4 MB
```

### Number of nodes
```
sqlite> SELECT COUNT(*) FROM nodes;
```
2340885

### Number of ways
```
sqlite> SELECT COUNT(*) FROM ways;
```
270119

### Number of unique users
```sql
sqlite> SELECT COUNT(DISTINCT(e.uid))          
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
```
1191

### Top 10 contributing users
```sql
sqlite> SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
GROUP BY e.user
ORDER BY num DESC
LIMIT 10;
```


```sql
Saikrishna_FultonCountyImport  1615997
Jack Kittle Buildings          226237
Liber                          154124
woodpeck_fixbot                132361
Jack the Ripper                92295
dygituljunky                   34586
DKNOTT                         33032
Ryan Lash                      27060
maven149                       24632
Rub21                          14746
```

## Additional Ideas

### Format of the User Input Data

In performing the data cleaning in the first part of this anlysis, I noticed that the type, or source of the map data are very diversified. For example, here are the top 10 types of data sources of ways:

```sql
addr         419488
regular      390754
tiger        169122
DeKalb       24088
LandPro08    22702
NHD          11987
building     1786
destination  1002
source       944
turn         921
```
The keys corresponding to each data source are quite different, and some values in the type field, such as building, source, turn, etc., seem not appropriate type values. I think it would be good idea to standardize the values of the input data to certain fields of the OpenStreetMap database, or at least make a given list of the values that can be used for the type and key fields. Doing this may reduce the flexibility of accepting new input data, but it would help improve the data quality and make it earier to use.

## Additional Data Exploration

### Top 10 appearing amenities

```sql
sqlite> SELECT value, COUNT(*) as num
FROM nodes_tags
WHERE key='amenity'
GROUP BY value
ORDER BY num DESC
LIMIT 10;
```

```sql
restaurant        569
school            424
place_of_worship  357
fast_food         219
bicycle_parking   211
bench             133
cafe              106
atm               104
fuel              104
fire_station      76
```

### Top 10 popular shops

```sql
sqlite> SELECT value, COUNT(*) as num
FROM nodes_tags
WHERE key='shop'
GROUP BY value
ORDER BY num DESC
LIMIT 10;
```
```sql
clothes       100
supermarket   72
hairdresser   56
convenience   53
beauty        39
car_repair    29
alcohol       26
shoes         23
mobile_phone  20
gift          18
```


### Most popular cuisines

```sql
sqlite> SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
    ON nodes_tags.id=i.id
WHERE nodes_tags.key='cuisine'
GROUP BY nodes_tags.value
ORDER BY num DESC;
```

```sql
american  55
pizza     43
mexican   41
sandwich  20
italian   18
chinese   17
burger    15
japanese  12
indian    10
sushi     9
```

## Conclusion
This review cleaned up most of the address data of the Metroplitan Atlanta area. Obviously, more clean up is needed for the entire data, but the address data have been well cleaned for the purpose of this project. I noticed the diversified data sources come with inconsistent values for data fields, which makes the data less clean and not efficient for practical use. I'd suggest standardizing the data format when the data are input to the OpenStreetMap system. 
