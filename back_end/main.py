import ssl
import uvicorn
import logging
from server_class import eIM_server

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Create an instance of the Server class
server_instance = eIM_server()

# Create SSL context
# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# ssl_context.load_cert_chain(certfile=server_instance.SSL_CERT_FILE, keyfile=server_instance.SSL_KEY_FILE)

# Set ciphers explicitly
# ssl_context.set_ciphers("ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256")

# Ensure only TLS 1.2+ is allowed
# ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

if __name__ == "__main__":
    logging.info("🔹 Starting Uvicorn with SSL debug mode...")
    uvicorn.run(
        server_instance.app,
        host="0.0.0.0",
        port=8443,
        ssl_certfile=server_instance.SSL_CERT_FILE,
        ssl_keyfile=server_instance.SSL_KEY_FILE,
        ssl_version=ssl.PROTOCOL_TLS_SERVER,  # Set SSL version
        ssl_ciphers="ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256",  # Explicit ciphers
        log_level="debug"
    )
