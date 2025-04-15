from database import eid_collection
from models import EIDModel, ActivationCode, GetEimPackageRequest
from ultis.helper import *
from ultis.encoder.esipa_encoder import *
from fastapi import HTTPException


from database import eid_collection
from models import *
from bson import ObjectId
import base64

# Store active HTTPS sessions
sm_dp_sessions = {}

async def check_pending_packet(eid_data: GetEimPackageRequest):
    """
    Check if an activation code is available for the given eid_name.
    If found and in 'available' state, move it to 'sent' and return response.
    If no activation codes are available, return an error.
    """

    # Search for the EID entry in the database
    eid_entry = await eid_collection.find_one({"eid_name": eid_data.eidValue})

    if not eid_entry:
        return {"eimPackageError": 1}  # No EIM Package Available

    # Check if there is an activation code in 'available' state
    for activation in eid_entry.get("activation_codes", []):
        if activation["state"] == "available":
            activation_code = activation["code"]

            # Move the state to 'sent'
            await eid_collection.update_one(
                {"_id": ObjectId(eid_entry["_id"]), "activation_codes.code": activation_code},
                {"$set": {"activation_codes.$.state": "sent"}}
            )

            # Encode the data in Base64
            encoded_data = await encode_profileDownloadTriggerRequest(activation_code, to_base64 = True)

            return {
                "profileDownloadTriggerRequest": encoded_data,
                "header": {
                    "functionExecutionStatus": {"status": "Executed-Success"}
                }
            }

    # If no activation codes are found
    return {"eimPackageError": 127}  # Undefined Error

async def handle_initiate_authentication(eid_data: InitiateAuthenticationRequest):
    """
    Forward information to the SM-DP+ server specified in "smdpAddress".

    Steps:
    1. Create an HTTPS connection with the SM-DP+ server.
    2. Forward the authentication request to the SM-DP+ server.
    3. Do not send any response back to IPA.
    """

    smdp_address = eid_data.smdpAddress
    smdp_url = f"https://{smdp_address}/gsma/rsp2/es9plus/initiateAuthentication"

    # Ensure we have an HTTPS session
    if smdp_address not in sm_dp_sessions:
        sm_dp_sessions[smdp_address] = aiohttp.ClientSession()

    session = sm_dp_sessions[smdp_address]

    # Prepare headers and payload
    headers = {
        "User-Agent": "CustomUserAgent/1.0",
        "X-Admin-Protocol": "gsma/rsp/v2_3",
        "Content-Type": "application/json;charset=UTF-8"
    }

    payload = {
        "euiccChallenge": eid_data.euiccChallenge,
        "euiccInfo1": eid_data.euiccInfo1,
        "smdpAddress": eid_data.smdpAddress
    }

    try:
        logging.info(f"Forwarding authentication request to SM-DP+: {smdp_url}")

        async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
            logging.info(f"Response from SM-DP+: {response.status}")

            # Log response content for debugging
            response_text = await response.text()
            logging.info(f"Response body: {response_text}")

            # Return the response back to the client
            return {
                "status_code": response.status,
                "response_body": response_text
            }

    except aiohttp.ClientError as e:
        logging.error(f"Failed to connect to {smdp_url}: {e}")


async def handle_AuthenticateServerResponseRequest(eid_data: AuthenticateServerResponseRequest):
    """
    Forward the authentication response to the SM-DP+ server and return its response.

    Steps:
    1. Create an HTTPS connection with the SM-DP+ server.
    2. Forward the request to the SM-DP+ server.
    3. Return the response received from SM-DP+ to the client.
    """

    smdp_address = "rsp.truphone.com"  # Replace with actual SMDP address
    smdp_url = f"https://{smdp_address}/gsma/rsp2/es9plus/authenticateClient"

    # Ensure we have an HTTPS session
    if smdp_address not in sm_dp_sessions:
        sm_dp_sessions[smdp_address] = aiohttp.ClientSession()

    session = sm_dp_sessions[smdp_address]

    # Prepare headers and payload
    headers = {
        "User-Agent": "CustomUserAgent/1.0",
        "X-Admin-Protocol": "gsma/rsp/v2_3",
        "Content-Type": "application/json;charset=UTF-8"
    }

    payload = {
        "transactionId": eid_data.transactionId,
        "authenticateServerResponse": eid_data.authenticateServerResponse
    }

    try:
        logging.info(f"Forwarding authentication response to SM-DP+: {smdp_url}")

        async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
            response_text = await response.text()
            logging.info(f"Response from SM-DP+: {response.status} - {response_text}")

            # ✅ Return the response back to the client
            return {
                "status_code": response.status,
                "response_body": response_text
            }

    except aiohttp.ClientError as e:
        logging.error(f"Failed to connect to {smdp_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Connection to SM-DP+ failed: {str(e)}")

async def handle_getBoundProfilePackage(eid_data: GetBoundProfilePackage):
    """
    Forward the prepareDownload response to the SM-DP+ server and return its response.

    Steps:
    1. Create an HTTPS connection with the SM-DP+ server.
    2. Forward the request to the SM-DP+ server.
    3. Return the response received from SM-DP+ to the client.
    """

    smdp_address = "rsp.truphone.com"  # Replace with actual SM-DP+ address
    smdp_url = f"https://{smdp_address}/gsma/rsp2/es9plus/getBoundProfilePackage"

    # Ensure we have an HTTPS session
    if smdp_address not in sm_dp_sessions:
        sm_dp_sessions[smdp_address] = aiohttp.ClientSession()

    session = sm_dp_sessions[smdp_address]

    # Prepare headers and payload
    headers = {
        "User-Agent": "CustomUserAgent/1.0",
        "X-Admin-Protocol": "gsma/rsp/v2_3",
        "Content-Type": "application/json;charset=UTF-8"
    }

    payload = {
        "transactionId": eid_data.transactionId,
        "prepareDownloadResponse": eid_data.prepareDownloadResponse
    }

    try:
        logging.info(f"Forwarding GetBoundProfilePackage response to SM-DP+: {smdp_url}")

        async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
            response_text = await response.text()
            logging.info(f"Response from SM-DP+: {response.status} - {response_text}")

            # ✅ Return the response back to the client
            return {
                "status_code": response.status,
                "response_body": response_text
            }

    except aiohttp.ClientError as e:
        logging.error(f"Failed to connect to {smdp_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Connection to SM-DP+ failed: {str(e)}")

