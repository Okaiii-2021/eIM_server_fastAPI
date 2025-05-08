import aiohttp
import logging


# Store active HTTPS sessions
sm_dp_sessions = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change DEBUG → INFO to reduce logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Disable MongoDB internal debug logs
logging.getLogger("pymongo").setLevel(logging.WARNING)  # Ignore DEBUG logs from pymongo
logging.getLogger("motor").setLevel(logging.WARNING)  # Ignore DEBUG logs from Motor (async pymongo)
