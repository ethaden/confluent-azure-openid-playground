import argparse
import time
import traceback
import requests
import logging
import sys
from typing import Dict
from functools import partial

from confluent_kafka import Consumer, KafkaError
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

    consumer = Consumer(consumer_conf)

    # Specify topic name
    consumer.subscribe([base_config.get('topic')])

    print("Starting to consume messages...")

    try:
        while True:
            msg = consumer.poll(timeout=10.0)

            if msg is None:
                # No message available within timeout
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event - not an error
                    print(f"Reached end of partition {msg.partition()}")
                    continue
                else:
                    print(f"Error: {msg.error()}")
                    break

            # Process the message
            print(f"Received message: Key={msg.key()}, Value={msg.value().decode('utf-8')}, "
                f"Topic={msg.topic()}, Partition={msg.partition()}, Offset={msg.offset()}")

    except Exception as e:
        print(f'Consumer exception: {e}')
        print(traceback.format_exc())
    # except KeyboardInterrupt:
    #     print("\nStopping consumer...")
    finally:
        # Close the consumer to commit final offsets
        consumer.close()
        print("Consumer closed")

if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='ccloud_standard_kafka_consumer',
            exit_on_error=True) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='ccloud_standard_kafka_consumer') # type: ignore  # pragma: no cover
    parser.add_argument('--config', '-c', required=True, help='A config file', default=None)
    parsed_args = parser.parse_args()
    config_file_name = parsed_args.config
    if config_file_name is not None and config_file_name!="":
        config = read_config_file(config_file_name)
        run(config)
    else:
        print("Please provide a config file")
        sys.exit (1)
