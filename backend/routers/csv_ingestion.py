"""
API routes for CSV ingestion.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from services.csv_ingestion import CSVIngestionService, CSVIngestionError

router = APIRouter(prefix="/csv", tags=["csv-ingestion"])


@router.post("/import", status_code=status.HTTP_200_OK)
def import_transactions_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import transactions from Google Forms CSV file.

    Expected CSV format:
    - Marca temporal: Form submission timestamp
    - Fecha del movimiento: Transaction date (DD/MM/YYYY)
    - Responsable: Participant name
    - Tipo: "Gasto" or "Ingreso"
    - Monto: Amount
    - Descripción: Description
    - Categoria: Main category
    - Subcategorias [X]: Subcategory columns (only relevant one filled)

    Returns:
        Import statistics including success count and errors
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        # Import from CSV
        stats = CSVIngestionService.import_from_csv(db, file.file)

        return {
            "message": "CSV import completed",
            "statistics": stats
        }

    except CSVIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during import: {str(e)}"
        )
    finally:
        file.file.close()


@router.post("/validate", status_code=status.HTTP_200_OK)
def validate_csv_format(
    file: UploadFile = File(...),
):
    """
    Validate CSV file format without importing data.

    Returns:
        Validation results
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    try:
        result = CSVIngestionService.validate_csv_format(file.file)

        if not result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Invalid CSV format")
            )

        return {
            "message": "CSV format is valid",
            "details": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during validation: {str(e)}"
        )
    finally:
        file.file.close()
