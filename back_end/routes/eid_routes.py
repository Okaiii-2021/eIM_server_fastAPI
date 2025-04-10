# routes/eid_routes.py
from fastapi import APIRouter
from models import EIDModel, ActivationCode
from services.eid_service import create_eid, get_all_eids, get_eid_by_name, add_activation_code_to_eid
from database import eid_collection  # ✅ Ensure the database is imported


eid_router = APIRouter()

# ✅ Function to Convert MongoDB Document to JSON-Compatible Format
def serialize_eid(eid):
    return {
        "_id": str(eid["_id"]),  # Convert ObjectId to string
        "eid_name": eid["eid_name"],
        "description": eid["description"],
        "num_profiles": eid["num_profiles"],
        "active_profile": eid["active_profile"],
        "activation_codes": eid.get("activation_codes", [])  # Ensure it's always a list
    }

@eid_router.get("/")
def root():
    return {"message": "Welcome to the EIM API!"}

@eid_router.post("/add-eid/")
async def add_eid(eid_data: EIDModel):
    return await create_eid(eid_data)

@eid_router.get("/eids/")
async def list_eids():
    try:
        eids = await get_all_eids()  # ✅ Call the service layer
        return eids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eid_router.get("/eid/{eid_name}")
async def get_eid_details(eid_name: str):
    return await get_eid_by_name(eid_name)


@eid_router.post("/eid/{eid_name}/add-activation")
async def add_activation_code(eid_name: str, activation: ActivationCode):
    """Add an activation code to an existing EID"""
    
    return await add_activation_code_to_eid(eid_name, activation)
