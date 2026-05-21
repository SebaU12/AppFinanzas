"""
Tests for CSV Ingestion functionality.
"""
import pytest
from io import BytesIO
import tempfile


def create_csv_content(rows: list[str]) -> BytesIO:
    """Helper to create CSV file content."""
    header = "Marca temporal,Fecha del movimiento,Responsable,Tipo,Monto,Descripción,Categoria ,Subcategorias Alimentacion,Subcategorias Transporte,Subcategorias Personal,Subcategorias Vivienda,Subcategorias Ingresos,Subcategorías Ahorros,Subcategorias Deudas,Subcategorias Cuidado Personal,Subcategorias Carro,Subcategorias Entretenimiento,Subcategorias Educacion y Trabajo,Subcategorias Mascotas,Subcategorias Otros\n"
    content = header + "\n".join(rows)
    return BytesIO(content.encode('utf-8'))


def test_import_valid_csv(client, test_db):
    """Test importing a valid CSV file."""
    # Create participants
    lu = client.post("/participants/", json={"name": "Lu"}).json()
    chebos = client.post("/participants/", json={"name": "Chebos"}).json()

    # Create categories (using seed data structure)
    alquiler = client.post("/categories/", json={
        "name": "Alquiler",
        "type": "EXPENSE"
    }).json()

    lu_sueldo = client.post("/categories/", json={
        "name": "Lu sueldo",
        "type": "INCOME"
    }).json()

    # Create CSV content
    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,666,Test expense,Vivienda,,,,Alquiler,,,,,,,,,",
        "10/02/2026 23:29:21,11/02/2026,Copine,Ingreso,2000,Test income,Ingresos,,,,,Lu sueldo,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    # Upload CSV
    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["total"] == 2
    assert data["statistics"]["success"] == 2
    assert len(data["statistics"]["errors"]) == 0

    # Verify transactions were created
    transactions = client.get("/transactions/").json()
    assert len(transactions) == 2


def test_import_csv_with_invalid_date(client, test_db):
    """Test CSV import with invalid date format."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,2026-02-10,Copain,Gasto,666,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "Invalid date format" in data["statistics"]["errors"][0]["error"]


def test_import_csv_unknown_participant(client, test_db):
    """Test CSV import with unknown participant."""
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,UnknownPerson,Gasto,666,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "Unknown participant" in data["statistics"]["errors"][0]["error"]


def test_import_csv_category_not_found(client, test_db):
    """Test CSV import with category not in database."""
    client.post("/participants/", json={"name": "Lu"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,666,Test,Vivienda,,,,NonExistentCategory,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "Category not found" in data["statistics"]["errors"][0]["error"]


def test_import_csv_type_mismatch(client, test_db):
    """Test CSV import with category type mismatch."""
    client.post("/participants/", json={"name": "Lu"})

    # Create expense category
    client.post("/categories/", json={
        "name": "Alquiler",
        "type": "EXPENSE"
    })

    # Try to import as income (tipo mismatch)
    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Ingreso,666,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "type mismatch" in data["statistics"]["errors"][0]["error"]


def test_import_csv_missing_amount(client, test_db):
    """Test CSV import with missing amount (should skip)."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["skipped"] == 1
    assert data["statistics"]["success"] == 0


def test_import_csv_invalid_amount(client, test_db):
    """Test CSV import with invalid amount format."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,not-a-number,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "Invalid amount" in data["statistics"]["errors"][0]["error"]


def test_import_csv_negative_amount(client, test_db):
    """Test CSV import with negative amount."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,-100,Test,Vivienda,,,,Alquiler,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "must be positive" in data["statistics"]["errors"][0]["error"]


def test_import_csv_no_subcategory(client, test_db):
    """Test CSV import with no subcategory filled."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,100,Test,Vivienda,,,,,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 0
    assert len(data["statistics"]["errors"]) == 1
    assert "No subcategory specified" in data["statistics"]["errors"][0]["error"]


def test_import_csv_multiple_rows_mixed_results(client, test_db):
    """Test CSV import with mix of valid and invalid rows."""
    client.post("/participants/", json={"name": "Lu"})
    client.post("/participants/", json={"name": "Chebos"})
    client.post("/categories/", json={"name": "Alquiler", "type": "EXPENSE"})
    client.post("/categories/", json={"name": "Lu sueldo", "type": "INCOME"})

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,666,Valid expense,Vivienda,,,,Alquiler,,,,,,,,",
        "10/02/2026 23:28:00,10/02/2026,UnknownPerson,Gasto,100,Invalid participant,Vivienda,,,,Alquiler,,,,,,,,",
        "10/02/2026 23:29:21,11/02/2026,Copine,Ingreso,2000,Valid income,Ingresos,,,,,Lu sueldo,,,,,,,,",
        "10/02/2026 23:30:00,bad-date,Copain,Gasto,50,Invalid date,Vivienda,,,,Alquiler,,,,,,,,",
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["total"] == 4
    assert data["statistics"]["success"] == 2
    assert len(data["statistics"]["errors"]) == 2

    # Verify successful transactions were created
    transactions = client.get("/transactions/").json()
    assert len(transactions) == 2


def test_validate_csv_valid_format(client, test_db):
    """Test CSV format validation with valid file."""
    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,666,Test,Vivienda,,,,Alquiler,,,,,,,,"
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/validate",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["details"]["valid"] is True
    assert data["details"]["total_rows"] == 1


def test_validate_csv_missing_columns(client, test_db):
    """Test CSV validation with missing required columns."""
    # CSV with missing columns
    content = "Fecha,Monto\n10/02/2026,100\n"
    csv_file = BytesIO(content.encode('utf-8'))

    response = client.post(
        "/csv/validate",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_import_non_csv_file(client, test_db):
    """Test importing non-CSV file."""
    content = BytesIO(b"Not a CSV file")

    response = client.post(
        "/csv/import",
        files={"file": ("test.txt", content, "text/plain")}
    )

    assert response.status_code == 400
    assert "must be a CSV file" in response.json()["detail"]


def test_import_csv_with_all_subcategory_types(client, test_db):
    """Test CSV import with different subcategory columns."""
    client.post("/participants/", json={"name": "Lu"})

    # Create categories from different sections
    client.post("/categories/", json={
        "name": "Compras (supermercado)",
        "type": "EXPENSE"
    })
    client.post("/categories/", json={
        "name": "Gas",
        "type": "EXPENSE"
    })
    client.post("/categories/", json={
        "name": "Suscripciones",
        "type": "EXPENSE"
    })

    rows = [
        "10/02/2026 23:27:15,10/02/2026,Copain,Gasto,100,Groceries,Alimentacion,Compras (supermercado),,,,,,,,,,,",
        "10/02/2026 23:28:00,10/02/2026,Copain,Gasto,50,Gas,Transporte,,Gas,,,,,,,,,,",
        "10/02/2026 23:29:00,10/02/2026,Copain,Gasto,15,Netflix,Entretenimiento,,,,,,,,,,Suscripciones,,,",
    ]
    csv_file = create_csv_content(rows)

    response = client.post(
        "/csv/import",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["statistics"]["success"] == 3
    assert len(data["statistics"]["errors"]) == 0

    # Verify transactions
    transactions = client.get("/transactions/").json()
    assert len(transactions) == 3
