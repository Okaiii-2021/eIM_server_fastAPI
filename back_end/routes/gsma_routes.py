# routes/eid_routes.py
from fastapi import APIRouter, Depends
from models import *
from services.gsma_service import *
from database import eid_collection  # ✅ Ensure the database is imported
# from main import server_instance


gsma_router = APIRouter()

# server_instance.app.include_router(gsma_router)

###################################################
############# For esipa
###################################################

@gsma_router.get("/gsma/rsp2/esipa/getEimPackage")
async def getEimPackage(eid_data: GetEimPackageRequest):
    print("Received Data:", eid_data)
    return await check_pending_packet(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/initiateAuthentication")
async def handle_init_authen(eid_data: InitiateAuthenticationRequest):
    print("Received Data:", eid_data)
    return await handle_initiate_authentication(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/AuthenticateServerResponseRequest")
async def handle_authenticate_server(eid_data: AuthenticateServerResponseRequest):
    print("Received Data:", eid_data)
    return await handle_AuthenticateServerResponseRequest(eid_data)


@gsma_router.post("/gsma/rsp2/es9plus/getBoundProfilePackage")
async def handle_get_bound_profilepackage(eid_data: GetBoundProfilePackage):
    """
    API Route: Prepare Download request forwarding to SM-DP+.
    """
    logging.info("✅ Received PrepareDownload request")
    return await handle_getBoundProfilePackage(eid_data)
