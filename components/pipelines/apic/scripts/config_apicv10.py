import os, json
import utils
import api_calls

"""

API Connect v10 post install configuration steps --> https://www.ibm.com/docs/en/api-connect/10.0.x?topic=environment-cloud-manager-configuration-checklist

"""

FILE_NAME = "config_apicv10.py"
DEBUG = os.getenv('DEBUG','')
# This is the default out of the box catalog that gets created when a Provider Organization is created.
catalog_name = "sandbox"

def info(step):
    return "[INFO]["+ FILE_NAME +"][STEP " + str(step) + "] - " 

try:

######################################################################################
# Step 1 - Get the IBM API Connect Toolkit credentials and environment configuration #
######################################################################################

    print(info(1) + "######################################################################################")
    print(info(1) + "# Step 1 - Get the IBM API Connect Toolkit credentials and environment configuration #")
    print(info(1) + "######################################################################################")

    toolkit_credentials = utils.get_toolkit_credentials(os.environ["CONFIG_FILES_DIR"])
    environment_config = utils.get_env_config(os.environ["CONFIG_FILES_DIR"])
    if DEBUG:
        print(info(1) + "These are the IBM API Connect Toolkit Credentials")
        print(info(1) + "-------------------------------------------------")
        print(info(1), json.dumps(toolkit_credentials, indent=4, sort_keys=False))
        print(info(1) + "These is the environment configuration")
        print(info(1) + "--------------------------------------")
        print(info(1), json.dumps(environment_config, indent=4, sort_keys=False))

##################################################################
# Step 2 - Get the IBM API Connect Cloud Management Bearer Token #
##################################################################

    print(info(2) + "##################################################################")
    print(info(2) + "# Step 2 - Get the IBM API Connect Cloud Management Bearer Token #")
    print(info(2) + "##################################################################")
    
    admin_bearer_token = api_calls.get_bearer_token(environment_config["APIC_ADMIN_URL"],
                                                    "admin",
                                                    environment_config["APIC_ADMIN_PASSWORD"],
                                                    "admin/default-idp-1",
                                                    toolkit_credentials["toolkit"]["client_id"],
                                                    toolkit_credentials["toolkit"]["client_secret"])
    if DEBUG:
        print(info(2) + "This is the Bearer Token to work against the IBM API Connect Cloud Management endpoints")
        print(info(2) + "--------------------------------------------------------------------------------------")
        print(info(2), admin_bearer_token)

#################################
# Step 3 - Get the Admin org ID #
#################################

    print(info(3) + "#################################")
    print(info(3) + "# Step 3 - Get the Admin org ID #")
    print(info(3) + "#################################")
    
    url = 'https://' + environment_config["APIC_ADMIN_URL"] + '/api/cloud/orgs'

    response = api_calls.make_api_call(url, admin_bearer_token, 'get')
    
    found = False
    admin_org_id = ''
    if response.status_code != 200:
          raise Exception("Return code for getting the Admin org ID isn't 200. It is " + str(response.status_code))
    for org in response.json()['results']:
        if org['org_type'] == "admin":
            found = True
            admin_org_id = org['id']
    if not found:
        raise Exception("[ERROR] - The Admin Organization was not found in the IBM API Connect Cluster instance")
    if DEBUG:
        print(info(3) + "Admin Org ID: " + admin_org_id)

####################################
# Step 4 - Create the Email Server #
####################################

    print(info(4) + "####################################")
    print(info(4) + "# Step 4 - Create the Email Server #")
    print(info(4) + "####################################")
    
    url = 'https://' + environment_config["APIC_ADMIN_URL"] + '/api/orgs/' + admin_org_id + '/mail-servers'
    
    # Create the data object
    data = {}
    data['title'] = 'Default Email Server'
    data['name'] = 'default-email-server'
    data['host'] = os.environ['EMAIL_HOST']
    data['port'] = int(os.environ['EMAIL_PORT'])
    credentials = {}
    credentials['username'] = os.environ['EMAIL_USERNAME']
    credentials['password'] = os.environ['EMAIL_PASSWORD']
    data['credentials'] = credentials
    data['tls_client_profile_url'] = None
    data['secure'] = False

    if DEBUG:
        print(info(4) + "This is the data object:")
        print(info(4), data)
        print(info(4) + "This is the JSON dump:")
        print(info(4), json.dumps(data))

    response = api_calls.make_api_call(url, admin_bearer_token, 'post', data)

    if response.status_code != 201:
          raise Exception("Return code for creating the Email Server isn't 201. It is " + str(response.status_code))
    email_server_url = response.json()['url']
    if DEBUG:
        print(info(4) + "Email Server url: " + email_server_url)

##################################################
# Step 5 - Sender and Email Server Configuration #
##################################################

    print(info(5) + "##################################################")
    print(info(5) + "# Step 5 - Sender and Email Server Configuration #")
    print(info(5) + "##################################################")

    url = 'https://' + environment_config["APIC_ADMIN_URL"] + '/api/cloud/settings'
    
    # Create the data object
    # Ideally this would also be loaded from a sealed secret
    data = {}
    data['mail_server_url'] = email_server_url
    email_sender = {}
    email_sender['name'] = 'APIC Administrator'
    email_sender['address'] = 'test@test.com'
    data['email_sender'] = email_sender

    if DEBUG:
        print(info(5) + "This is the data object:")
        print(info(5), data)
        print(info(5) + "This is the JSON dump:")
        print(info(5), json.dumps(data))

    response = api_calls.make_api_call(url, admin_bearer_token, 'put', data)

    if response.status_code != 200:
          raise Exception("Return code for Sender and Email Server configuration isn't 200. It is " + str(response.status_code))

############################################
# Step 6 - Create a Provider Organization #
############################################

    print(info(10) + "############################################")
    print(info(10) + "# Step 6 - Create a Provider Organization #")
    print(info(10) + "############################################")

    # First, we need to get the user registries so that we can create a new user who will be the Provider Organization Owner

    provider_registries = response.json()['provider_user_registry_urls']

    managed_registry_url = None

    # search for managed registry
    for registry_url in provider_registries:
        registry_details = api_calls.make_api_call(registry_url, admin_bearer_token, 'get')
        
        if registry_details.status_code != 200:
            raise Exception("Could not get registry details for: " + registry_url)

        registry_info = registry_details.json()

        if registry_info.get("management_type") == "managed":
            managed_registry_url = registry_url
            break

    if managed_registry_url is None:
        raise Exception("No managed provider user registry found. Cannot continue.")

    if DEBUG:
        print(info(10) + f"Using managed Provider User Registry: {managed_registry_url}")

    # Then, we need to register the user that will be the Provider Organization owner

    url = managed_registry_url + '/users'

    # Create the data object
    # Ideally this should be loaded from a sealed secret.
    # Using defaults for now.
    data = {}
    data['username'] = os.environ["PROV_ORG_OWNER_USERNAME"]
    data['email'] = os.environ["PROV_ORG_OWNER_EMAIL"]
    data['first_name'] = os.environ["PROV_ORG_OWNER_FIRST_NAME"]
    data['last_name'] = os.environ["PROV_ORG_OWNER_LAST_NAME"]
    data['password'] = os.environ["PROV_ORG_OWNER_PASSWORD"]

    if DEBUG:
        print(info(10) + "This is the data object:")
        print(info(10), data)
        print(info(10) + "This is the JSON dump:")
        print(info(10), json.dumps(data))

    response = api_calls.make_api_call(url, admin_bearer_token, 'post', data)

    if response.status_code != 201:
          raise Exception("Return code for registering the provider organization owner user isn't 201. It is " + str(response.status_code))
    
    owner_url = response.json()['url']
    if DEBUG:
        print(info(10) + "Provider Organization Owner url: " + owner_url)
    
    # Finally, we can create the Provider Organization with the previous owner

    url = 'https://' + environment_config["APIC_ADMIN_URL"] + '/api/cloud/orgs'

    # Compute the name of the Provider Organization from the title
    po_name=os.environ["PROV_ORG_TITLE"].strip().replace(" ","-")

    # Create the data object
    # Ideally this should be loaded from a sealed secret.
    # Using defaults for now.
    data = {}
    data['title'] = os.environ["PROV_ORG_TITLE"]
    data['name'] = po_name.lower()
    data['owner_url'] = owner_url

    if DEBUG:
        print(info(10) + "This is the data object:")
        print(info(10), data)
        print(info(10) + "This is the JSON dump:")
        print(info(10), json.dumps(data))

    response = api_calls.make_api_call(url, admin_bearer_token, 'post', data)

    if response.status_code != 201:
          raise Exception("Return code for creating the provider organization isn't 201. It is " + str(response.status_code))

###############################################################
# Step 7 - Get the IBM API Connect Provider API Bearer Token #
###############################################################

    print(info(11) + "###############################################################")
    print(info(11) + "# Step 7 - Get the IBM API Connect Provider API Bearer Token #")
    print(info(11) + "###############################################################")
    
    # Ideally, the username and password for getting the Bearer Token below would come from a sealed secret (that woul also be used
    # in the previous step 6 when registering the new user for the provider organization owner)
    # Using defaults for now.
    admin_bearer_token = api_calls.get_bearer_token(environment_config["APIC_API_MANAGER_URL"],
                                                    os.environ["PROV_ORG_OWNER_USERNAME"],
                                                    os.environ["PROV_ORG_OWNER_PASSWORD"],
                                                    "provider/default-idp-2",
                                                    toolkit_credentials["toolkit"]["client_id"],
                                                    toolkit_credentials["toolkit"]["client_secret"])
    if DEBUG:
        print(info(11) + "This is the Bearer Token to work against the IBM API Connect API Management endpoints")
        print(info(11) + "-------------------------------------------------------------------------------------")
        print(info(11), admin_bearer_token)

#######
# END #
#######

    print("#######")
    print("# END #")
    print("#######")

except Exception as e:
    raise Exception("[ERROR] - Exception in " + FILE_NAME + ": " + repr(e))