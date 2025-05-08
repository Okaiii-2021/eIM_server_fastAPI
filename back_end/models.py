# models.py
from pydantic import BaseModel, Field, StringConstraints, root_validator
import base64
from typing import Annotated
from typing import List, Optional

class ActivationCode(BaseModel):
    code: str
    iccid: str
    state: str  # Options: Deleted, Available, Sent, Complete

class EIDModel(BaseModel):
    eid_name: str
    description: str
    num_profiles: int = Field(ge=0)  # Ensure `num_profiles` is >= 0
    active_profile: Optional[str] = None  # 👈 Optional field
    activation_codes: List[ActivationCode] = []

# Định nghĩa kiểu EID có regex kiểm tra 32 chữ số
EIDType = Annotated[str, StringConstraints(pattern=r"^[0-9]{32}$")]
# Define types
Base64Type = Annotated[str, StringConstraints(pattern=r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$")]

# Define constraints for transactionId (2-32 characters, HEX)
TransactionIDType = Annotated[str, StringConstraints(pattern=r"^[0-9A-F]{2,32}$")]



class GetEimPackageRequest(BaseModel):
    eidValue: EIDType = Field(..., description="EID as described in SGP.22 [4]")
    notifyStateChange: bool = Field(None, description="Notification to the eIM that it should update its information about the eUICC")
    rPlmn: str | None = Field(None, description="MCC and MNC of the last registered PLMN, base64 encoded")

    # Optional: Validate rPlmn is a valid Base64 string
    @classmethod
    def validate_rPlmn(cls, value: str) -> str:
        if value:
            try:
                base64.b64decode(value, validate=True)
            except Exception:
                raise ValueError("rPlmn must be a valid base64 encoded string")
        return value

# Define Base64 validation function
def validate_base64(value: str) -> str:
    """Ensure the input string is a valid Base64 encoded value."""
    try:
        base64.b64decode(value, validate=True)
    except Exception:
        raise ValueError(f"'{value}' is not a valid Base64-encoded string.")
    return value

class InitiateAuthenticationRequest(BaseModel):
    euiccChallenge: Base64Type = Field(..., description="Base64 encoding of the eUICC Challenge as defined in SGP.22 [4]")
    euiccInfo1: Base64Type = Field(..., description="Base64 encoding of euiccinfo1 as defined in SGP.22 [4]")
    smdpAddress: str = Field(..., description="SM-DP+ Address as defined in SGP.22 [4]")
    eimTransactionId: TransactionIDType | None = Field(
        None, description="eimTransactionId as defined in section 6.3.2.1 SGP32"
    )

    # Validate Base64 fields
    @classmethod
    def validate_base64_fields(cls, value: str) -> str:
        return validate_base64(value)

    # Apply validation to Base64 fields
    _validate_euiccChallenge = validate_base64_fields.__func__
    _validate_euiccInfo1 = validate_base64_fields.__func__
    
class AuthenticateClient(BaseModel):
    transactionId: TransactionIDType = Field(
        ..., description="TransactionID as defined in SGP.22 [4]"
    )
    authenticateServerResponse: str = Field(
        ..., description="AuthenticateServerResponse as provided by ES10b.AuthenticateServer, possibly in compact format"
    )

    # Validate Base64 field
    @classmethod
    def validate_base64(cls, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except Exception:
            raise ValueError("authenticateServerResponse must be a valid Base64-encoded string")
        return value

    # Apply Base64 validation
    _validate_authenticateServerResponse = validate_base64.__func__

class GetBoundProfilePackage(BaseModel):
    transactionId: TransactionIDType = Field(
        ..., description="TransactionID as defined in SGP.22 [4]"
    )
    prepareDownloadResponse: str = Field(
        ..., description="PrepareDownloadResponse as provided by ES10b.PrepareDownload, possibly in compact format"
    )

    # Validate Base64 field
    @classmethod
    def validate_base64(cls, value: str) -> str:
        try:
            base64.b64decode(value, validate=True)
        except Exception:
            raise ValueError("prepareDownloadResponse must be a valid Base64-encoded string")
        return value

    # Apply Base64 validation
    _validate_prepareDownloadResponse = validate_base64.__func__

class HandleNotification(BaseModel):
    pendingNotification: Base64Type | None = Field(
        None, description="PendingNotification as defined in section 5.14.7 SGP32"
    )
    provideEimPackageResult: Base64Type | None = Field(
        None, description="ProvideEimPackageResult as defined in section 6.3.2.7 SGP32"
    )

    @root_validator(pre=True)
    def check_only_one_field(cls, values):
        pendingNotification = values.get("pendingNotification")
        provideEimPackageResult = values.get("provideEimPackageResult")
        if ((pendingNotification is None) == (provideEimPackageResult is None)) and ((pendingNotification is Base64Type) == (provideEimPackageResult is Base64Type)) :
            raise ValueError("Exactly one of 'pendingNotification' or 'provideEimPackageResult' must be set")
        return values







