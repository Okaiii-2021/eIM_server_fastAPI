# routes/eid_routes.py
from fastapi import APIRouter, Depends
from models import *
from services.gsma_service import *
from database import eid_collection


gsma_router = APIRouter()

############################################
############# For esipa ####################
############################################

@gsma_router.post("/gsma/rsp2/esipa/getEimPackage")
async def getEimPackage(eid_data: GetEimPackageRequest):
    print("Received Data:", eid_data)
    return await check_pending_packet(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/initiateAuthentication")
async def handle_init_authen(eid_data: InitiateAuthenticationRequest):
    print("Received Data:", eid_data)
    return await handle_initiate_authentication(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/authenticateClient")
async def handle_authenticate_server(eid_data: AuthenticateClient):
    print("Received Data: ", eid_data)
    return await handle_AuthenticateClient(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/getBoundProfilePackage")
async def handle_get_bound_profilepackage(eid_data: GetBoundProfilePackage):
    """
    API Route: Prepare Download request forwarding to SM-DP+.
    """
    logging.info("Received GetBoundProfilePackage: ",eid_data)
    return await handle_getBoundProfilePackage(eid_data)

@gsma_router.post("/gsma/rsp2/esipa/handleNotification")
async def handle_handle_notification(eid_data: HandleNotification):
    """
    API Route: Prepare Download request forwarding to SM-DP+.
    """
    logging.info("Received PrepareDownload request")
    return await handle_handleNotification(eid_data)
