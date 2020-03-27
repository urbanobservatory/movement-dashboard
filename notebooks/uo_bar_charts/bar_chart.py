import os
import requests
import datetime
import json
import io
import pandas as pd
from .plot_data import plot_data
class BarChart:

    def __init__(self,name):

        self.name = name
        self.__make_folders()


    def plot_data(self,renamer):
        return plot_data(self,renamer)

    def __make_folders(self):
        self.data_folder = '../cache/bar-charts/{folder_name}-data/'.format(folder_name=self.name)

        self.geojson_folder = '../cache/bar-charts/{folder_name}-geojson/'.format(folder_name=self.name)
        self.plots_folder = '../cache/bar-charts/{folder_name}-plots/'.format(folder_name=self.name)
        self.sensor_map_folder = '../cache/bar-charts/maps/'
        if not os.path.exists('../cache/bar-charts/'):
            os.makedirs('../cache/bar-charts/')
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        if not os.path.exists(self.geojson_folder):
            os.makedirs(self.geojson_folder)

        if not os.path.exists(self.sensor_map_folder):
            os.makedirs(self.sensor_map_folder)

        if not os.path.exists(self.plots_folder):
            os.makedirs(self.plots_folder)

        self.sensor_json = '../cache/bar-charts/{folder_name}.json'.format(folder_name=self.name)

    def cache_data(self,sensor_params, variable_params, start_date, end_date, variables=[]):

        dt_format = "%Y%m%d%H%M%S"

        url = 'http://uoweb3.ncl.ac.uk:80/metadata/api/variables'
        if len(variables) == 0:
            r = requests.get(url, variable_params)

            for item in r.json()['items']:
                variables.append(item['name'])
        url = 'http://uoweb3.ncl.ac.uk:80/metadata/api/sensors'

        api_url = 'http://uoweb3.ncl.ac.uk/api/v1.1/sensors/{sensor_name}/data/csv/'
        r = requests.get(url, sensor_params)
        print(r.url)
        sensor_list = []

        sensors = r.json()['items']

        page_count = r.json()['pagination']['pageCount']

        for i in range(1,page_count):
            r = requests.get(url, {**sensor_params,**dict(page=i)})
            sensors += r.json()['items']
        for i, item in enumerate(sensors):
            print('cacheing sensor: ',item['name'] + '({i}/{tot})'.format(i=i+1,tot=len(sensors)))
            sensor_list.append(item['name'])
            json.dump(
                item['current_location']['geojson'],
                open(
                    os.path.join('{geojson_folder}/{sensor_name}.json'.format(
                        sensor_name=item['name'],
                        geojson_folder=self.geojson_folder,
                    )),
                    'w'
                )
            )
            params = {
                'starttime': (start_date - datetime.timedelta(days=0)).strftime(dt_format),
                'endtime': (end_date - datetime.timedelta(days=0)).strftime(dt_format),
                'data_variable': ','.join(variables),
            }
            r = requests.get(api_url.format(sensor_name=item['name']), params)
            frame = pd.read_csv(io.StringIO(r.content.decode('utf-8')))

            frame.to_pickle('{data_folder}/{sensor_name}.tar.gz'.format(
                sensor_name=item['name'],
                data_folder=self.data_folder
            )
            )
        with open(self.sensor_json,'w') as sensor_json_wrapper:
            json.dump({'sensors': sensor_list}, sensor_json_wrapper)
