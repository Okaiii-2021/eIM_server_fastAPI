import ctypes
import base64


def encodeProfileDownloadDataAsn(activationcode_utf8: str):
    # This function only encode for activation code
    # TODO handle when activation code > 128
    
    # Convert AC utf8 to hex
    AC_hex = activationcode_utf8.encode("utf-8").hex()
    AC_hex_bytes = bytes.fromhex(AC_hex)
    AC_len = len(AC_hex_bytes)
    AC_data = bytes([0x80, AC_len]) + AC_hex_bytes
    ProfileDownloadData_len = AC_len + 2
    ProfileDownloadData_data = bytes([0xA0, ProfileDownloadData_len]) + AC_data
    
    return ProfileDownloadData_data



def encodeTransactionIdAsn(transactionId: str):
    transactionID_hex_bytes = bytes.fromhex(transactionId)
    transactionID_len = len(transactionID_hex_bytes)
    transactionId_data = bytes([0x82, transactionID_len]) + transactionID_hex_bytes
    
    return transactionId_data




def encodeProfileDownloadTriggerRequest(ProfileDownloadData_data: bytes, transactionId_data: bytes):
    # ProfileDownloadTriggerRequest tag 'BF54'
    
    total_length = 0
    
    if(ProfileDownloadData_data):
        total_length += len(ProfileDownloadData_data)
    
    if(transactionId_data):
        total_length += len(transactionId_data)
    
    
    total_byte = total_length + 2 + 1 # 2 bytes for tag BF54, 1 byte for len
    
    # Define buffer size
    buffer_size = total_byte
    buffer = bytearray(buffer_size)
    
    offset = 0
    buffer[offset : offset + 2] = 0xBF54
    offset += 2

    buffer[offset] = total_length
    offset += 1
    
    # fill ProfileDownloadData
    buffer[offset : offset + len(ProfileDownloadData_data)] = ProfileDownloadData_data
    offset += len(ProfileDownloadData_data)

    # fill TransactionId
    buffer[offset : offset + len(transactionId_data)] = transactionId_data
    offset += len(transactionId_data)
    
    print(offset)

    # Convert buffer to base64
    base64_encoded = base64.b64encode(buffer)
    
    return base64_encoded






    
    
    
    
    
    
    
    
        



