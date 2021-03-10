#!/usr/bin/python3
import json
from mysql.connector import connect, Error
import pandas as pd
from pprint import pprint
import requests


class ApiUtils():

    def getApiResponse(self, request_url):
        """Sends the GET request to and API that does not require headers.
        request_url is url for API endpoint
        Returns API response formatted as JSON """
        response = requests.get(request_url)
        if response.status_code == 200:
            response_json = json.loads(response.content)
            return response_json

    def getLines(self):
        """ Step 1 - Task 1: Call the lines API endpoint
        and Load the API response into a variable """
        request_url = "https://www.septastats.com/api/current/lines"
        api_response = self.getApiResponse(request_url)
        return api_response

    def getRoutes(self):
        """ Step 2 - Task 1: Call the routes API endpoint
        and Load the API response into a variable """
        request_url = "http://www3.septa.org/hackathon/TransitViewAll/"
        api_response = self.getApiResponse(request_url)
        return api_response

    def getLineMetadata(self, station, n = None):
        """ Step 3 - Task 1: Call the current lines metadata (arrivals) API endpoint
        and Load the response into a variable
        station is the Regional Station name where the trains are arriving
        n is an integer that allows us to get the next n sequential trains that arrive at the station"""
        if n is None:
            #get all arrivals
            request_url = "http://www3.septa.org/hackathon/Arrivals/{}/".format(station,n)
            api_response = self.getApiResponse(request_url)
        else:
            #get n number of arrivals
            request_url = "http://www3.septa.org/hackathon/Arrivals/{}/{}/".format(station,n)
            api_response = self.getApiResponse(request_url)
        return api_response

class SqlUtils():
    def __init__(self, user_name, password, host, port, db_name):
        """ Assumes src dest are nodes and weight is a number """
        self.user_name = user_name
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name

    def loadLinesDf(self, json_data, headers, n):
        """ Step 1 - TASK 2: Loads line json into dataframe (df).
        json_data is expected to the lines_json
        headers is a list of strings defining the column headers for the df
        n is an integer defining the number of rows that should be removed from the df"""
        #load json line data into dataframe
        df = pd.DataFrame(columns = headers)
        for k in json_data.keys():
            if type(json_data[k]) is dict:
                newdf = pd.DataFrame.from_records([[k, ""]], columns = headers)
                df = df.append(newdf,  ignore_index = True)
        for k in json_data.keys():
            if type(json_data[k]) is dict:
                new_json = json_data[k]
                for k in new_json:
                    newdf = pd.DataFrame.from_records([[k, new_json[k]]], columns = headers)
                    df = df.append(newdf,  ignore_index = True)

        #remove top n rows from dataframe
        for idx in range(0,n):
            df = df.drop(index=idx)
        return df

    def loadRoutesDf(self, json_data, headers, n):
        """ Step 2 - TASK 2: Loads route json into dataframe (df).
        json_data is expected to the routes_json
        headers is a list of strings defining the column headers for the df
        n is an integer defining the number of rows that should be removed from the df """
        #load json data into dataframe
        df = pd.DataFrame(columns = headers)
        for route_dict in json_data["routes"]:
            for key in route_dict.keys():
                route_id = key
                #step 2 - task 1 cont.
                route_segments = route_dict[route_id]
                for route_segment in route_segments:
                    vehicle_id = route_segment.get("VehicleID")
                    direction = route_segment.get("Direction")
                    destination = route_segment.get("destination")
                    #step 2 - task 2
                    newdf = pd.DataFrame.from_records([[route_id, vehicle_id, direction, destination]], \
                                columns = headers)
                    df = df.append(newdf,  ignore_index = True)

        #remove n top rows from dataframe
        for idx in range(0,n):
            df = df.drop(index=idx)
        return df

    def loadLineMetaDf(self, column_headers, stations, rec_counter = 1):
        """For each station name, calls the line metadata API to get the arrival information.
        Returns None if station information is not found by API. For Stations found by API,
        parses line metadata json and loads the data into a pandas dataframe for each arrival found.
        If no station names from the getStations list are returned, the routes table is refreshed,
        a new getStations list is generated, line metadata then attempts to load into a df again"""
        api = ApiUtils()
        #create lines metadata dataframe
        df = pd.DataFrame(columns = column_headers)

        if rec_counter > 3:
            print("Cannot find any Regional Station names in Line Metadata Feed. Tried 3 times.")
            return df
        #for each station name, make API call
        for station in stations:
            line_metadata_json = api.getLineMetadata(station)
            #pprint(line_metadata_json)

            #load API response into Pandas
            if line_metadata_json is not None:
                for key in line_metadata_json.keys():
                    full_station_info = line_metadata_json[key]
                    if full_station_info == [[], []]:
                        #break look for if empty station info is returned
                        break
                    for direction in full_station_info:
                        for directional in direction:
                            directional_arrivals = direction[directional]
                            for arrival in directional_arrivals:
                                line = station
                                direction = directional
                                origin = arrival.get("origin")
                                destination = arrival.get("destination")
                                train_id = arrival.get("train_id")
                                newdf = pd.DataFrame.from_records([[line, direction, origin, destination, train_id]],\
                                            columns = column_headers)
                                df = df.append(newdf,  ignore_index = True)

#         #if lines metadata is completely empty. grab routes data again
        if df.empty:
            routes_json = api.getRoutes()
            routes_df = self.loadRoutesDf(routes_json, ["route", "vehicle_id", "direction", "destination" ], 0)
            self.loadTableAllowOverwrite(routes_df, "route", self.user_name, self.password, self.host, self.port, self.db_name)
            stations = self.getStations("route", self.user_name, self.password, self.host, self.port, self.db_name)
            return self.loadLineMetaDf(column_headers, stations, rec_counter+1 )
        else:
            return df
        return df

    def createDatabase(self, user_name, password, host, port, db_name):
        """ Checks to see if the database name exists for a given MySQL connection.
        If the database name does not exist, a new database is created with that name"""
        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password
            )
        except Error as e:
            print(e)

        #load all database names into cursor
        mycursor = myconnection.cursor()
        mycursor.execute("SHOW DATABASES")

        db_exists = False

        #determine if database name already exists
        for found_db in mycursor:
            #note: db_name prints as tuple, ('septa_transit',)
            if db_name in found_db:
                db_exists = True
                break
                mycursor.close()
                return

        #if database name is not found, make database
        if not(db_exists):
            execute_string = "CREATE DATABASE IF NOT EXISTS {}".format(db_name)
            mycursor.execute(execute_string)
            mycursor.close()
            return

    def tableExists(self, table_name, user_name, password, host, port, db_name):
        """ Determine if the table exists in the database.
        Returns Boolean. True is table_name is found. False table_name not found"""
        #ensure the database exists, if not makes a database
        #TODO: enhance to fail if db_name is not found
        self.createDatabase(user_name, password, host, port, db_name)
        #start by assuming the table name does not exist
        table_exists = False
        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password,
                database=db_name
            )
        except Error as e:
            print(e)

        #load all table names into cursor
        mycursor = myconnection.cursor()
        mycursor.execute("SHOW TABLES")

        #determine if table name already exists
        for found_table in mycursor:
            #each table name prints as tuple, ('line_name',)
            if table_name in found_table:
                table_exists = True
                break
                mycursor.close()

        return table_exists
        
    def createTableStatement(self, table_name, column_headers):
        """ Generates the string needed to execute a MySQL CREATE TABLE statement.
            column_headers is a list. Each column header is loaded into the table as a BLOB datatype.
            BLOB in MySQL provides the same amount of storage as Microsoft's VARCHAR(MAX)
        """
        if len(column_headers) == 1:
            create_table = "CREATE TABLE IF NOT EXISTS {} ({} BLOB )".format(table_name, header[0])
        else: 
            string_list = []
            string_start = "CREATE TABLE IF NOT EXISTS {} (".format(table_name)
            string_list.append(string_start)
            string_end = ")"
            for i in range(len(column_headers)):

                header_string = " {} BLOB,".format(column_headers[i])
                if i == len(column_headers)-1:
                    header_string = header_string[:-1]
                string_list.append(header_string)

            string_list.append(string_end)

            create_table = ''.join(string_list)
        return create_table

    def createTable(self, dataframe, table_name, user_name, password, host, port, db_name):
        """ Creates a table using the given table_name in the MySQL connection provided.
        dataframe is expected to be a pandas df.
        All parameters are required. No defaults are set.
        """
        #ensure the database exists, if not makes a database
        self.createDatabase(user_name, password, host, port, db_name)

        column_headers = dataframe.columns.tolist()

        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password,
                database=db_name
            ) 
        except Error as e:
            print(e)

        #initiate cursor
        mycursor = myconnection.cursor()

        #execute create table statement
        create_table_statement = self.createTableStatement(table_name, column_headers)
        mycursor.execute(create_table_statement)
        mycursor.close()

        return
        
    def readTable(self, table_name, user_name, password, host, port, db_name, select_statement = None, toPrint = True):
        """ Connects to MySQL and outputs the table to enable reading in terminal """

        if select_statement is None:
            select_statement = "SELECT * FROM `" + table_name + "`"
        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password,
                database=db_name
            ) 
        except Error as e:
            print(e)

        #initiate cursor
        mycursor = myconnection.cursor()

        mycursor.execute(select_statement)
        # read all table records
        result = mycursor.fetchall()
        if toPrint:
            for i in result:
                print(i)

        mycursor.close()
        return result

    def dropTable(self, table_name, user_name, password, host, port, db_name):
        """ Drops the table name in the MySQL connection provided. """
        #ensure the database exists
        self.createDatabase(user_name, password, host, port, db_name)

        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password,
                database=db_name
            ) 
        except Error as e:
            print(e)

        #initiate cursor
        mycursor = myconnection.cursor()
        #execute drop table statement
        execute_string = "DROP TABLE {}".format(table_name)
        mycursor.execute(execute_string)
        mycursor.close()
        return

    def insertIntoTable(self, dataframe, table_name, user_name, password, host, port, db_name):
        """ Inserts rows from Pandas DF into the table name in the MySQL connection provided. """
        #connect to MySQL server
        try:
            myconnection = connect(
                host=host,
                port=port,
                user=user_name,
                password=password,
                database=db_name
            ) 
        except Error as e:
            print(e)

        #initiate cursor
        mycursor = myconnection.cursor()

        # creating column list for inserting into table
        cols = "`,`".join([str(i) for i in dataframe.columns.tolist()])

        for i, row in dataframe.iterrows():
            #make insert statement string for inserting into table
            insert_into = "INSERT INTO `" + table_name + "` (`" + cols + "`) VALUES (" + "%s," *(len(row)-1) + "%s)"
            #insert each row into the table
            mycursor.execute(insert_into, tuple(row)) 
            #commit changes. the connection is not autocommitted by default. must commit to save changes
            myconnection.commit()

        mycursor.close()
        return

    def loadTableNoOverwrite(self, dataframe, table_name, user_name, password, host, port, db_name):
        """ Checks if the table exists.
        If the table exists - No action is taken. This function does not allow overwriting tables.
        If the table does not exist - A table is created, data is inserted into the new table from the df"""
        table_exists = self.tableExists(table_name, user_name, password, host, port, db_name)
        if not(table_exists):
            self.createTable(dataframe, table_name, user_name, password, host, port, db_name)
            self.insertIntoTable(dataframe, table_name, user_name, password, host, port, db_name)
        return

    def loadTableAllowOverwrite(self, dataframe, table_name, user_name, password, host, port, db_name):
        """ Checks if the table exists.
        If the table exists. The table is dropped, a new one is created, data is inserted into the table from the df .
        If the table does not exist - A table is created, data is inserted into the new table from the df"""
        table_exists = self.tableExists(table_name, user_name, password, host, port, db_name)
        if table_exists:
            self.dropTable(table_name, user_name, password, host, port, db_name)
            self.createTable(dataframe, table_name, user_name, password, host, port, db_name)
            self.insertIntoTable(dataframe, table_name, user_name, password, host, port, db_name)
        if not(table_exists):
            self.createTable(dataframe, table_name, user_name, password, host, port, db_name)
            self.insertIntoTable(dataframe, table_name, user_name, password, host, port, db_name)
        return

    def getStations(self, table_name, user_name, password, host, port, db_name):
        """ Reads the route table created in MySQL. Selects description column and
        parses column using pattern matching to generate the regional station name key.
        Outputs a list of regional station names"""
        stations = []
        select_statement = "SELECT destination FROM `" + table_name + "`"
        destinations = self.readTable(table_name, user_name, password, host, port, db_name, select_statement, False)
        for destination in destinations:
            #TODO: should we also split station names with " Transit"? maybe splittin on " Trans" is best.
            station_name = destination[0].decode("utf-8").split(" Transportation")[0]
            if station_name not in stations:
                stations.append(station_name)
        return stations

