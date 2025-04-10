import aiohttp
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change DEBUG → INFO to reduce logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Disable MongoDB internal debug logs
logging.getLogger("pymongo").setLevel(logging.WARNING)  # Ignore DEBUG logs from pymongo
logging.getLogger("motor").setLevel(logging.WARNING)  # Ignore DEBUG logs from Motor (async pymongo)


# Store active HTTPS sessions
sm_dp_sessions = {}

async def create_https_connection(smdp_address: str):
    """
    Create and store an HTTPS session with the given SM-DP+ address.
    Ensures the connection works by sending a POST request.
    """

    # Check if session already exists
    if smdp_address in sm_dp_sessions:
        logging.info(f"✅ Reusing existing HTTPS session for SM-DP+ address: {smdp_address}")
        return sm_dp_sessions[smdp_address]

    # Create new session
    session = aiohttp.ClientSession(base_url=f"https://{smdp_address}")
    sm_dp_sessions[smdp_address] = session
    logging.info(f"🔄 Created new HTTPS session for SM-DP+ address: {smdp_address}")

    # ✅ Debug log before making the request
    logging.debug("📤 Sending POST request to SM-DP+ server...")

    # ✅ Test connection by sending a POST request
    url = "/gsma/rsp2/es9plus/initiateAuthentication"
    headers = {
        "User-Agent": "CustomUserAgent/1.0",
        "X-Admin-Protocol": "gsma/rsp/v2_3",
        "Content-Type": "application/json;charset=UTF-8"
    }
    payload = {
        "euiccChallenge": "F+yp//kx14/cYL65/l++QQ==",
        "euiccInfo1": "vyA1ggMCBQCpFgQUgTcPUSXQsdQI1MOyMubSXnlb6/uqFgQUgTcPUSXQsdQI1MOyMubSXnlb6/s=",
        "smdpAddress": smdp_address
    }

    try:
        async with session.post(url, headers=headers, json=payload, ssl=False, timeout=5) as response:
            logging.debug(f"📥 Received response: Status={response.status}")
            response_text = await response.text()
            logging.info(f"📩 Response from SM-DP+: {response_text}")

            if response.status == 200:
                logging.info(f"✅ Successfully connected to {smdp_address} (Status: {response.status})")
            else:
                logging.warning(f"⚠️ Connected to {smdp_address}, but got unexpected status: {response.status}")

    except aiohttp.ClientError as e:
        logging.error(f"🚨 Failed to connect to {smdp_address}: {e}")
        await session.close()
        del sm_dp_sessions[smdp_address]  # Remove failed session
        return None  # Return None if connection fails

    return session