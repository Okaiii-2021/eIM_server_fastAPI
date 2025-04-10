from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import asyncio
import logging
import socket
import ssl

from routes.eid_routes import eid_router
from routes.gsma_routes import gsma_router

class eIM_server:
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
        self.SSL_CERT_FILE = "/home/okai/work_space/TMA_project/eim_server/back_end/certs/server.crt"
        self.SSL_KEY_FILE = "/home/okai/work_space/TMA_project/eim_server/back_end/certs/server.key"

        # # Register API routes
        self.app.include_router(eid_router, prefix="/api")
        self.app.include_router(gsma_router)
        
    def setup_middlewares(self):
        """Set up CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all frontend requests (change for production)
            allow_credentials=True,
            allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
            allow_headers=["*"],  # Allow all headers
        )

    async def check_verified_client(self, request: Request):
        """Middleware: Allow only verified clients to access APIs."""
        client_ip = request.client.host

        if client_ip not in self.verified_clients:
            raise HTTPException(status_code=403, detail="Client has not established a secure HTTPS connection")

        return client_ip

