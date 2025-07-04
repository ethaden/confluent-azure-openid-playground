import sys
import jwt
import argparse
import msal

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
    parser.add_argument('--client-id', '-c', required=True)
    parser.add_argument('--client-secret', '-s', required=True)
    parser.add_argument('--app-id', '-a', required=False, help='If not set, client-id is used', default=None)
    parser.add_argument('--scope', '-x', required=False, default='.default')
    #parsed_args = parser.parse_args(args=sys.argv)
    parsed_args = parser.parse_args()
    tenant_id = parsed_args.tenant_id
    client_id = parsed_args.client_id
    client_secret = parsed_args.client_secret
    app_id=parsed_args.app_id if parsed_args.app_id is not None else client_id
    scopes = [ f'{app_id}/{parsed_args.scope}' ]
    print (scopes)

    authority = 'https://login.microsoftonline.com/' + tenant_id
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
        )

    result = app.acquire_token_for_client(
        scopes=scopes
    )

    if 'access_token' in result:
        access_token = result['access_token']
        print(decode_jwt(access_token))
    else:
        print(result.get('error'))
        print(result.get('error_description')) 
