import requests
import base64

# Function to generate authentication token
def generate_auth_token(customer_id: str, password: str, email: str, country_code: int = 91):
    """Generate MessageCentral auth token.

    Params are sent as query parameters per API spec.
    Enhanced logging to surface exact server response on failures.
    """
    # Base64 encode the password as required by the API
    base64_password = base64.b64encode(password.encode("utf-8")).decode("utf-8")

    url = "https://cpaas.messagecentral.com/auth/v1/authentication/token"
    params = {
        "customerId": customer_id,
        "key": base64_password,
        "scope": "NEW",
        "country": str(country_code),
        "email": email,
    }

    headers = {
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        content_type = response.headers.get("content-type", "")

        # Prefer JSON if available
        data = None
        if "application/json" in content_type.lower():
            try:
                data = response.json()
            except ValueError:
                data = None

        if response.status_code != 200:
            print(f"Failed to generate token. HTTP {response.status_code}")
            if data is not None:
                # Print any helpful fields the API might return
                print("Response JSON:", data)
                msg = data.get("message") or data.get("error") or data.get("errorMessage")
                if msg:
                    print("Server message:", msg)
            else:
                # Fall back to raw text if not JSON
                print("Response text:", response.text[:500])
            return None

        # HTTP 200 - parse JSON body for token
        if not isinstance(data, dict):
            print("Unexpected non-JSON response for successful request.")
            print("Response text:", response.text[:500])
            return None

        status_val = data.get("status")
        # Token may be at root or nested in data
        token = data.get("token") or (data.get("data") or {}).get("token")

        if status_val == 200 and token:
            print("Token generated successfully.")
            print(f"Authentication Token: {token}")
            return token

        # If we reach here, print diagnostics
        print("Error generating token: ", data.get("message") or data.get("error") or "Unknown error")
        print("Full response JSON:", data)
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error requesting token: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Replace these with your actual values
    customer_id = "C-9FBBA6F36AA14EC"  # Replace with your actual customer ID from Message Central
    password = "HippoCampus@2025"  # Your password
    email = "rohit.tirunellai@gmail.com"  # Replace with your email

    # Call the function to generate the token
    auth_token = generate_auth_token(customer_id, password, email)

    if auth_token:
        print("Successfully generated token:", auth_token)
    else:
        print("Failed to generate token.")