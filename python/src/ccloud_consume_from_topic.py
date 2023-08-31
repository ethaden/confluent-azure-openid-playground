import random
import sys
import functools
import argparse
import time
import requests
import logging

from confluent_kafka import DeserializingConsumer, KafkaException, KafkaError
from confluent_kafka.serialization import StringDeserializer
import socket

from ccloud_base import CCloud_Azure_Base, ClientAuthenticationError, read_config_file

# Acquire an Azure access token from the specified App Registration and the given scope configured in there
# Make sure that this app registration issues JWT 2.0 tokens (update its manifest!)
# Run "az login" and login to Azure with your acount (via web browser)

class CCloud_Azure_Consumer(CCloud_Azure_Base):

    def __init__(self, app_id: str, pool_id: str, env_id: str, cluster_id: str, topic: str, client_id: str=None, consumer_group_id: str=None):
        super().__init__(app_id, pool_id)
        self._env_id = env_id
        self._cluster_id = cluster_id
        self._topic = topic
        self._client_id = client_id
        self._consumer_group_id = consumer_group_id

    def run(self):
        try:
            headers_kafka_rest_api = {
                'Authorization': 'Bearer {}'.format(self.azure_token),
                'Confluent-Identity-Pool-Id': self.pool_id
            }
            # Use Confluent STS API to exchange
            headers_ccloud_api = {
                'Authorization': 'Bearer {}'.format(self.ccloud_sts_token)
            }
            cluster_data_url = f'https://api.confluent.cloud/cmk/v2/clusters/{self._cluster_id}?environment={self._env_id}'
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
            string_deserializer = StringDeserializer('utf_8')
            client_config = {
                'bootstrap.servers': kafka_bootstrap_endpoint,
                'client.id': self._client_id or socket.gethostname(),
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'OAUTHBEARER',
                'oauth_cb': lambda config_str: self.get_azure_token_with_expiry(self._cluster_id, config_str),
                'logger': logger,
                'key.deserializer': string_deserializer,
                'value.deserializer': string_deserializer,
                'group.id': self._consumer_group_id or random.randint(0, 10000000),
                'auto.offset.reset': 'smallest'
            }
            consumer = DeserializingConsumer(client_config)
            try:
                consumer.subscribe([self._topic])
                while True:
                    msg = consumer.poll(timeout=1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            logger.info('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                        else:
                            raise KafkaExeption(msg.error())
                    else:
                        print (f'{msg.key()}: {msg.value()}')
            except Exception as exc:
                logger.error(f'An exception occurred: {exc}')
            finally:
                consumer.close()


        except ClientAuthenticationError as exc:
            print (f'Unable to authenticate to Azure: {str(exc)}')
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
    parser.add_argument('--consumer-group-id', '-g', help='The conumser group ID (if not specified, a random number is used)')
    parser.add_argument('--config', '-c', help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    app_id = parsed_args.app_id
    pool_id = parsed_args.pool_id
    env_id = parsed_args.env_id
    topic = parsed_args.topic
    cluster_id = parsed_args.cluster_id
    client_id = parsed_args.client_id
    consumer_group_id = parsed_args.consumer_group_id
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        if app_id is None: app_id = config.get('app_id', None)
        if pool_id is None: pool_id = config.get('pool_id', None)
        if env_id is None: env_id = config.get('env_id', None)
        if cluster_id is None: cluster_id = config.get('cluster_id', None)
        if topic is None: topic = config.get('topic', None)
        if cluster_id is None: cluster_id = config.get('cluster_id', None)
        if consumer_group_id is None: consumer_group_id = config.get('consumer_group_id', None)
    if app_id is None or pool_id is None or env_id is None or cluster_id is None or topic is None:
        print ('Please provide either a config file or all individual values as parameters')
        exit (1)
    consumer = CCloud_Azure_Consumer(app_id, pool_id, env_id, cluster_id, topic, client_id, consumer_group_id)
    consumer.run()
