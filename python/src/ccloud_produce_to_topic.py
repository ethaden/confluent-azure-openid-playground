import datetime
import sys
import functools
import argparse
import time
import requests
import logging

from confluent_kafka import Producer, SerializingProducer
from confluent_kafka.serialization import StringSerializer
import socket

from ccloud_util import read_config_file
from ccloud_auth_provider_azure import CCloud_Auth_Provider_Azure, AuthenticationError
from ccloud_auth_provider_base import CCloud_Auth_Provider_Base

# Acquire an Azure access token from the specified App Registration and the given scope configured in there
# Make sure that this app registration issues JWT 2.0 tokens (update its manifest!)
# Run "az login" and login to Azure with your acount (via web browser)

class CCloud_Azure_Producer:

    def __init__(self, auth_provider: CCloud_Auth_Provider_Base, env_id: str, cluster_id: str, topic: str, client_id: str=None):
        self._auth_provider = auth_provider
        self._env_id = env_id
        self._cluster_id = cluster_id
        self._topic = topic
        self._client_id = client_id

    def run(self):
        try:
            cluster_data_url = f'https://api.confluent.cloud/cmk/v2/clusters/{self._cluster_id}?environment={self._env_id}'
            headers_ccloud_api = self._auth_provider.get_auth_header(cluster_data_url)
            response = requests.get(cluster_data_url, headers=headers_ccloud_api)
            if response.status_code != 200:
                error_msg = response.json().get('errors')[0].get('detail')
                raise Exception(f'Unable to get metadata of cluster (status code: {response.status_code}, message: "{error_msg}")')
            cluster_metadata = response.json()
            cluster_name = cluster_metadata.get('spec').get('display_name')
            cluster_base_url =  cluster_metadata.get('spec').get('http_endpoint')
            kafka_bootstrap_endpoint = cluster_metadata.get('spec').get('kafka_bootstrap_endpoint')
            print (cluster_base_url)

            logger = logging.getLogger(__name__)
            string_serializer = StringSerializer('utf_8')
            client_config = {
                'bootstrap.servers': kafka_bootstrap_endpoint,
                'client.id': self._client_id or socket.gethostname(),
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'OAUTHBEARER',
                'oauth_cb': lambda config_str: self._auth_provider.get_azure_token_with_expiry(self._cluster_id, config_str),
                'logger': logger,
                'key.serializer': string_serializer,
                'value.serializer': string_serializer,
                'partitioner': 'murmur2'
            }
            producer = SerializingProducer(client_config)
            while True:
                producer.poll(0.0)
                now = datetime.datetime.now()
                producer.produce(self._topic, key='key', value=now.isoformat(), 
                    on_delivery = lambda err, msg: self.delivery_report(err, msg))
                time.sleep(1)
            producer.flush()

        except AuthenticationError as exc:
            print (f'Unable to authenticate: {str(exc)}')
            exit(1)
    def delivery_report(self, err, msg):
        if err is not None:
            print('Delivery failed for User record {}: {}'.format(msg.key(), err))
            return
        print('User record {} successfully produced to {} [{}] at offset {}'.format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()))

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
    parser.add_argument('--topic', '-t', help='The topic name')
    parser.add_argument('--client-id', '-i', help='The client ID (if not specified, te hostname is used)')
    parser.add_argument('--exclude-managed-identity-credential', '-m', help='Disables using the managed identity in Azure authentication which might speed up the login on developer machines. Default: False', action='store_true')
    parser.add_argument('--debug-azure-authentication', '-d', help='Log debug output from Azure authentication. Default: False', action='store_true')
    parser.add_argument('--config', '-c', help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    app_id = parsed_args.app_id
    pool_id = parsed_args.pool_id
    env_id = parsed_args.env_id
    cluster_id = parsed_args.cluster_id
    topic = parsed_args.topic
    client_id = parsed_args.client_id
    exclude_managed_identity_credential = parsed_args.exclude_managed_identity_credential
    debug_azure_authentication = parsed_args.debug_azure_authentication
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        if app_id is None: app_id = config.get('app_id', None)
        if pool_id is None: pool_id = config.get('pool_id', None)
        if env_id is None: env_id = config.get('env_id', None)
        if cluster_id is None: cluster_id = config.get('cluster_id', None)
        if topic is None: topic = config.get('topic', None)
        if client_id is None: client_id = config.get('client_id', None)
        exclude_managed_identity_credential = config.get('exclude_managed_identity_credential', exclude_managed_identity_credential)
        debug_azure_authentication = config.get('debug_azure_authentication', debug_azure_authentication)
    if app_id is None or pool_id is None or env_id is None or cluster_id is None or topic is None:
        print ('Please provide either a config file or all individual values as parameters')
        exit (1)
    auth_provider = CCloud_Auth_Provider_Azure(app_id, pool_id, exclude_managed_identity_credential=exclude_managed_identity_credential, logging_enable=debug_azure_authentication)
    producer = CCloud_Azure_Producer(auth_provider, env_id, cluster_id, topic, client_id)
    producer.run()
