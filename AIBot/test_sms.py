import requests

url = "https://cpaas.messagecentral.com/verification/v3/send?countryCode=91&customerId=C-9FBBA6F36AA14EC&senderId=UTOMOB&type=SMS&flowType=SMS&mobileNumber=9885794107&message=Welcome to Message Central. We are delighted to have you here! - Powered by U2opia"

headers = {
'authToken': "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJDLTlGQkJBNkYzNkFBMTRFQyIsImlhdCI6MTc1NjIxOTA0MSwiZXhwIjoxOTEzODk5MDQxfQ.qOmJrqLFjoDb6n6-SzyQD5KsK2SbnL7VHcldy1jV1cN4d6KLmtNh_HciIQNngDS6FiKrunLDtS8Y4dzaQ1gETg"
}

response = requests.request("POST", url, headers=headers)

print(response.text)