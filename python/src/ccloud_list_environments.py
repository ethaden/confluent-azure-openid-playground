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

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError
  
def get_sts_token(pool_id: str, azure_access_token):
    data = {'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
              'subject_token': azure_access_token.token,
              'identity_pool_id': pool_id,
              'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt',
              'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token'}
    url = 'https://api.confluent.cloud/sts/v1/oauth2/token'
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
        raise Exception('Unable to authenticate!')
    return response.json()

def main(app_id: str, pool_id: str):
    # Note, that while writing this comment, the feature of using the visual studio code extension to authenticate with Azure via DefaultAzureCredential is broken in the libs
    # To save some time, we disable this and the shared token method for now
    #default_credential = DefaultAzureCredential()
    default_credential = DefaultAzureCredential(exclude_visual_studio_code_credential=True, exclude_shared_token_cache_credential=True)
    # Acquire an Azure access token from the specified App Registration and the given scope configured in there
    # Make sure that this app registration issues JWT 2.0 tokens (update its manifest!)
    # Run "az login" and login to Azure with your acount (via web browser)
    try:
        azure_access_token = default_credential.get_token(f'{app_id}/.default')
        # Use Confluent STS API to exchange
        ccloud_token = get_sts_token(pool_id=pool_id, azure_access_token=azure_access_token)
        header = {
            'Authorization': 'Bearer {}'.format(ccloud_token['access_token'])
        }
        initial_url = 'https://api.confluent.cloud/org/v2/environments?page_size=10'
        current_url = initial_url
        # Traverse all result pages, starting with initial one
        print ('Found the following clusters:')
        while current_url is not None:
            response = requests.get(current_url, headers=header)
            current_url = None
            if response.status_code != 200:
                raise Exception('Unable to list environments')
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

def read_config_file(config_file_name: str) -> Dict[str, Any]:
    try:
        with open(config_file_name, 'r') as fs:
            return load(fs, Loader=Loader)
    except OSError:
        pass
    raise Exception(f'Unable to open config file "{config_file_name}"')

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
    main(app_id, pool_id)
