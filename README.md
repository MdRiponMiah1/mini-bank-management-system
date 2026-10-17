# Mini Bank Management System API

A RESTful banking API built with **Django** and **Django REST Framework (DRF)**. The project demonstrates customer authentication, personal bank accounts, deposits, withdrawals, transfers, transaction history, date filtering, daily withdrawal limits, and CSV statements.

> **Project status:** Educational assignment. This project is not a production-ready banking system and must not be used to handle real money or sensitive customer data.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Run the Development Server](#run-the-development-server)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Example Requests](#example-requests)
- [Transaction History and Filters](#transaction-history-and-filters)
- [CSV Statement Download](#csv-statement-download)
- [Daily Withdrawal Limit](#daily-withdrawal-limit)
- [Django Admin](#django-admin)
- [Running Tests](#running-tests)
- [Validation and Access Rules](#validation-and-access-rules)
- [Security and Development Notes](#security-and-development-notes)
- [GitHub Preparation](#github-preparation)
- [License](#license)

## Features

- Customer registration and token-based login.
- Authenticated profile viewing and updating.
- Create and list personal Savings and Current accounts.
- Automatically generated unique 12-digit account numbers.
- View account details and current balance.
- Deposit money and create transaction records.
- Withdraw money after validating the amount, available balance, and daily withdrawal limit.
- Transfer money between accounts and create records for both the sending and receiving sides.
- Paginated transaction history with account, transaction-type, and date-range filters.
- Download an account statement as a CSV file.
- Django Admin support for reviewing banking records.
- Automated tests for customer, account, and transaction behavior.

## Technology Stack

- **Language:** Python
- **Web framework:** Django
- **API framework:** Django REST Framework
- **Authentication:** DRF Token Authentication, with Session and Basic Authentication also configured
- **Development database:** SQLite
- **Statement export:** Python standard-library CSV support

Exact dependency versions are pinned in `requirements.txt`.

## Project Structure

```text
mini-bank-management-system/
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── bank_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── customers/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── transactions/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

The local `db.sqlite3` file is created when the project is migrated and run; it should not be committed to a public repository.

## Requirements

- Python version compatible with the pinned Django release in `requirements.txt`.
- `pip`.
- A terminal or command prompt.

## Installation and Setup

### 1. Get the project

If the repository has already been pushed to GitHub, clone it using your repository URL:

```bash
git clone <your-repository-url>
cd mini-bank-management-system
```

Replace `<your-repository-url>` with the actual Git repository URL. If you already have the project folder, open your terminal in that folder instead.

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Android Termux:**

If the project is in shared storage, create the virtual environment in the Termux home directory to avoid shared-storage permission problems:

```bash
python -m venv ~/mini-bank-venv
source ~/mini-bank-venv/bin/activate
```

Activate the environment again whenever you open a new terminal session.

### 3. Install dependencies

Run these commands from the project root, with the virtual environment activated:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create an administrator account

```bash
python manage.py createsuperuser
```

Follow the prompts to create the admin username and password.

## Run the Development Server

```bash
python manage.py runserver
```

The development server normally runs at:

```text
http://127.0.0.1:8000/
```

Use `Ctrl+C` to stop the server. The API routes are listed below. The project does not necessarily provide a browsable API landing page at the root URL.

## Authentication

The registration endpoint creates a customer account. Log in with the customer's username and password to receive an authentication token.

For protected endpoints, include this HTTP header:

```http
Authorization: Token YOUR_AUTH_TOKEN
```

Replace `YOUR_AUTH_TOKEN` with the token returned by the login endpoint. Do not share tokens or store real tokens in the repository.

## API Endpoints

All API endpoints use the `/api/` prefix. Registration and login do not require authentication. The other endpoints require authentication unless otherwise noted.

### Authentication and Profile

| Method | Endpoint | Purpose | Authentication |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a customer | Not required |
| `POST` | `/api/auth/login/` | Log in and receive a token | Not required |
| `GET` | `/api/auth/profile/` | View the current user's profile | Required |
| `PUT` / `PATCH` | `/api/auth/profile/` | Update the current user's profile | Required |
| `GET` | `/api/profile/` | Alternate route to view the current user's profile | Required |
| `PUT` / `PATCH` | `/api/profile/` | Alternate route to update the current user's profile | Required |

Both profile routes are present in the project's current URL configuration.

### Bank Accounts

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/accounts/` | List the authenticated user's accounts |
| `POST` | `/api/accounts/` | Create a Savings or Current account |
| `GET` | `/api/accounts/<account_id>/` | View an account's details |
| `GET` | `/api/accounts/<account_id>/balance/` | View an account's balance |

### Transactions and Statements

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/transactions/deposit/` | Deposit money |
| `POST` | `/api/transactions/withdraw/` | Withdraw money |
| `POST` | `/api/transactions/transfer/` | Transfer money to another account |
| `GET` | `/api/transactions/` | View transaction history |
| `GET` | `/api/transactions/statement/` | Download an account statement as CSV |

**Important route correction:** Transaction history is available at `/api/transactions/`. The route `/api/transactions/history/` is not defined in the current `transactions/urls.py`.

### Django Admin

Open `http://127.0.0.1:8000/admin/` and sign in using the superuser account created with `createsuperuser`.

## Example Requests

The examples below show request bodies. Use the actual account IDs and account numbers returned by your running API. Send the authentication header for protected endpoints.

### 1. Register a customer

**Endpoint:** `POST /api/auth/register/`

```json
{
  "username": "customer1",
  "email": "customer1@example.com",
  "password": "Use-a-strong-password-123"
}
```

Use a strong password that meets Django's password validation rules.

### 2. Log in

**Endpoint:** `POST /api/auth/login/`

```json
{
  "username": "customer1",
  "password": "Use-a-strong-password-123"
}
```

Copy the token from the response and send it in the `Authorization` header for authenticated requests.

### 3. View or update your profile

**Endpoint:** `GET /api/auth/profile/`

For an update, use `PATCH /api/auth/profile/` with the fields you want to change, for example:

```json
{
  "first_name": "Customer",
  "last_name": "One"
}
```

The profile serializer does not allow the user ID or username to be changed through this endpoint.

### 4. Create a bank account

**Endpoint:** `POST /api/accounts/`

```json
{
  "account_type": "SAVINGS"
}
```

Use `SAVINGS` or `CURRENT` for `account_type`. The server assigns the account owner, unique account number, starting balance, and timestamps. Do not send a client-supplied owner or opening balance.

### 5. View your accounts

**Endpoint:** `GET /api/accounts/`

The endpoint returns accounts associated with the authenticated user.

### 6. View an account balance

**Endpoint:** `GET /api/accounts/1/balance/`

Replace `1` with an account ID belonging to the authenticated user.

### 7. Deposit money

**Endpoint:** `POST /api/transactions/deposit/`

```json
{
  "account_id": 1,
  "amount": "500.00",
  "description": "Cash deposit"
}
```

### 8. Withdraw money

**Endpoint:** `POST /api/transactions/withdraw/`

```json
{
  "account_id": 1,
  "amount": "100.00",
  "description": "ATM withdrawal"
}
```

A withdrawal must use a positive amount, must not exceed the available balance, and must comply with the configured daily withdrawal limit.

### 9. Transfer money

**Endpoint:** `POST /api/transactions/transfer/`

```json
{
  "from_account_id": 1,
  "recipient_account_number": "123456789012",
  "amount": "50.00",
  "description": "Transfer to another account"
}
```

Replace the sample recipient account number with an actual 12-digit account number. A transfer cannot be made to the same account, and the sender must have sufficient funds.

## Transaction History and Filters

**Endpoint:** `GET /api/transactions/`

Examples:

```text
/api/transactions/?page=1
/api/transactions/?type=DEPOSIT
/api/transactions/?start_date=2026-01-01&end_date=2026-12-31
/api/transactions/?account_id=1
```

Date values use the `YYYY-MM-DD` format. The filters can be combined, for example:

```text
/api/transactions/?type=WITHDRAWAL&start_date=2026-01-01&end_date=2026-12-31&page=1
```

Supported transaction types are:

- `DEPOSIT`
- `WITHDRAWAL`
- `TRANSFER_SENT`
- `TRANSFER_RECEIVED`

The API uses page-number pagination with a default page size of 10. Normal users should only access transactions associated with their own accounts. Do not use an account ID from another user as a way to access private data.

## CSV Statement Download

**Endpoint:** `GET /api/transactions/statement/`

Request a statement for one of your accounts:

```text
/api/transactions/statement/?account_id=1
```

Optional date filters can be supplied:

```text
/api/transactions/statement/?account_id=1&start_date=2026-01-01&end_date=2026-12-31
```

The response is a CSV file that can be opened in spreadsheet software. Replace `account_id=1` with an account ID you are authorized to access.

## Daily Withdrawal Limit

The daily withdrawal limit is configured in `bank_project/settings.py` using `DAILY_WITHDRAWAL_LIMIT`. The current development value is:

```python
DAILY_WITHDRAWAL_LIMIT = '50000.00'
```

Change this setting if your assignment requires a different limit. The limit is intended to restrict the total amount withdrawn from an account during a day.

## Django Admin

1. Run the development server.
2. Open `http://127.0.0.1:8000/admin/`.
3. Sign in using the superuser credentials.
4. Review the available customer, bank account, and transaction administration pages.

Admin access should be restricted to trusted administrators. The project's admin interface is intended for educational and local development use.

## Running Tests

Run the complete test suite:

```bash
python manage.py test
```

Run tests for individual apps:

```bash
python manage.py test customers
python manage.py test accounts
python manage.py test transactions
```

The test suite covers customer registration and login, profile access, account access, deposits, withdrawals, transfers, transaction history, CSV statements, and withdrawal-limit behavior. The tests currently included in the repository are the source of truth for exact test coverage.

## Validation and Access Rules

The API is designed to enforce these important business rules:

- Registration validates customer details and passwords.
- Authenticated users access their own profile and accounts.
- Account numbers are generated uniquely by the application.
- Transaction amounts must be positive.
- Withdrawals and transfers must not exceed the available balance.
- A transfer cannot send money from an account to itself.
- Successful transaction operations create transaction records.
- A transfer records both the sending and receiving sides.
- Transaction history is paginated and can be filtered.
- CSV statements are requested for a specified account and optional date range.

These are educational application rules, not a guarantee of production-grade financial integrity. Before any real-world use, the implementation would need independent security review, stronger database constraints, concurrency testing, monitoring, and operational controls.

## Security and Development Notes

- This project is for learning and assignment purposes; it is not a production banking system.
- Do not commit real passwords, API tokens, secret keys, `.env` files, or private customer data.
- Configure a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `ALLOWED_HOSTS` for the environment before deployment. Never expose a development secret key on a public server.
- Use HTTPS in deployed environments.
- The local SQLite database is for development. Do not commit `db.sqlite3` or database backups containing private data.
- Monetary values use decimal fields rather than binary floating-point values.
- Transaction operations use database transactions to group related balance and transaction-record updates.
- SQLite does not provide robust row-level locking for concurrent financial operations. A production-style deployment should use a suitable database such as PostgreSQL and carefully review transaction locking and race conditions.
- Add appropriate logging, backups, rate limiting, monitoring, and security checks before any public deployment.
- Never use real financial information when demonstrating this assignment.

## GitHub Preparation

Before pushing the project to a public repository:

1. Review `.gitignore` and confirm that it excludes virtual environments, local database files, Python caches, and secrets.
2. Check whether a database or secret has already been tracked by Git; adding a filename to `.gitignore` does not remove a file that is already tracked.
3. Do not commit `.env` files, tokens, passwords, real customer data, or database backups.
4. Ensure `README.md` describes the actual routes and features in the code.
5. Run the test suite before pushing:

   ```bash
   python manage.py test
   ```

## License

This project was created for educational purposes. No specific open-source license is declared by this README. If you plan to distribute the project under an open-source license, add the appropriate license file and update this section.
