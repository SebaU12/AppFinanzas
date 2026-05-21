"""
Seed data for fixed category list with Spanish labels.
"""
from models.category import CategoryType

# Fixed category list as defined in AGENT.md
CATEGORIES_SEED = [
    # Ingresos (Income)
    {"name": "Lu sueldo", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},
    {"name": "Lu FICO", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},
    {"name": "Chebos Sueldo", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},
    {"name": "Chebos Prisma", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},
    {"name": "Hackatones + extras", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},
    {"name": "Giftcards", "type": CategoryType.INCOME, "is_personal": False, "allows_credit": False},

    # Ahorro (Savings - treated as expense)
    {"name": "Aporte Lu", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Aporte Chebos", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},

    # Vivienda (Housing)
    {"name": "Alquiler", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Servicios (Luz, internet)", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Mantenimiento + agua", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Arbitrios", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},

    # Deudas (Debts)
    {"name": "Viajes", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Tarjeta de credito", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Extra", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},

    # Alimentación (Food)
    {"name": "Compras (supermercado)", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Delivery / Comida fuera", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Cuidado Personal, Salud y Limpieza (Personal Care, Health & Cleaning)
    {"name": "Articulos de higiene", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Suplementos", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Proteina", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Consultas medicas", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Vacunas", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Articulos de limpieza Depa", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Transporte (Transportation)
    {"name": "Metropolitano / Bus / Taxi", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": False},
    {"name": "Gas", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Gasolina", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Carro (Car)
    {"name": "Mantenimiento", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Lavados", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Entretenimiento (Entertainment)
    {"name": "Suscripciones", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Regalos por cumpleaños", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Citas", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Visitas a amigos", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Salidas Mario y Noemi", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Educación y Trabajo (Education & Work)
    {"name": "LLM Claude", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Certificados", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Cursos", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Viaticos", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Mascotas (Pets)
    {"name": "Banio Goli", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Vacunas Goli", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Comida Goli", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Gastos Goli", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Gastos Ron", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Otros (Other)
    {"name": "Inconvenientes", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},
    {"name": "Compras Depa", "type": CategoryType.EXPENSE, "is_personal": False, "allows_credit": True},

    # Personal (Personal - excluded from reimbursements)
    {"name": "Gastos Lu", "type": CategoryType.EXPENSE, "is_personal": True, "allows_credit": True},
    {"name": "Gastos Chebos", "type": CategoryType.EXPENSE, "is_personal": True, "allows_credit": True},
]
