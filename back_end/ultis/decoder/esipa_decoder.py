import asn1tools
import base64
import os
from pprint import pprint

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

asn1_schema_path = os.path.join(script_dir, "../asn1/esim.asn1")
asn1_PKIX1Explicit88_schema_path = os.path.join(script_dir, "../asn1/PKIX1Explicit88.asn1")
asn1_PKIX1Implicit88_schema_path = os.path.join(script_dir, "../asn1/PKIX1Implicit88.asn1")

# Compile the ASN.1 schema using DER encoding
asn_schema = asn1tools.compile_files([asn1_schema_path, asn1_PKIX1Explicit88_schema_path, asn1_PKIX1Implicit88_schema_path], codec="der")


async def get_smdpAdd_from_pendingNotification(pendingNotification: str) -> str:

    smdp_address = None

    # Convert Base64 to binary DER format
    encoded_der = base64.b64decode(pendingNotification)

    decoded_pendingNotification = asn_schema.decode("PendingNotification", encoded_der)
    if "profileInstallationResult" == decoded_pendingNotification[0]:
        profile_installation_result = decoded_pendingNotification[1]
        profile_data = profile_installation_result["profileInstallationResultData"]
        notification_metadata = profile_data["notificationMetadata"]
        notification_address = notification_metadata["notificationAddress"]
        print("Notification Address:", notification_address)
        smdp_address = notification_address
    else:
        print("Other type of notification received:", decoded_pendingNotification)

    return smdp_address


async def get_eid_from_provideEimPackageResult(provideEimPackageResult: str) -> str:
    # Convert Base64 to binary DER format
    encoded_der = base64.b64decode(provideEimPackageResult)
    decoded_provideEimPackageResult = asn_schema.decode("ProvideEimPackageResult", encoded_der)
    eid = decoded_provideEimPackageResult.get("eidValue")
    return eid

async def get_json_eimPackageResult_from_provideEimPackageResult(provideEimPackageResult: str) -> str:
    # Convert Base64 to binary DER format
    encoded_der = base64.b64decode(provideEimPackageResult)
    json_provideEimPackageResult = asn_schema.decode("ProvideEimPackageResult", encoded_der)
    json_eimPackageResult = json_provideEimPackageResult.get("eimPackageResult")
    return json_eimPackageResult

