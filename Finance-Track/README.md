# Finance Tracker

A Django-based finance tracking application that helps you manage accounts, transactions, and financial data across multiple teams and currencies.

## Features

### Core Features
- **Team Management**: Create and manage multiple teams
- **Multi-Currency Support**: PKR (Primary), USD, GBP with automatic conversion
- **Account Management**: Support for various account types (Cash, Bank, Credit Card, Savings, Investment)
- **Transaction Types**:
  - Income: Add money to accounts
  - Expense: Remove money from accounts  
  - Transfer: Move money between accounts
- **Categories**: Organize transactions by custom categories
- **Real-time Balance Tracking**: All balances converted to PKR for unified reporting

### Design
- Minimal black and white user interface
- Clean, professional appearance
- Responsive design for mobile and desktop

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Finance-Track
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv finance_env
   source finance_env/bin/activate  # On Windows: finance_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Setup initial currencies**
   ```bash
   python manage.py setup_currencies
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Usage

### Getting Started
1. Visit `http://127.0.0.1:8000/admin/` to access the Django admin
2. Create teams and add users as members
3. Set up currencies and exchange rates
4. Create accounts for different currencies
5. Add income/expense categories
6. Start tracking transactions

### Main Features
- **Dashboard**: Overview of total balance and recent transactions
- **Accounts**: Manage all your financial accounts
- **Transactions**: View and add income, expense, and transfer transactions
- **Categories**: Organize your financial activities
- **Admin Panel**: Full administrative control

### Currency Conversion
- PKR is the primary currency for all reporting
- Exchange rates can be updated in the admin panel
- All transactions are automatically converted to PKR for unified reporting

## Project Structure

```
Finance-Track/
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── forms.py           # Django forms
│   ├── admin.py           # Admin interface
│   ├── urls.py            # URL patterns
│   └── templates/         # HTML templates
├── finance_tracker/       # Django project settings
├── manage.py              # Django management script
└── README.md              # This file
```

## Models

### Team
- Team management with multiple members
- Access control for accounts and transactions

### Currency
- Supported currencies: PKR, USD, GBP
- Exchange rates for conversion to PKR

### Account
- Multiple account types
- Currency-specific balances
- Automatic PKR conversion

### Category
- Income, Expense, and Transfer categories
- Team-specific organization

### Transaction
- Income, Expense, and Transfer types
- Automatic balance updates
- Currency conversion

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and personal use.

## Support

For questions or issues, please create an issue in the repository.
