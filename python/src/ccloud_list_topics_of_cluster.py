import sys
import time
import argparse
import requests
from typing import Dict, Any

from ccloud_base import CCloud_Azure_Base, ClientAuthenticationError, read_config_file

# Acquire an Azure access token from the specified App Registration and the given scope configured in there
# Make sure that this app registration issues JWT 2.0 tokens (update its manifest!)
# Run "az login" and login to Azure with your acount (via web browser)

class CCloud_Azure_Cluster_Topics(CCloud_Azure_Base):

    def __init__(self, app_id: str, pool_id: str, env_id: str, cluster_id: str):
        super().__init__(app_id, pool_id)
        self._env_id = env_id
        self._cluster_id = cluster_id

    def run(self):
        try:
            headers_ccloud_api = {
                'Authorization': 'Bearer {}'.format(self.ccloud_sts_token)
            }
            cluster_data_url = f'https://api.confluent.cloud/cmk/v2/clusters/{cluster_id}?environment={self._env_id}'
            response = requests.get(cluster_data_url, headers=headers_ccloud_api)
            if response.status_code != 200:
                error_msg = response.json().get('errors')[0].get('detail')
                raise Exception(f'Unable to get metadata of cluster (status code: {response.status_code}, message: "{error_msg}")')
            cluster_metadata = response.json()
            cluster_name = cluster_metadata.get('spec').get('display_name')
            cluster_base_url =  cluster_metadata.get('spec').get('http_endpoint')
            
            initial_url = f'{cluster_base_url}/kafka/v3/clusters/{cluster_id}/topics'
            current_url = initial_url
            # Traverse all result pages, starting with initial one
            print (f'Found the following topics in cluster "{cluster_name}":')
            while current_url is not None:
                headers_kafka_rest_api = {
                    'Authorization': 'Bearer {}'.format(self.azure_token),
                    'Confluent-Identity-Pool-Id': pool_id
                }
                response = requests.get(current_url, headers=headers_kafka_rest_api)
                current_url = None
                if response.status_code != 200:
                    error_code = response.json().get('error_code')
                    error_msg = response.json().get('message')
                    raise Exception(f'Unable to list topics (status code: {error_code}, message: "{error_msg}")')
                response_json = response.json()
                metadata = response_json.get('metadata', None)
                if metadata is not None:
                    current_url = metadata.get('next', None)
                clusters = response_json['data']
                for cluster in clusters:
                    print (f'{cluster["topic_name"]}')
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
    parser.add_argument('--env-id', '-e', help='The environment Id')
    parser.add_argument('--cluster-id', '-k', help='The cluster Id')
    parser.add_argument('--config', '-c', help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    app_id = parsed_args.app_id
    pool_id = parsed_args.pool_id
    env_id = parsed_args.env_id
    cluster_id = parsed_args.cluster_id
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        if app_id is None: app_id = config.get('app_id', None)
        if pool_id is None: pool_id = config.get('pool_id', None)
        if env_id is None: env_id = config.get('env_id', None)
        if cluster_id is None: cluster_id = config.get('cluster_id', None)
    if app_id is None or pool_id is None or env_id is None or cluster_id is None:
        print ('Please provide either a config file or all individual values as parameters')
        exit (1)
    topic_lister = CCloud_Azure_Cluster_Topics(app_id, pool_id, env_id, cluster_id)
    topic_lister.run()
