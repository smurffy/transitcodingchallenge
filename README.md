<b>Options on How to Run:</b><br>
```
    sudo python3 setup.py install
    
    sudo python3 main.py   ( you will be prompted for a mysql user name and password )
    
    sudo python3 main.py -ho <host> -po <port> -db <database name>
    
    sudo python3 main.py -ho <host> -po <port> -db <database name> -us <myusername> -pw <mypassword>
```

<b>If you run into myconnection or mysql.connector Errors:</b><br>

```
    Must have MySQL installed
    1. Go to URL : https://dev.mysql.com/downloads/mysql/
    2. Download the DMG file for your operating system
    2.Open DMG file and walk through the prompt to install
```

<b>Coding Challenge Submission by Steph Murphy:</b><br>
This directory is designed to have the main.py script solve the prompt for Part 1 of the Coding Challenge<br>

<b>How it works:</b><br>
If you'd like to use an already existing function (can be found in the teslacodingchallenge folder) you first need to initiate the classes you find in utils.py, and then you can call the function(s):
```
    import transitcodingchallenge.utils as utils

    api = utils.ApiUtils()
    sql = utils.SqlUtils(user_name=user_name,<
                            password=password,
                            host=host,
                            port=port,
                            db_name=db_name))
```
<b>Basic functions of note:</b><br>

getLines<br>
- Used the python requests library to make a call to the API endpoint. Formatted the json response using json.loads() <br>

loadLinesDf<br>
- Parsed the line json to the expected format. Used python pandas to load json into a dataframe row by row. Removed top n rows according to function input<br>

loadTableNoOverwrite<br>
- Checks if table name exists. Does nothing if table exists. Otherwise creates a table and loads the dataframe into the MySQL table
(used for line data)<br>

getRoutes<br>
- Used the python requests library to make a call to the API endpoint. Formatted the json response using json.loads(). Wrapped in a function called getLines()<br>

loadRoutesDf<br>
- Used parsed the route json to anticipated format for pandas. Used python pandas to load json into a dataframe row by row. Removed top n rows according to function intput<br>

loadTableAllowOverwrite<br>
- Checks if table name exists. If so, it drops table, creates a new one, and loads the dataframe into the MySQL table. Other wise creates a table and loads the dataframe into the MySQL table (used for route data and line metadata data)<br>

getStations<br>
- Reads the route table created in MySQL. Selects description column and parses column using pattern matching to generate the regional station name key. Outputs a list of regional station names.<br>

loadLineMetaDf<br>
- For each station name, calls the line metadata API to get the arrival information. Returns None if station information is not found by API. For Stations found by API, parses line metadata json and loads the data into a pandas dataframe for each arrival found. If no station names from the getStations list are returned, the routes table is refreshed, a new getStations list is generated, line metadata then attempts to load into a df again <br>

<b>First Thoughts on Part 2 of the Coding Challenge:</b><br>
Have Data Updating Follow a cycle of,<br>
-Ingest: base data<br>
-Reconcile: changed data<br>
-Compact: base data and change data (new base data table)<br>
-Purge: replace base data with new base data table<br>
-(Cycle back to Ingest)<br>
<br>
Data would require indexing and more robust timestamp information. modified time, and maybe deleted_time. With regards to script time management, it takes time to purge and ingest. During this time will allow reconcile table to continue aggregate the queue of changed records while other steps in cycle are running.<br>

Keys to consider for indexes,<br>
- (routes) VehicleIDNumber, RouteNumber#VehicleIDNum, Regional Station Name<br>
- (line metadata) station name, train_id<br>
- ..needs more research

<b>General Process Improvements:</b><br>
- Pattern for parsing the Regional Station Name from the route description needs to be more robust in order to capture more station name strings<br>
- Consider using connection pooling to speed up changes submitted to MySQL<br>
- It would be useful to have more timestamp information available for incremental updates<br>
  (could store a timestamp from when I pull info or use a timestamp from the API)<br>

<b>Closing Remarks,</b><br>
Thanks for providing me with this Coding Challenge.<br>
Best, Steph Murphy<br>
