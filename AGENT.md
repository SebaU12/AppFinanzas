Perfecto, entendido 👍
Aquí tienes **la versión corregida en inglés**, **manteniendo los labels y contenidos del apartado de *Budget* en español** (tal como *Lu Sueldo, Lu FICO, Chebos Sueldo, Chebos Prisma, etc.*).
Todo lo demás queda en inglés técnico.

---

# Backend Documentation – Shared Personal Financial System

## 1. System Objective

This backend system aims to enable personal and shared financial control (couple/household) under a logic similar to business accounting, maintaining:

* Fixed monthly budgets
* Tracking of actual expenses (independent of payment method)
* Liquidity control (cash flow)
* Credit card and installment management
* Accounts payable and receivable
* Reimbursements and settlements between participants
* Future purchase simulation (multi-month)

The system is designed to run **100% locally**, using free tools, with manual data input via Google Forms and CSV files.

---

## 2. General Architecture

### 2.1 Logical Architecture

```
[ Google Forms / CSV ]
          |
          v
[ Data Ingestion ]
          |
          v
[ Financial Core ]
  |     |     |
Budget   Cash   Reimbursement
  |     |     |
  └── Accounting Statements ──┐
                              v
                        [ Local API ]
                              v
                          [ Frontend ]
```

### 2.2 Technology Stack

| Layer          | Technology                 |
| -------------- | -------------------------- |
| Backend        | Python + FastAPI           |
| Database       | SQLite                     |
| ORM            | SQLAlchemy                 |
| CSV Ingestion  | Pandas                     |
| Frontend       | React (local)              |
| Dashboards     | Recharts                   |
| Authentication | Simple local (config file) |

---

## 3. Backend Modules

---

## 3.1 Module: Participants

### Purpose

Manage the people participating in the financial system.

### Entity

**Participant**

| Field              | Type    | Description                       |
| ------------------ | ------- | --------------------------------- |
| id                 | UUID    | Unique identifier                 |
| name               | string  | Participant name                  |
| active             | boolean | Participates in the current month |
| default_percentage | float   | Default % for reimbursements      |

---

## 3.2 Module: Categories

### Purpose

Define financial categories and their accounting behavior.

### Entity

**Category**

| Field         | Type    | Description                  |
| ------------- | ------- | ---------------------------- |
| id            | UUID    |                              |
| name          | string  |                              |
| type          | enum    | income / expense             |
| is_personal   | boolean | Excluded from reimbursements |
| allows_credit | boolean |                              |

---

Entiendo perfectamente. He revisado las capturas de pantalla de tu nuevo formulario de Google y el ejemplo del CSV resultante. Hay varios cambios en las subcategorías (como la adición de "Artículos de limpieza Depa" y "Compras Depa") y en los nombres de algunas categorías principales.

Aquí tienes la documentación actualizada siguiendo el formato que ya manejabas:

---

## 3.3 Module: Budget

### Budget Category Structure

The following categories make up the **base monthly budget table**, on which expenses, reimbursements, and accounting statements are calculated. This structure is fixed and serves as the central axis of the system.

> **Note:** Category names and subcategories are kept in Spanish for internal consistency with the Google Form and the resulting CSV.

#### Ingresos

* Lu sueldo
* Lu FICO
* Chebos Sueldo
* Chebos Prisma
* Hackatones + extras
* Giftcards

#### Ahorros

* Aporte Lu
* Aporte Chebos

#### Vivienda

* Alquiler
* Servicios (Luz, internet)
* Mantenimiento + agua
* Arbitrios

#### Deudas

* Viajes
* Tarjeta de credito
* Extra

#### Alimentación

* Compras (supermercado)
* Delivery / Comida afuera

#### Cuidado Personal, Salud y Limpieza

* Articulos de higiene
* Suplementos
* Proteina
* Consultas medicas
* Vacunas
* Articulos de limpieza Depa

#### Transporte

* Metropolitano / Bus / Taxi
* Gas
* Gasolina

#### Carro

* Mantenimiento
* Lavados

#### Entretenimiento

* Suscripciones
* Regalos por cumpleaños
* Citas
* Visitas a amigos
* Salidas Mario y Noemi

#### Educación y Trabajo

* LLM Claude
* Certificados
* Cursos
* Viaticos

#### Mascotas

* Banio Goli
* Vacunas Goli
* Comida Goli
* Gastos Goli
* Gastos Ron

#### Otros

* Inconvenientes
* Compras Depa

#### Personal (excluido de reembolsos)

* Gastos Lu
* Gastos Chebos

---

### Purpose

Define monthly spending limits per category, aligned with accounting and reimbursement logic.

### Entity

**MonthlyBudget**

| Field           | Type    | Description |
| --------------- | ------- | ----------- |
| id              | UUID    |             |
| month           | YYYY-MM |             |
| category_id     | UUID    |             |
| budgeted_amount | decimal |             |

---

## 3.4 Module: Expenses and Income

### Purpose

Record actual economic transactions.

### Entity

**Transaction**

| Field          | Type            | Description           |
| -------------- | --------------- | --------------------- |
| id             | UUID            |                       |
| date           | date            |                       |
| amount         | decimal         |                       |
| category_id    | UUID            |                       |
| participant_id | UUID            |                       |
| payment_method | enum            | cash / debit / credit |
| card_id        | UUID (optional) |                       |
| is_credit      | boolean         |                       |
| installments   | int (optional)  |                       |
| description    | string          |                       |

---

## 3.5 Module: Credit Cards

### Purpose

Separate expense recognition from card payment.

### Entities

**CreditCard**

| Field       | Type   |
| ----------- | ------ |
| id          | UUID   |
| name        | string |
| closing_day | int    |
| payment_day | int    |

**CardInstallment**

| Field          | Type    |
| -------------- | ------- |
| id             | UUID    |
| transaction_id | UUID    |
| month          | YYYY-MM |
| amount         | decimal |
| paid           | boolean |

---

## 3.6 Module: Accounts Payable and Receivable

### Purpose

Represent future obligations and receivable rights.

### Entities

**AccountPayable**

| Field  | Type        |
| ------ | ----------- |
| id     | UUID        |
| source | card / loan |
| month  | YYYY-MM     |
| amount | decimal     |

**AccountReceivable**

| Field              | Type    |
| ------------------ | ------- |
| id                 | UUID    |
| source_participant | UUID    |
| target_participant | UUID    |
| month              | YYYY-MM |
| amount             | decimal |

---

## 3.7 Module: Reimbursement

### Purpose

Settle shared expenses between participants.

### Rules

* Applies to all categories except those with `is_personal = true`
* Executed at month-end
* Expenses are split using configurable percentages

### Entities

**MonthlyReimbursement**

| Field       | Type    |
| ----------- | ------- |
| id          | UUID    |
| month       | YYYY-MM |
| category_id | UUID    |

**ReimbursementDetail**

| Field                | Type    |
| -------------------- | ------- |
| reimbursement_id     | UUID    |
| participant_id       | UUID    |
| percentage           | float   |
| corresponding_amount | decimal |
| amount_paid          | decimal |
| balance              | decimal |

---

## 3.8 Module: Expected Purchases (Simulation)

### Purpose

Simulate the financial impact of future multi-month purchases.

### Entity

**ExpectedPurchase**

| Field        | Type    |
| ------------ | ------- |
| id           | UUID    |
| name         | string  |
| total_amount | decimal |
| installments | int     |
| category_id  | UUID    |
| start_month  | YYYY-MM |
| simulated    | boolean |

### Simulation Output

* Impact on monthly budget
* Impact on cash flow
* Impact on accounts payable

---

## 3.9 Module: Accounting Statements

### Income Statement

| Concept  | Amount |
| -------- | ------ |
| Income   |        |
| Expenses |        |
| Result   |        |

### Cash Flow

| Month | Cash Inflows | Cash Outflows | Balance |

### Balance Sheet

| Assets              | Liabilities      |
| ------------------- | ---------------- |
| Cash                | Accounts payable |
| Accounts receivable |                  |

---

## 4. Usage Flows

### Credit Card Expense Registration

1. Full expense is recorded at consumption time
2. Monthly budget is impacted
3. Future installments are generated
4. Monthly payment affects cash flow

### Monthly Closing

1. Reimbursements are calculated
2. Accounts receivable/payable are generated
3. Accounting statements are consolidated

### Simulation

1. User creates an expected purchase
2. Backend simulates affected months
3. No real transactions are created

---

## 5. Guiding Principle

> **An expense occurs when it is consumed, not when it is paid.**

This principle governs the entire backend.

