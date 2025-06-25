import sys
import jwt
import argparse
from datetime import datetime, tzinfo

def decode_jwt(access_token: str):
    alg = jwt.get_unverified_header(access_token)['alg']
    decoded = jwt.decode(access_token, algorithms=[alg], options={"verify_signature": False})
    return decoded


if __name__=='__main__':
    if sys.version_info >= (3, 9):
        parser = argparse.ArgumentParser(prog='decode_jwt',
            exit_on_error=False) # type: ignore  # pragma: no cover
    else:
        parser = argparse.ArgumentParser(prog='decode_jwt') # type: ignore  # pragma: no cover
    parser.add_argument('--access-token', '-a', required=True)
    #parsed_args = parser.parse_args(args=sys.argv)
    parsed_args = parser.parse_args()
    access_token = parsed_args.access_token
    decoded_token = decode_jwt(access_token)
    print(decoded_token)
    if 'iat' in decoded_token:
        iat_date = datetime.fromtimestamp(decoded_token.get('iat'))
        print(f'Issued at: {iat_date.strftime("%Y-%m-%d %H:%M:%S")} (UTC)')
    if 'exp' in decoded_token:
        exp_date = datetime.fromtimestamp(decoded_token.get('exp'))
        print(f'Expiration at: {exp_date.strftime("%Y-%m-%d %H:%M:%S")} (UTC)')
