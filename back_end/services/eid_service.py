# services/eid_service.py
from database import eid_collection
from models import EIDModel, ActivationCode
from fastapi import HTTPException
from bson import ObjectId

async def create_eid(eid_data: EIDModel):
    """Create a new EID entry in the database."""
    existing_eid = await eid_collection.find_one({"eid_name": eid_data.eid_name})
    if existing_eid:
        raise HTTPException(status_code=400, detail="EID already exists")

    eid_dict = eid_data.dict()
    await eid_collection.insert_one(eid_dict)
    return {"message": "EID added successfully!", "eid_name": eid_data.eid_name}

async def get_all_eids():
    """Fetch all EIDs from MongoDB."""
    eids = await eid_collection.find().to_list(None)
    # ✅ Convert ObjectId `_id` to string to prevent serialization issues
    for eid in eids:
        eid["_id"] = str(eid["_id"])
    return eids

async def get_eid_by_name(eid_name: str):
    """Fetch a single EID and its details from MongoDB."""
    eid = await eid_collection.find_one({"eid_name": eid_name})
    if not eid:
        raise HTTPException(status_code=404, detail="EID not found")
    
    # Convert ObjectId to string
    eid["_id"] = str(eid["_id"])
    return eid

async def add_activation_code_to_eid(eid_name: str, activation: ActivationCode):
    """Add an activation code to an existing EID"""
    
    # Find EID
    eid_data = await eid_collection.find_one({"eid_name": eid_name})
    if not eid_data:
        raise HTTPException(status_code=404, detail="EID not found")

    # Prepare new activation code
    new_activation = {
        "code": activation.code,
        "iccid": "",  # Default empty ICCID (Modify if needed)
        "state": "available"
    }

    # Update MongoDB document
    await eid_collection.update_one(
        {"_id": ObjectId(eid_data["_id"])},  # ✅ Ensure ObjectId conversion
        {"$push": {"activation_codes": new_activation}}
    )

    return {"message": "Activation code added successfully", "eid_name": eid_name}
