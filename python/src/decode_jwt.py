import sys
import jwt
import argparse

from azure.identity import DefaultAzureCredential

def decode_jwt(access_token: str):
    alg = jwt.get_unverified_header(access_token)['alg']
    decoded = jwt.decode(access_token, algorithms=[alg], options={"verify_signature": False})
    return decoded


if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='decode_jwt',
            exit_on_error=False) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='ccloud_list_environments') # type: ignore  # pragma: no cover
    parser.add_argument('--access-token', '-a', required=True)
    #parsed_args = parser.parse_args(args=sys.argv)
    parsed_args = parser.parse_args()
    access_token = parsed_args.access_token
    print(decode_jwt(access_token))
