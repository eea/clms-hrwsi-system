#!/usr/bin/env python3
"""
Wekeo_api_manager module implements the method to interact with WEkEO API to extract candidate inputs.
"""
import sys
import os
import datetime
import yaml
import requests

# Authorizing other packages absolute import
ROOT_FOLDER = '/'.join(os.getcwd().split('nrt_production_system')[:-1])
sys.path.append(ROOT_FOLDER+'nrt_production_system')

from HRWSI_System.harvester.apimanager.api_manager import ApiManager

class WekeoApiManager(ApiManager):
    """Interact with WEkEO API to extract data"""

    def __init__(self,
                 processing_condition_name: str,
                 input_type: str,
                 max_day_since_publication_date: int,
                 max_day_since_measurement_date: int,
                 tile_list_file: str = None,
                 geometry_file: str = None):

        super().__init__(processing_condition_name, max_day_since_publication_date, max_day_since_measurement_date)
        self.input_type = input_type

        # Load config file
        config_data = ApiManager.read_config_file()

        self.url = config_data["API"]["url"]
        self.nb_img_per_page = config_data["API"]["image_per_page"] # Limit max
        self.max_retries = config_data["API"]["max_retries"]

        if tile_list_file:
            try :
                assert geometry_file
                with open(tile_list_file, 'r', encoding="utf-8") as config_file:
                    self.tile_list = yaml.safe_load(config_file)
            except AssertionError:
                self.logger.error("Tile_list file found but no geometry file. Tile_list file is ignored.")
                self.tile_list = None
        else:
            self.tile_list = None

        if geometry_file:
            with open(geometry_file, 'r', encoding="utf-8") as config_file:
                self.geometry = yaml.safe_load(config_file)
        else:
            self.geometry = None

        # Construct request

        # Today
        today = datetime.date.today()

        # PublicationDate interval
        limit_publication_date = datetime.timedelta(days=self.max_day_since_publication_date)
        begin_publication_date = today - limit_publication_date
        filter_publication_date = f"PublicationDate gt {begin_publication_date}T00:00:00.000Z and PublicationDate lt {today}T23:59:59.999Z"

        # ContentDate/Start interval
        limit_content_date = datetime.timedelta(days=self.max_day_since_measurement_date)
        begin_content_date = today - limit_content_date
        filter_content_date = f"ContentDate/Start gt {begin_content_date}T00:00:00.000Z and ContentDate/Start lt {today}T23:59:59.999Z"

        # Image per page
        filter_image_per_page = f"&$top={self.nb_img_per_page}"

        # Orderby
        filter_order_by = "&$orderby=PublicationDate"

        # Contain input type
        filter_contains = f"contains(Name,'{self.input_type}')"

        self.request = f"$filter={filter_contains} and {filter_content_date} and {filter_publication_date}"+filter_order_by+filter_image_per_page

        # Geometry
        if self.geometry:
            filter_geometry=f"OData.CSC.Intersects(area=geography{self.geometry})"
            self.request = f"$filter={filter_contains} and {filter_content_date} and {filter_publication_date} and {filter_geometry}"+filter_order_by+filter_image_per_page


    def get_candidate_inputs(self) -> tuple[tuple]:
        self.logger.info("Begin get_candidate_inputs for WEkEO API")

        # Send request
        self.logger.debug("Request : %s", self.request)
        content = self.send_request(self.request)

        # Get candidate
        candidate_input_tuple = ()
        candidate_input_tuple = self.create_input_tuple(content, candidate_input_tuple)

        self.logger.info("End get_candidate_inputs for WEkEO API")
        return candidate_input_tuple

    def send_request(self, request: str) -> bytes:
        """Send request to Wekeo API and keep the json of the result"""

        self.logger.info("Begin send_request to Wekeo API")

        # Return exception if server fails to send response data
        for _ in range(self.max_retries):
            try:
                r = requests.get(self.url, params=request, timeout=30)
            except requests.exceptions.Timeout:
                self.logger.error("Time out")
                continue
            except requests.exceptions.URLRequired as e:
                self.logger.critical("A valid URL is required to make a request.")
                raise SystemExit(e) from e
            except requests.exceptions.InvalidURL as e:
                self.logger.critical("The URL provided was somehow invalid.")
                raise SystemExit(e) from e
            except requests.exceptions.RequestException as e:
                self.logger.critical("Something else went wrong with requests.get")
                raise SystemExit(e) from e
        content = r.json()

        self.logger.info("End send_request to Wekeo API")

        return content

    def create_input_tuple(self, content: dict, candidate_input_tuple: tuple[tuple]) -> tuple[tuple]:
        """Create tuple of input thanks to the request result"""

        self.logger.info("Begin create tuple to Wekeo API")

        # Create tuple with candidate
        for i in range (len(content['value'])):
            data_name_split = content['value'][i]['Name'].split("_")
            mission = data_name_split[0][:2]
            measurement_day = int(data_name_split[2].split("T")[0])
            tile = data_name_split[5]
            date = content['value'][i]['ContentDate']['Start']
            path = content['value'][i]['S3Path']
            if (self.tile_list and tile in self.tile_list) or not self.tile_list:
                candidate_input_tuple = candidate_input_tuple + ((self.processing_condition_name, date, tile, measurement_day, path, mission),)

        # Add candidate in the others pages of the request if there exist
        if '@odata.nextLink' in content:
            next_page = content['@odata.nextLink']
            nb = next_page.split("=")[-1]
            content = self.send_request(self.request+f"&$skip={nb}")
            candidate_input_tuple = self.create_input_tuple(content, candidate_input_tuple)

        self.logger.info("End create tuple to Wekeo API")

        return candidate_input_tuple
