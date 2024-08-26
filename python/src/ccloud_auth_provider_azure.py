# Class for providing authentication headers or tokens for clients for Azure

import requests
import time
import jwt
import logging

from typing import Any, Dict, Tuple
from decode_jwt import decode_jwt

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError

from ccloud_auth_provider_base import CCloud_Auth_Provider_Base, AuthenticationError


class CCloud_Auth_Provider_Azure(CCloud_Auth_Provider_Base):

    def __init__(self, app_id: str, pool_id: str, exclude_managed_identity_credential: bool=False, min_token_validity: int=30, logging_enable: bool=False):
        try:
            self._app_id = app_id
            self._pool_id = pool_id
            self._min_token_validity = min_token_validity
            # Note, that while writing this comment, the feature of using the visual studio code extension to authenticate with Azure via DefaultAzureCredential is broken in the libs
            # To save some time, we disable this and the shared token method for now
            #default_credential = DefaultAzureCredential()
            if logging_enable:
                logging.basicConfig(level=logging.DEBUG)
            # Unfortunately, we need to stick to setting exclude_visual_studio_code_credential=True until the developers finally fix their code
            self._default_credential = DefaultAzureCredential(exclude_visual_studio_code_credential=True, exclude_shared_token_cache_credential=True, exclude_managed_identity_credential=exclude_managed_identity_credential, logging_enable=logging_enable)
            self._azure_token = None
            self._azure_token_access_token_decoded = None
            self._ccloud_token = None
            self._ccloud_token_access_token_decoded = None
        except ClientAuthenticationError as exc:
            raise AuthenticationError(exc)
    
    @property
    def app_id(self)->str:
        return self._app_id

    @property
    def pool_id(self)->str:
        return self._pool_id

    def _get_azure_token(self)->Tuple[str, bool]:
        if self._azure_token is not None:
            expiration = int(self._azure_token_access_token_decoded['exp'])
            now = int(time.time())
            if expiration - now >= self._min_token_validity:
                return self._azure_token, False

        self._azure_token = self._default_credential.get_token(f'{self._app_id}/.default')
        self._azure_token_access_token_decoded = self.decode_jwt(self._azure_token.token)
        # print ('#####################################')
        # print ('Azure Token')
        # print ('#####################################')
        # print (self._azure_token)
        # print ('Decoded:')
        # print (decode_jwt(self._azure_token.token))
        # print ('#####################################')
        return self._azure_token, True
    
    def get_azure_token_with_expiry(self, cluster_id, config_str)->Tuple[str, float, str, Dict[str, str]]:
        token, _ = self._get_azure_token()
        return (token.token, float(self._azure_token_access_token_decoded['exp']), '', {'logicalCluster': cluster_id, 'identityPoolId': self._pool_id})

    @property
    def azure_token(self)->str:
        token, _ = self._get_azure_token()
        return token.token
    
    @property
    def ccloud_sts_token(self)->str:
        azure_token, azure_token_renewed = self._get_azure_token()
        if self._ccloud_token is not None:
            if not azure_token_renewed:
                expiration = int(self._ccloud_token_access_token_decoded['exp'])
                now = int(time.time())
                if expiration - now >= self._min_token_validity:
                    return self._ccloud_token['access_token']

        data = {'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'subject_token': azure_token.token,
                'identity_pool_id': self._pool_id,
                'subject_token_type': 'urn:ietf:params:oauth:token-type:jwt',
                'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token'}
        url = 'https://api.confluent.cloud/sts/v1/oauth2/token'
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=data, headers=headers)
        if response.status_code != 200:
            error_msg = response.json().get('errors')[0].get('detail')
            raise Exception(f'Unable to authenticate (status code: {response.status_code}, message: "{error_msg}")')
        self._ccloud_token = response.json()
        self._ccloud_token_access_token_decoded = self.decode_jwt(self._ccloud_token['access_token'])
        # print ('#####################################')
        # print ('STS Token')
        # print ('#####################################')
        # print (self._ccloud_token)
        # print ('Decoded:')
        # print (decode_jwt(self._ccloud_token['access_token']))
        # print ('#####################################')
        return self._ccloud_token['access_token']
    
    def decode_jwt(self, access_token: str)->Dict[str, Any]:
        alg = jwt.get_unverified_header(access_token)['alg']
        decoded = jwt.decode(access_token, algorithms=[alg], options={"verify_signature": False})
        return decoded

    def get_token(self, uri: str) -> str:
        return self.get_bearer(uri)

    def get_bearer(self, uri: str) -> str:
        if uri.startswith('https://pkc-') or uri.startswith('pkc-'):
            return self.azure_token
        elif uri.startswith('https://'):
            return self.ccloud_sts_token
        else:
            raise (f'Unable to identify correct token for URI "{uri}". Did you forget to use "https://"?')

    def get_auth_header(self, uri: str) -> Dict[str, str]:
        if uri.startswith('https://pkc-') or uri.startswith('pkc-'):
            return {
                'Authorization': 'Bearer {}'.format(self.azure_token),
                'Confluent-Identity-Pool-Id': self._pool_id
            }
        elif uri.startswith('https://'):
            return {
                'Authorization': 'Bearer {}'.format(self.ccloud_sts_token)
            }
        else:
            raise (f'Unable to identify correct auth header for URI "{uri}". Did you forget to use "https://"?')

