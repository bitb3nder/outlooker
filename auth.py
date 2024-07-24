import requests, time, os

def get_tenant_id_from_email(email):
    domain = email.split('@')[-1]
    lookup_url = f"https://login.microsoftonline.com/{domain}/.well-known/openid-configuration"
    response = requests.get(lookup_url)

    if response.status_code == 200:
        tenant_info = response.json()
        tenant_id = tenant_info.get("issuer", "").split("/")[-2]
        return tenant_id
    else:
        print("Failed to obtain tenant information")
        print("Response code:", response.status_code)
        print("Response message:", response.text)
        return None

def get_access_token_from_email(tenant_id, email, password):
    # Function to obtain access token using ROPC flow
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "password",
        "client_id": "d3590ed6-52b3-4102-aeff-aad2292ab01c",
        "scope": "https://graph.microsoft.com/.default",
        "username": email,
        "password": password
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code == 200:
        response_json = response.json()
        access_token = response_json.get("access_token")
        refresh_token = response_json.get("refresh_token")
        return access_token
    else:
        print("Failed to obtain access token")
        print("Response code:", response.status_code)
        print("Response message:", response.text)
        return None

def get_access_token_from_refresh_token(refresh_token):
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": "d3590ed6-52b3-4102-aeff-aad2292ab01c",
        "scope": "https://graph.microsoft.com/.default",
        "refresh_token": refresh_token
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(token_url, data=data, headers=headers)
    
    if response.status_code == 200:
        response_json = response.json()
        access_token = response_json.get("access_token")
        return access_token
    else:
        print("Failed to obtain access token from refresh token")
        print("Response code:", response.status_code)
        print("Response message:", response.text)
        return None

def graph_auth(args):
    # Check for refresh token in .auth_token file
    if not args.access_token and not args.refresh_token:
        auth_token_path = ".auth_token"
        if os.path.exists(auth_token_path):
            with open(auth_token_path, "r") as token_file:
                refresh_token = token_file.read().strip()
            if refresh_token:
                print("Using refresh token from .auth_token file.")
                access_token = get_access_token_from_refresh_token(refresh_token)
                if not access_token:
                    print("Failed to obtain access token using the refresh token from .auth_token.")
                    return 0
                return access_token
            else:
                print("No refresh token found in .auth_token file.")
    
    # Use provided access token if available
    if args.access_token:
        return args.access_token
    
    # Use provided refresh token if available
    elif args.refresh_token:
        access_token = get_access_token_from_refresh_token(args.refresh_token)
        if not access_token:
            print("Failed to obtain access token using provided refresh token.")
            return 0
        return access_token
    
    # Use email and password for authentication if available
    elif args.email and args.password:
        tenant_id = args.tenant_id if args.tenant_id else get_tenant_id_from_email(args.email)
        if not tenant_id:
            print("Failed to determine tenant ID.")
            return 0
        access_token, _ = get_access_token_from_email(tenant_id, args.email, args.password)
        if not access_token:
            print("Failed to obtain access token using email and password.")
            return 0
        return access_token
    
    # Print error if no valid method for authentication
    else:
        print("Error: Email and password, or an access token or refresh token, are required for authentication.")
        return 0

def device_code_auth(client_id="d3590ed6-52b3-4102-aeff-aad2292ab01c", scope="https://graph.microsoft.com/.default offline_access"):
    tenant_id = "common"  # Use 'common' to support all Azure AD tenants
    device_code_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode"
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": client_id,
        "scope": scope
    }

    response = requests.post(device_code_url, data=data)

    if response.status_code != 200:
        print("Failed to initiate device code flow")
        print("Response code:", response.status_code)
        print("Response message:", response.text)
        return None

    device_code_info = response.json()
    device_code = device_code_info["device_code"]
    user_code = device_code_info["user_code"]
    verification_uri = device_code_info["verification_uri"]
    interval = device_code_info["interval"]

    print("To authenticate, please visit:", verification_uri)
    print("Enter the code:", user_code)

    printed_authorization_pending = False
    while True:
        token_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device_code
        }

        token_response = requests.post(token_url, data=token_data)

        if token_response.status_code == 200:
            token_info = token_response.json()            
            refresh_token = token_info.get("refresh_token")

            if refresh_token:
                with open(".auth_token", "w") as token_file:
                    token_file.write(refresh_token)
                print("[+] Authentication successful. Refresh token saved to .auth_token.")
                print(f"[+] Refresh token:\n{refresh_token}\n")
                return refresh_token
            else:
                print("[-] Failed to obtain refresh token")
                return None

        elif token_response.status_code in [400, 401]:
            error_info = token_response.json()
            if error_info.get("error") == "authorization_pending":
                if not printed_authorization_pending:
                    print("Authorization pending. Waiting for user to authenticate...")
                    printed_authorization_pending = True
                time.sleep(interval)
            else:
                print("[-] Failed to obtain access token")
                print("[-] Response code:", token_response.status_code)
                print("[-] Response message:", token_response.text)
                return None

        else:
            print("[-] Failed to obtain access token")
            print("[-] Response code:", token_response.status_code)
            print("[-] Response message:", token_response.text)
            return None