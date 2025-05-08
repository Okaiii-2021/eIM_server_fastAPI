from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import asyncio
import logging
import socket
import ssl
from pathlib import Path
from typing import Dict
import secrets

from routes.eid_routes import eid_router
from routes.gsma_routes import gsma_router

base_dir = Path(__file__).resolve().parent
print(base_dir)

class SingletonMeta(type):
    _instances = {}

    def __call__(cls):
        if cls not in cls._instances:
            instance = super().__call__()
            cls._instances[instance] = instance
        return cls._instances[instance]

class eIM_server(metaclass = SingletonMeta):
    def __init__(self):
        """Initialize the FastAPI app and manage server state."""
        self.app = FastAPI()

        # Middleware (CORS, logging, etc.)
        self.setup_middlewares()

        # Store verified clients (clients that established an HTTPS connection)
        self.verified_clients = set()

        # Store HTTPS sessions for clients
        self.sm_dp_sessions = {}

        # Load SSL certificate and key for HTTPS connections
        self.SSL_CERT_FILE = base_dir / "certs" / "server.crt"
        self.SSL_KEY_FILE = base_dir / "certs" / "server.key"

        # # Register API routes
        self.app.include_router(eid_router, prefix="/api")
        self.app.include_router(gsma_router)

        # Map EIDs to current transactionID
        self.eid_transId_map: Dict[str, str] = {"89041030891636202427100000006394": "532FF17955D34F019A7EB98736377DD2"}

        # Map TransactionID to SMDP+ address
        self.transId_smdp_map: Dict[str, str] = {"": ""}

    def setup_middlewares(self):
        """Set up CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all frontend requests (change for production)
            allow_credentials=True,
            allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
            allow_headers=["*"],  # Allow all headers
        )

    @staticmethod
    def generate_eim_transaction_id_hex() -> str:
        """Returns a 32-character hex string (16 bytes)."""
        return secrets.token_hex(16)  # 32 chars (2 chars per byte)

    def update_eid_transId_map(self, eid: str, trans_id: str) -> None:
        if not eid or not trans_id:
            raise ValueError("EID and TransactionID must not be empty!")
        self.eid_transId_map[eid] = trans_id

    def edit_transId_for_eid_transId_map(self, eid: str, trans_id:str) -> None:
        if eid not in self.eid_transId_map.keys():
            raise ValueError("EID not exists!")
        self.eid_transId_map[eid] = trans_id

    def get_eid_from_transID(self, transID: str) -> str:
        for key, value in self.eid_transId_map.items():
            if transID == value:
                return key
        raise ValueError(f"transID '{transID}' does not exist!")

    def is_transId_valid(self, transId: str) -> bool:
        return transId in self.eid_transId_map.values()

    def update_transId_smdp_map(self, transId: str, smdp_add: str) -> None:
        if not transId or not smdp_add:
            raise ValueError("transId and smdp_add must not be empty!")
        self.transId_smdp_map[transId] = smdp_add

    def get_smdp_from_transId(self, transId: str) -> str:
        for key, value in self.transId_smdp_map.items():
            if key == transId:
                return value
        raise ValueError(f"transID '{transId}' does not exist!")


