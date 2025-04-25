import json
import requests

# Read proxy config from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

end_point = config['endPoint']
api_key = config['apiKey']

import requests
import json

def generate(
    model: str,
    system: str,
    query: str,
    temperature: float | None = None,
    lastk: int | None = None,
    session_id: str | None = None,
    rag_threshold: float | None = 0.5,
    rag_usage: bool | None = False,
    rag_k: int | None = 0
):
    headers = {
        'x-api-key': api_key
    }

    request = {
        'model': model,
        'system': system,
        'query': query,
        'temperature': temperature,
        'lastk': lastk,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_usage': rag_usage,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            res = json.loads(response.text)
            msg = {'response': res['result'], 'rag_context': res['rag_context']}
        else:
            # HTTP Status code explanations
            status_explanations = {
                400: "Bad Request: The server could not understand the request due to invalid syntax.",
                401: "Unauthorized: The request lacks valid authentication credentials.",
                403: "Forbidden: The client does not have access rights to the content.",
                404: "Not Found: The server cannot find the requested resource.",
                500: "Internal Server Error: The server encountered an unexpected condition that prevented it from fulfilling the request.",
                502: "Bad Gateway: The server received an invalid response from the upstream server.",
                503: "Service Unavailable: The server is not ready to handle the request, often due to temporary overload or maintenance.",
                504: "Gateway Timeout: The server did not receive a timely response from an upstream server."
            }

            # Get the explanation of the response status code or a generic message if unknown
            status_message = status_explanations.get(response.status_code, "Unknown Error: The server returned an unrecognized status code.")
            msg = f"Error: Received response code {response.status_code}. {status_message}"

    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"

    return msg



def upload(multipart_form_data):

    headers = {
        'x-api-key': api_key
    }

    msg = None
    try:
        response = requests.post(end_point, headers=headers, files=multipart_form_data)
        
        if response.status_code == 200:
            msg = "Successfully uploaded. It may take a short while for the document to be added to your context"
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    
    return msg


def pdf_upload(
    path: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }

    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'file': (None, open(path, 'rb'), "application/pdf")
    }

    response = upload(multipart_form_data)
    return response

def text_upload(
    text: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }


    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'text': (None, text, "application/text")
    }


    response = upload(multipart_form_data)
    return response

def retrieve(
    query: str,
    session_id: str,
    rag_threshold: float,
    rag_k: int
    ):

    headers = {
        'x-api-key': api_key,
        'request_type': 'retrieve'
    }

    request = {
        'query': query,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            msg = json.loads(response.text)
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg  
