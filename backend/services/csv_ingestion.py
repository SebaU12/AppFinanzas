"""
CSV Ingestion Service for Google Forms data.
"""
from datetime import datetime
from decimal import Decimal
from typing import BinaryIO
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.transaction import Transaction, PaymentMethod
from models.category import Category, CategoryType
from models.participant import Participant


class CSVIngestionError(Exception):
    """Custom exception for CSV ingestion errors."""
    pass


class CSVIngestionService:
    """Service for importing transactions from Google Forms CSV."""

    # Mapping from Spanish form values to our enums
    TIPO_MAPPING = {
        "Gasto": CategoryType.EXPENSE,
        "Ingreso": CategoryType.INCOME,
    }

    # Participant name mapping (customize as needed)
    PARTICIPANT_MAPPING = {
        "Copain": "Lu",
        "Copine": "Chebos",
        "Lu": "Lu",
        "Chebos": "Chebos",
    }

    @staticmethod
    def import_from_csv(db: Session, file: BinaryIO) -> dict:
        """
        Import transactions from CSV file.

        Args:
            db: Database session
            file: CSV file (binary IO)

        Returns:
            dict with import statistics (success, errors, skipped)
        """
        # Read CSV with pandas
        try:
            df = pd.read_csv(file)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
        except Exception as e:
            raise CSVIngestionError(f"Failed to read CSV file: {str(e)}")

        # Validate required columns
        required_columns = [
            "Fecha del movimiento",
            "Responsable",
            "Tipo",
            "Monto",
            "Descripción",
            "Categoria",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise CSVIngestionError(f"Missing required columns: {', '.join(missing_columns)}")

        # Track statistics
        stats = {
            "total": len(df),
            "success": 0,
            "errors": [],
            "skipped": 0,
        }

        # Process each row
        for idx, row in df.iterrows():
            try:
                transaction = CSVIngestionService._process_row(db, row, idx)
                if transaction:
                    db.add(transaction)
                    stats["success"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["errors"].append({
                    "row": idx + 2,  # +2 because Excel rows start at 1 and header is row 1
                    "error": str(e)
                })

        # Commit all successful imports
        if stats["success"] > 0:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise CSVIngestionError(f"Failed to commit transactions: {str(e)}")

        return stats

    @staticmethod
    def _process_row(db: Session, row: pd.Series, row_idx: int) -> Transaction | None:
        """
        Process a single CSV row into a Transaction.

        Args:
            db: Database session
            row: Pandas series representing one row
            row_idx: Row index for error reporting

        Returns:
            Transaction object or None if row should be skipped
        """
        # Skip if essential fields are empty
        if pd.isna(row["Monto"]) or pd.isna(row["Categoria"]):
            return None

        # Parse date (DD/MM/YYYY format)
        try:
            transaction_date = datetime.strptime(row["Fecha del movimiento"], "%d/%m/%Y").date()
        except ValueError as e:
            raise CSVIngestionError(f"Invalid date format: {row['Fecha del movimiento']}. Expected DD/MM/YYYY")

        # Map participant
        responsable = row["Responsable"]
        if responsable not in CSVIngestionService.PARTICIPANT_MAPPING:
            raise CSVIngestionError(f"Unknown participant: {responsable}")

        participant_name = CSVIngestionService.PARTICIPANT_MAPPING[responsable]
        participant = db.query(Participant).filter(Participant.name == participant_name).first()
        if not participant:
            raise CSVIngestionError(f"Participant not found in database: {participant_name}")

        # Parse amount
        try:
            amount = Decimal(str(row["Monto"]))
            if amount <= 0:
                raise CSVIngestionError(f"Amount must be positive: {amount}")
        except Exception as e:
            raise CSVIngestionError(f"Invalid amount: {row['Monto']}")

        # Get category name from subcategory columns
        categoria_principal = row["Categoria"]
        subcategory_columns = [
            "Subcategorias Alimentacion",
            "Subcategorias Transporte",
            "Subcategorias Personal",
            "Subcategorias Vivienda",
            "Subcategorias Ingresos",
            "Subcategorías Ahorros",
            "Subcategorias Deudas",
            "Subcategorias Cuidado Personal",
            "Subcategorias Carro",
            "Subcategorias Entretenimiento",
            "Subcategorias Educacion y Trabajo",
            "Subcategorias Mascotas",
            "Subcategorias Otros",
        ]

        # Find the filled subcategory
        category_name = None
        for col in subcategory_columns:
            if col in row and pd.notna(row[col]) and row[col].strip():
                category_name = row[col].strip()
                break

        if not category_name:
            raise CSVIngestionError(f"No subcategory specified for row")

        # Look up category in database
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            raise CSVIngestionError(f"Category not found in database: {category_name}")

        # Verify category type matches "Tipo"
        tipo = row["Tipo"]
        if tipo not in CSVIngestionService.TIPO_MAPPING:
            raise CSVIngestionError(f"Invalid Tipo: {tipo}. Must be 'Gasto' or 'Ingreso'")

        expected_type = CSVIngestionService.TIPO_MAPPING[tipo]
        if category.type != expected_type:
            raise CSVIngestionError(
                f"Category type mismatch: {category_name} is {category.type.value}, "
                f"but Tipo is {tipo} ({expected_type.value})"
            )

        # Get description
        description = row.get("Descripción", "")
        if pd.isna(description):
            description = ""

        # For now, default to CASH payment method
        # TODO: Add payment method column to form if needed
        payment_method = PaymentMethod.CASH

        # Create transaction
        transaction = Transaction(
            date=transaction_date,
            amount=amount,
            description=str(description),
            category_id=category.id,
            participant_id=participant.id,
            payment_method=payment_method,
            is_credit=False,
        )

        return transaction

    @staticmethod
    def validate_csv_format(file: BinaryIO) -> dict:
        """
        Validate CSV format without importing.

        Args:
            file: CSV file (binary IO)

        Returns:
            dict with validation results
        """
        try:
            df = pd.read_csv(file)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to read CSV: {str(e)}"
            }

        required_columns = [
            "Fecha del movimiento",
            "Responsable",
            "Tipo",
            "Monto",
            "Descripción",
            "Categoria",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                "valid": False,
                "error": f"Missing required columns: {', '.join(missing_columns)}"
            }

        return {
            "valid": True,
            "total_rows": len(df),
            "columns": list(df.columns)
        }
