# This is a playground for using Azure OIDC with Confluent Cloud

Please have a look in the subfolders for examples in multiple programming languages.

CAUTION: Everything contained in this repository is not supported by Confluent.

DISCLAIMER AND WARNING: You use this code at your own risk! Please do not use it for production systems. The author may not be held responsible for any harm caused by this code!

## Preconditions

This project requires the following setup.


### Setup of Azure

Create an "App registrations" in your EntraID tenant. This resource is the global representation of your Confluent Cloud organization. It is connected to one Enterprise Application per Azure Tenant, each of them represent the identity of your Confluent Cloud organization in that tenant.

Conceptually, you could either use your user identity or another app registration representing your own application to request access to the application registration that represents your Confluent Cloud organization. These are completely separate entities in Entra ID. Make sure you don't mix these up with the entities representing your Confluent Cloud organization!

Therefore, when we talk about the app registration or the enterprise application in the following text, we always refer to the app registration/enterprise application which represents your Confluent Cloud organization.

#### Optionally: Create App Roles
One way to authorize users for specific resources in Confluent Cloud is to configure App Roles in Azure.
Just add roles to your app registration, for example a role called `OrgAdminRole`, and configure it such that both users/groups and applications may get access to it.

You can check the existence of your configured app roles (e.g. "OrgAdminRole") in the tokens provided by the user application by configuring appropriate rules in your identity pool, see below.

In the `API permissions`, add a new permission with a name of your choice.

The App registration always comes with an "Enterprise Application". You can access this using the overview of the app registration. If you want to use roles, you need to restrict access to the enterprise application to selected users/groups and assign your custom roles to them (you find the settings under `Users and Groups`).

#### Alternatively: Use Security Groups

Instead of using roles you can also check for membership in security groups for authorization in Confluent Cloud.

By default, groups are not contained in the tokens issued by Entra ID. In you app registration, you can enable the `groups` token under `Token configuration` by adding a group claim. Make sure to include at least security groups and use the default setting `Group ID` for all of `ID, Access, SAML`.

### Setup of Confluent Cloud

#### Add Identity Provider to Workload identities

Configure an Entra ID (formerly called "Azure AD") provider with any name and description.

Set the Issuer URL according to the Microsoft documentation, i.e. `https://login.microsoftonline.com/<YOUR-TENANT-ID>/v2.0`.

Set the JWKS URI correctly following the docs, i.e. `
https://login.microsoftonline.com/organizations/discovery/v2.0/keys`.


#### Identity Pool

Create a new identity pool in the identity provider.
You can use `claims.sub` as value for the identity claim field.

Configure a filter. Here, cou can check the existence of your configured app roles (e.g. "OrgAdminRole") in the tokens provided by the user application by configuring appropriate rules in your identity pool. For example:

```text
claims.aud=='Put your Application (client) ID here' &&
'OrgAdminRole' in claims.roles
```

Assign the `OrganizationAdmin` role to the identity pool.

Alternatively (and potentially being the better option), you can check for security groups, if you have configured the groups claim for app registration's tokens (see above).

A rule for checking access to your identity pool could then look like this:

```text
claims.aud=='Put your Application (client) ID here' &&
'<PUT SID OF THE DESIRED SECURITY GROUP HERE>' in claims.groups
```

## Troubleshooting

Try to request a token manually, using this call:

```console
curl --request POST \
--url 'https://YOUR_DOMAIN/oauth/token' \
--header 'content-type: application/x-www-form-urlencoded' \
--data grant_type=client_credentials \
--data client_id=YOUR_CLIENT_ID \
--data client_secret=YOUR_CLIENT_SECRET \
--data scope=YOUR_SCOPE
```


## License

Copyright Eike Thaden, 2023.

See LICENSE file
