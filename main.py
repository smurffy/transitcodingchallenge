#!/usr/bin/python3
import argparse
from datetime import datetime
from getpass import getpass
import json
from mysql.connector import connect, Error
import pandas as pd
from pprint import pprint
import requests
import transitcodingchallenge.utils as utils


def main(user_name, password, host, port, db_name):
    startTime = datetime.now()
    api = utils.ApiUtils()
    sql = utils.SqlUtils(user_name=user_name,
                            password=password,
                            host=host,
                            port=port,
                            db_name=db_name)

    # Step 1 - Task 1: load lines API results into variable
    lines_json = api.getLines()

    # Step 1 - Task 2: load json into dataframe
    lines_df = sql.loadLinesDf(lines_json, ["line_name", "description"], 3)

    # Step 1 - Task3: load dataframe into MySQL
    sql.loadTableNoOverwrite(lines_df, "line_name", user_name, password, host, port, db_name)

    # Step 2 - Task1: load routes API results to variable (this contains all routes)
    routes_json = api.getRoutes()

    # Step 2 - Task2: load routes API results to dataframe
    routes_df=sql.loadRoutesDf(routes_json, ["route", "vehicle_id", "direction", "destination"], 0)

    # Step 2 - Task3: load dataframe into MySQL
    sql.loadTableAllowOverwrite(routes_df, "route", user_name, password, host, port, db_name)

    # Step 3 - Task1: for route stations, load the line metadata API results to a table
    stations = sql.getStations("route", user_name, password, host, port, db_name)
    line_metadata_df = sql.loadLineMetaDf(["line", "direction", "origin", "destination", "train_id"], stations)
    sql.loadTableAllowOverwrite(line_metadata_df, "line_metadata", user_name, password, host, port, db_name)

    # Let's end with printing some stuff so we can see the output of our hard work
    pd.set_option('display.max_columns', None)
    if not(lines_df.empty):
        print("------Top 5 rows in Lines DataFrame-----")
        print(lines_df.head(5))
    if not(routes_df.empty):
        print("------Top 5 rows in Routes DataFrame-----")
        print(routes_df.head(5))
    if not(line_metadata_df.empty):
        print("------Top 5 rows in Line Metadata DataFrame-----")
        print(line_metadata_df.head(5))

    print("\n##### Script Runtime for SEPTA Transit Coding Challenge - ", datetime.now() - startTime, "#####")

if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Runs through All Steps for Problem 1 of the Data Analyst Coding Challenge')
    parser.add_argument("-us", "--mysql_username", dest="user_name", help="Username for accessing MySQL Server", required=False)
    parser.add_argument("-pw", "--mysql_password", dest="password", help="Username for accessing MySQL Server", required=False)
    parser.add_argument("-ho", "--mysql_host", dest="host", help="Host Name for accessing MySQL Server", default="localhost")
    parser.add_argument("-po", "--mysql_port", dest="port", help="Host Name for accessing MySQL Server", default="3306")
    parser.add_argument("-db", "--mysql_database", dest="db_name", help="Database Name for accessing MySQL Server", default="septa_transit")
    args = parser.parse_args()

    if args.user_name is None:
        user = getpass("Enter MySQL username: ")
    else:
        user = args.user_name

    if args.password is None:
        pw = getpass("Enter MySQL password: ")
    else:
        pw = args.password

    main(user, pw, args.host, args.port, args.db_name)
