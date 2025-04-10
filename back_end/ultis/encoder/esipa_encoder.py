import asn1tools
import os
import base64

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to esim.asn1 dynamically
asn1_schema_path = os.path.join(script_dir, "../asn1/esim.asn1")

# Biên dịch schema từ file .asn1
codec = asn1tools.compile_files(asn1_schema_path, "der")

async def encode_profileDownloadTriggerRequest(profileDownloadData : str, eimTransactionId : str = None, to_base64: bool = False):
    """
    Encodes ProfileDownloadTriggerRequest using ASN.1 DER format.

    :param profileDownloadData: Activation code string (e.g., "1$rsp.truphone.com$QRF-SPEEDTEST")
    :param eimTransactionId: Hex string representing the transaction ID (e.g., "F0466F057454405F9909E77688D146BF")
    :return: ASN.1 encoded bytes
    """

    data = {}
    
    # ProfileDownloadData ::= CHOICE {
    # activationCode [0] UTF8String (SIZE(0..255)),
    # contactDefaultSmdp [1] NULL,
    # contactSmds [2] SEQUENCE {
    # smdsAddress UTF8String OPTIONAL
    # }
    # } 
    # currently support activationCode
    if(profileDownloadData):
        data["profileDownloadData"] = ("activationCode", profileDownloadData)
    
    if(eimTransactionId):
        data["eimTransactionId"] = (bytes.fromhex("F0466F057454405F9909E77688D146BF"))
    
    # Encode to ASN.1 DER
    encoded_data = codec.encode("ProfileDownloadTriggerRequest", data)
    
    # Convert to Base64 if requested
    if to_base64:
        return base64.b64encode(encoded_data).decode()
    
    return encoded_data

