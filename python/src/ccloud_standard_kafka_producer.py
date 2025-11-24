import argparse
import time
import traceback
import requests
import logging
import sys
from typing import Dict
from functools import partial

from confluent_kafka import Producer, KafkaError
from confluent_kafka import KafkaException

from ccloud_util import read_config_file


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable Confluent Kafka debug logging
logging.getLogger('confluent_kafka').setLevel(logging.INFO)

def oauth_token_refresh_cb(base_config, oauth_config):
    try:
        proxies = None
        if 'http_proxy' in base_config:
            http_proxy = base_config.get('http_proxy')
            https_proxy = base_config.get('https_proxy', http_proxy)
            proxies = {
                "http"  : http_proxy,
                "https" : https_proxy
            }
        payload = {
            'grant_type': 'client_credentials',
            'client_id': base_config.get('sasl_oauthbearer_client_id'),
            'client_secret': base_config.get('sasl_oauthbearer_client_secret'),
            'scope': {base_config.get("sasl_oauthbearer_scope")}
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(
            base_config.get('sasl_oauthbearer_token_endpoint_url'),
            data=payload,
            proxies=proxies,
            timeout=5,
            headers=headers
        )
        if response.status_code != 200:
            print (response.content)
        response.raise_for_status()
        token = response.json()

        #print("token is")
        #print(token)

        # Return the token and its expiration time
        now = time.time()
        expires_at = now + float(token['expires_in'])
        principal = "" # not required
        extensions = { 'logicalCluster': base_config.get('cluster_id') }
        # Pool ID is optional, there may also be multiple pool IDs (not covered here in this example)
        if 'identityPoolId' in base_config and base_config['identityPoolId'] != '':
            extensions['identityPoolId'] = base_config['identityPoolId']
        return token['access_token'], expires_at, principal, extensions
    except Exception as e:
        print("Exception has happened")
        # pprint(e)
        print(traceback.format_exc())
        # Handle exceptions and signal failure
        raise KafkaException(f"OAuth token refresh failed: {e}")

def run(base_config: Dict[str, str]):
    consumer_conf = {
        'bootstrap.servers': base_config.get('bootstrap_servers'),
        'group.id': base_config.get('consumer_group_id'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'OAUTHBEARER',
        'oauth_cb': partial(oauth_token_refresh_cb, base_config),
        'partitioner': 'murmur2', # Recommended for producers, added just for reference here
        #'debug': 'security,protocol,broker'
        #'debug': 'all'
    }

    producer = Producer(consumer_conf)

    print("Starting to produce messages...")

    try:
        for i in range(0, 5):
            producer.produce(base_config['topic'], key=f'K{i}', value=f'{i}')

    except Exception as e:
        print(f'Producer exception: {e}')
        print(traceback.format_exc())
    # except KeyboardInterrupt:
    #     print("\nStopping consumer...")
    finally:
        # Close the producer to commit final offsets
        producer.flush()
        print("Producer closed")

if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='ccloud_standard_producer',
            exit_on_error=True) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='ccloud_standard_producer') # type: ignore  # pragma: no cover
    parser.add_argument('--config', '-c', required=True, help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        run(config)
    else:
        print("Please provide a config file")
        sys.exit (1)
