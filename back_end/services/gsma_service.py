from database import eid_collection
from models import EIDModel, ActivationCode, GetEimPackageRequest
from ultis.helper import *
from ultis.encoder.esipa_encoder import *
from ultis.decoder.esipa_decoder import *
from fastapi import HTTPException
from typing import Dict
from database import eid_collection
from models import *
from bson import ObjectId
import base64


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

            # Singleton instance
            from main import server_instance
            eim_trans_id = server_instance.generate_eim_transaction_id_hex()
            server_instance.update_eid_transId_map(eid_data.eidValue, eim_trans_id)

            # Encode the data in Base64
            encoded_data = await encode_profileDownloadTriggerRequest(profileDownloadData = activation_code, eimTransactionId = eim_trans_id, to_base64 = True)

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
    """

    smdp_address = eid_data.smdpAddress
    smdp_url = f"https://{smdp_address}/gsma/rsp2/es9plus/initiateAuthentication"

    # Ensure we have an HTTPS session
    if smdp_address not in sm_dp_sessions:
        sm_dp_sessions[smdp_address] = aiohttp.ClientSession()

    session = sm_dp_sessions[smdp_address]

    # Singleton instance
    from main import server_instance
    eid = server_instance.get_eid_from_transID(eid_data.eimTransactionId)

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
        logging.info(f"Forwarding InitiateAuthenticationRequest to SM-DP+: {smdp_url}")

        async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
            logging.info(f"Response from SM-DP+: {response.status}")

            # Log response content for debugging
            response_text = await response.text()
            logging.info(f"Response body: {response_text}")

            if (response.status == 200):
                # Parse JSON response
                try:
                    response_data = await response.json()
                except ValueError:
                    logging.error("Invalid JSON response")
                    raise

                # Check for transactionId
                if "transactionId" in response_data:
                    transaction_id = response_data["transactionId"]
                    logging.info(f"Found transactionId: {transaction_id}")

                    # Store the transactionId mapping
                    server_instance.edit_transId_for_eid_transId_map(eid, transaction_id)
                    server_instance.update_transId_smdp_map(transaction_id, smdp_address)

            # Return the response back to the client
            return {
                "status_code": response.status,
                "response_body": response_text
            }

    except aiohttp.ClientError as e:
        logging.error(f"Failed to connect to {smdp_url}: {e}")


async def handle_AuthenticateClient(eid_data: AuthenticateClient):
    """
    Forward the authentication response to the SM-DP+ server and return its response.
    """

    transId = eid_data.transactionId

    # Singleton instance
    from main import server_instance
    smdp_address = server_instance.get_smdp_from_transId(eid_data.transactionId)

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
        logging.info(f"Forwarding AuthenticateClient to SM-DP+: {smdp_url}")

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
    """
    transId = eid_data.transactionId

    # Singleton instance
    from main import server_instance
    smdp_address = server_instance.get_smdp_from_transId(eid_data.transactionId)
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
        logging.info(f"Forwarding GetBoundProfilePackage to SM-DP+: {smdp_url}")

        async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
            response_text = await response.text()
            logging.info(f"Response from SM-DP+: {response.status} - {response_text}")

            # Return the response back to the client
            return {
                "status_code": response.status,
                "response_body": response_text
            }

    except aiohttp.ClientError as e:
        logging.error(f"Failed to connect to {smdp_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Connection to SM-DP+ failed: {str(e)}")

async def handle_handleNotification(eid_data: HandleNotification):
    if eid_data.pendingNotification is not None:
        smdp_address = get_smdpAdd_from_pendingNotification(eid_data.pendingNotification)

        if smdp_address is None:
            raise HTTPException(
                status_code=200,
                detail=""
            )

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
            "pendingNotification": eid_data.pendingNotification
        }

        try:
            logging.info(f"Forwarding pendingNotification to SM-DP+: {smdp_url}")

            async with session.post(smdp_url, headers=headers, json=payload, ssl=False, timeout=10) as response:
                response_text = await response.text()
                logging.info(f"Response from SM-DP+: {response.status} - {response_text}")

                # Return the response back to the client
                return {
                    "status_code": response.status,
                    "response_body": response_text
                }
        except aiohttp.ClientError as e:
            logging.error(f"Failed to connect to {smdp_url}: {e}")
            raise HTTPException(status_code=500, detail=f"Connection to SM-DP+ failed: {str(e)}")

    elif eid_data.provideEimPackageResult is not None:
        eid = get_eid_from_provideEimPackageResult(eid_data.provideEimPackageResult)
        json_eimPackageResult = get_json_eimPackageResult_from_provideEimPackageResult(eid_data.provideEimPackageResult)

        if json_eimPackageResult[0] == "profileDownloadTriggerResult":
            # download profile notification
            profileDownloadTriggerResult = json_eimPackageResult[1]
            process_profileDownloadTriggerResult(profileDownloadTriggerResult)

        elif json_eimPackageResult[0] == "euiccPackageResult":
            # todo
            pass
        elif json_eimPackageResult[0] == "ePRAndNotifications":
            # todo
            pass
        elif json_eimPackageResult[0] == "ipaEuiccDataResponse":
            # todo
            pass
        elif json_eimPackageResult[0] == "eimPackageResultResponseError":
            # todo
            pass


async def process_profileDownloadTriggerResult(profileDownloadTriggerResult: Dict):
    profileDownloadTriggerResultData = profileDownloadTriggerResult.get("profileDownloadTriggerResultData")

    if profileDownloadTriggerResultData[0] == "profileInstallationResult":
        profileInstallationResult = profileDownloadTriggerResultData[1]
        finalResult = profileInstallationResult.get("finalResult")

        if finalResult[0] == "successResult":
            # todo
            logging.info("successResult notification !!!!")
            pass
        elif finalResult[0] == "errorResult":
            # todo
            pass
    elif profileDownloadTriggerResultData[0] == "profileDownloadError":
        # todo
        pass