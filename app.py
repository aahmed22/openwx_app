import pandas as pd 
from pandas import json_normalize
import requests, json, time, os
from pretty_html_table import build_table
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from decouple import config
from database import sending_data_mongodb
from mailgun_email import send_simple_message


load_dotenv()

class DataExtract(object):
    def __init__(self):
        self.open_wx_api_key = os.getenv("OPEN_WX_API_KEY")
        self.zip_codes = config('ZIP_CODES', default='').split(',')
        self.country_code = os.getenv("COUNTRY_CODE")
        self.geo_url = os.getenv("GEO_URL")
        self.wx_url = os.getenv("WX_URL")
        self.excel_file = os.getenv("EXCEL_FILE")
        self.emplate_template = os.getenv("EMAIL_TEMPLATE")
        self.pretty_table = os.getenv("PRETTY_TABLE")
        self.rendered_report = os.getenv("HTML_FILE")
        self.recipent_address = os.getenv("RECIPIENT_EMAIL")
        self.email_subject = os.getenv("EMAIL_SUBJECT")
        self.email_body = os.getenv("EMAIL_BODY")
        self.execute()

    
    def execute(self):
        geo_info_results = list(map(lambda zip_code: self.acquire_geo_location(zip_code), self.zip_codes))

        if geo_info_results is not None:
            geo_info_df = pd.DataFrame(geo_info_results)

            openwx_data_dict = {}
            openwx_data_dict.update(geo_info_df.apply(lambda row: self.acquire_region_weather(row['lat'], row['lon']), axis=1))

            openwx_data_list = [json.loads(value) for value in openwx_data_dict.values()]
            
            df = pd.DataFrame(openwx_data_list)
            flatten_df = json_normalize(df[0])
            cities = flatten_df['name'].to_list()
            flatten_df.to_excel(self.excel_file, index=False, header=True)

            try:
                sending_data_mongodb(flatten_df)

                html_table_blue_light = build_table(flatten_df, 'blue_light')
                with open(self.pretty_table, 'w') as f: f.write(html_table_blue_light)
                time.sleep(1)

                email_template_loc = self.emplate_template
                rendered_content = self.render_template(email_template_loc, zip_codes=self.zip_codes, cities=cities)
                self.render_template

                with open(self.rendered_report, 'w') as file: file.write(rendered_content)
                time.sleep(1)

                send_simple_message(self.recipent_address, self.email_subject, 
                                    self.email_body, self.rendered_report, self.excel_file)

            except Exception as e:
                print(e)
        else:
            print("Unable to fetch geo location data.")


    def acquire_geo_location(self, zip_code):
        geo_location_url = f"{self.geo_url}?zip={zip_code},{self.country_code}&appid={self.open_wx_api_key}"
        zip_code_info = None

        try:
            response = requests.get(geo_location_url)
            response.raise_for_status()
            zip_code_info = response.json()
            print(zip_code_info)
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")

        return zip_code_info
    

    def acquire_region_weather(self, lat, lon):
        try:
            weather_url = f'{self.wx_url}?lat={lat}&lon={lon}&appid={self.open_wx_api_key}'
            response = requests.get(weather_url)
            response.raise_for_status()
            local_weather_info = response.json()
            print(local_weather_info)

            flattened_data = pd.json_normalize(local_weather_info)
            weather_data = local_weather_info.get('weather', [])
            weather_df = pd.json_normalize(weather_data, sep='_')
            weather_df.rename(columns={col: f'weather_{col}' for col in weather_df.columns}, inplace=True)
            df = pd.concat([weather_df, flattened_data], axis=1)
            df.drop(columns=['weather'], inplace=True)

            json_data = df.to_json(orient='records')

            return json_data 
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")


    def render_template(self, template_name, **kwargs):
        env = Environment(loader=FileSystemLoader('.')) 
        template = env.get_template(template_name)

        return template.render(**kwargs)
    

DataExtract()