import os
from uuid import uuid1 as uid
import datetime
from pathlib import Path
from dotenv import dotenv_values
from collections import OrderedDict
from csv import DictReader
from datetime import datetime as dt

import pandas as pd
from influxdb_client import WritePrecision, InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, PointSettings, WriteOptions, ASYNCHRONOUS

config = dotenv_values(".env")
token = config["INFLUXDB_TOKEN"]
org = "libra"
url = "http://eu-west-a1.libramli.ai:8086"
bucket="influx"

def send_data(field_value1, field_value2, timestamps, metadata):

	with InfluxDBClient(url=url, token=token, org=org) as client:
	
		measurement, video_name, type_timestamp = metadata
		field1, field2 = measurement.split("-")
		# print(field1, field2)
		write_api = client.write_api(write_options=SYNCHRONOUS)
		for index, timestamp in enumerate(timestamps):
			# print(type(timestamp))
			if type_timestamp == "datetime":
				timestamp_obj = dt.strptime(f"{timestamp}", '%Y-%m-%d %H:%M:%S.%f')
				# print(timestamp_obj)
				timestamp = int(timestamp_obj.timestamp() * 1000) # To ms
				# print(timestamp)
	
					# .tag(f"videoName", f"{dt.now().strftime('%Y-%m-%d')}") \
			point = Point(f"{measurement}") \
					.tag(f"videoName", f"{video_name}") \
					.field(f"id", f"{str(uid())}") \
					.field(f"{field1}", float(field_value1[index])) \
					.field(f"{field2}", float(field_value2[index])) \
					.time(int(timestamp)*1000000) # Convert in ns 
				
			write_api.write(bucket=bucket, org=org, record=point)
	
def fetch_data(start, end, measurement):

	field_name1, field_name2 = measurement.split("-")

	p = {
		"_bucket" : f"{bucket}",
		"_start" : start,
		"_stop" : end,
		"_measurement" : f"{measurement}",
		"_field1" : f"{field_name1}",
		"_field2" : f"{field_name2}",
		# "_asc": False,
	}
			# |> sort(columns: ["_time"], desc: _asc) 
	query = '''
		from(bucket: _bucket) 
			|> range(start: time(v: _start) , stop: time(v: _stop) )
			|> filter(fn: (r) => r["_measurement"] == _measurement)
			|> filter(fn: (r) => r["_field"] == _field1 or r["_field"] == _field2)
			|> aggregateWindow(every: 1ms, fn: mean, createEmpty: false)
			|> yield(name: "mean")
		'''


	with InfluxDBClient(url=url, token=token, org=org, debug=False) as client:
		query_api = client.query_api()
		tables = query_api.query(org=org, query=query, params=p)
		timestamps , field1, field2 = [], [] ,[]
		for i,table in enumerate(tables):
			for row in table.records:
				# print(f"Field {row.get_field()},Value {row.get_value()}, Timestamps {row.get_time()}")
				if row.get_field() == f"{field_name1}":
					field1.append(row.get_value())
					timestamps.append(row.get_time().strftime('%Y-%m-%d %H:%M:%S.%f'))
				elif row.get_field() == f"{field_name2}":
					field2.append(row.get_value())

		return field1, field2, timestamps

def delete_data(start, end, measurement):
    
    with InfluxDBClient(url=url, token=token, org=org) as client:
        del_api = client.delete_api()
        del_api.delete(start,end, bucket="test", org=org)