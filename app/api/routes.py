from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, citizens, licenses, applications, audit, transactions, mock, external

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(citizens.router, prefix="/citizens", tags=["citizens"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["licenses"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(mock.router, prefix="/mock", tags=["mock"])
api_router.include_router(external.router, prefix="/external", tags=["external"]) 