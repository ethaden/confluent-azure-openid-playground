import sys
import jwt
import argparse

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError

def decode_jwt(access_token: str):
    alg = jwt.get_unverified_header(access_token)['alg']
    decoded = jwt.decode(access_token, algorithms=[alg], options={'verify_signature': False})
    return decoded


if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='fetch_and_show_access_token',
            exit_on_error=False) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='fetch_and_show_access_token') # type: ignore  # pragma: no cover
    parser.add_argument('--tenant-id', '-t', required=True)
    parser.add_argument('--app-id', '-a', required=True, help='If not set, client-id is used', default=None)
    parser.add_argument('--scope', '-x', required=False, default='.default')
    #parsed_args = parser.parse_args(args=sys.argv)
    parsed_args = parser.parse_args()
    tenant_id = parsed_args.tenant_id
    app_id=parsed_args.app_id

    try:
        # Unfortunately, we need to stick to setting exclude_visual_studio_code_credential=True until the developers finally fix their code
        default_credential = DefaultAzureCredential(exclude_visual_studio_code_credential=True, exclude_shared_token_cache_credential=True, exclude_managed_identity_credential=True)

        access_token = default_credential.get_token([f'{app_id}/{parsed_args.scope}'])
        print(decode_jwt(access_token))
    except ClientAuthenticationError as exc:
        print (exc)
