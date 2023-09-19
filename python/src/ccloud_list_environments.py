import sys
import time
import argparse
import requests
from typing import Dict, Any
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from ccloud_base import CCloud_Azure_Base, ClientAuthenticationError, read_config_file

# Acquire an Azure access token from the specified App Registration and the given scope configured in there
# Make sure that this app registration issues JWT 2.0 tokens (update its manifest!)
# Run "az login" and login to Azure with your acount (via web browser)

class CCloud_Azure_Environment_Lister(CCloud_Azure_Base):

    def __init__(self, app_id: str, pool_id: str):
        super().__init__(app_id, pool_id)

    def run(self):
        try:
            initial_url = 'https://api.confluent.cloud/org/v2/environments?page_size=10'
            current_url = initial_url
            # Traverse all result pages, starting with initial one
            print ('Found the following environments:')
            while current_url is not None:
                headers_ccloud_api = {
                    'Authorization': 'Bearer {}'.format(self.ccloud_sts_token)
                }
                response = requests.get(current_url, headers=headers_ccloud_api)
                current_url = None
                if response.status_code != 200:
                    error_msg = response.json().get('errors')[0].get('detail')
                    raise Exception(f'Unable to list environments (status code: {response.status_code}, message: "{error_msg}")')
                response_json = response.json()
                metadata = response_json.get('metadata', None)
                if metadata is not None:
                    current_url = metadata.get('next', None)
                environments = response_json['data']
                for environment in environments:
                    print (f'{environment["display_name"]} ({environment["id"]})')
                # Potenially wait for seconds specified by server until sending next request
                rate_limit_reset_secs = int(response.headers.get('Retry-After', '0'))
                time.sleep(rate_limit_reset_secs)
        except ClientAuthenticationError as exc:
            print (f'Unable to authenticate to Azure: {str(exc)}')
            exit(1)

if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='ccloud_list_environments',
            exit_on_error=False) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='ccloud_list_environments') # type: ignore  # pragma: no cover
    parser.add_argument('--app-id', '-a', help='The Id of the Azure App Registration configured in the Confluent Cloud Identity Pool', default=None)
    parser.add_argument('--pool-id', '-p', help='The Id of the Identity Pool configured in Confluent Cloud', default=None)
    parser.add_argument('--config', '-c', help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    app_id = parsed_args.app_id
    pool_id = parsed_args.pool_id
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        if app_id is None: app_id = config.get('app_id', None)
        if pool_id is None: pool_id = config.get('pool_id', None)
    if app_id is None or pool_id is None:
        print ('Please provide either a config file or all individual values as parameters')
        exit (1)
    env_lister = CCloud_Azure_Environment_Lister(app_id, pool_id)
    env_lister.run()
