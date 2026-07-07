from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from routers import (
    participant_router, category_router, budget_router,
    transaction_router, credit_card_router, debit_card_router, installment_router,
    account_payable_router, account_receivable_router, reimbursement_router,
    expected_purchase_router, statements_router, csv_ingestion_router,
    cash_flow_router, exchange_rate_router, transfer_router
)

app = FastAPI(
    title="Finanzas API",
    version="0.1.0",
    description="Shared personal finance system with business-accounting logic"
)

# Include routers
app.include_router(participant_router)
app.include_router(category_router)
app.include_router(budget_router)
app.include_router(transaction_router)
app.include_router(credit_card_router)
app.include_router(debit_card_router)
app.include_router(installment_router)
app.include_router(account_payable_router)
app.include_router(account_receivable_router)
app.include_router(reimbursement_router)
app.include_router(expected_purchase_router)
app.include_router(statements_router)
app.include_router(csv_ingestion_router)
app.include_router(cash_flow_router)
app.include_router(exchange_rate_router)
app.include_router(transfer_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Validation error"
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Database error occurred",
            "detail": str(exc)
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "An unexpected error occurred",
            "detail": str(exc)
        },
    )


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Finanzas API is running"}
