# AMPRO License System

A comprehensive system for processing and printing driver's licenses, integrating with government databases and providing an interface for department workers.

## Features

- Connect to government databases to retrieve citizen information
- Process and consolidate citizen data
- Manage license applications and status tracking
- Generate ISO-compliant license files
- Generate license QR codes and previews
- Secure authentication and authorization
- Transaction history and audit logging

## Technology Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Authentication**: JWT-based authentication
- **Deployment**: Render

## Project Structure

```
ampro/
├── alembic/              # Database migration files
├── app/                  # Main application code
│   ├── api/              # API endpoints
│   │   └── v1/           # API version 1
│   │       └── endpoints/  # Individual API route handlers
│   ├── core/             # Core functionality
│   ├── crud/             # Database CRUD operations
│   ├── db/               # Database connection, models
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── static/           # Static files
│   └── templates/        # HTML templates
├── requirements.txt      # Python dependencies
├── Procfile              # For Render deployment
└── README.md             # Project documentation
```

## Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/schuttebj/ampro.git
   cd ampro
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   DATABASE_URL=postgresql://ampro_license_db_user:R0W46Np7pL1LJjVSF93b3uIoTVmFJKnz@dpg-d0dss9h5pdvs73al0t4g-a/ampro_license_db
   SECRET_KEY=your-secret-key
   DEBUG=true
   ```

5. Run database migrations:
   ```
   alembic upgrade head
   ```

6. Start the development server:
   ```
   uvicorn app.main:app --reload
   ```

7. The API will be available at `http://localhost:8000` and the interactive Swagger documentation at `http://localhost:8000/docs`

## API Documentation

The API is documented using OpenAPI (Swagger) and can be accessed at `/docs` when the application is running.

### Key Endpoints

- **Authentication**
  - `POST /api/v1/auth/login`: Get access token
  - `POST /api/v1/auth/test-token`: Test token validity

- **Users**
  - `GET /api/v1/users/me`: Get current user information
  - `PUT /api/v1/users/me`: Update current user information

- **Citizens**
  - `GET /api/v1/citizens`: List citizens
  - `POST /api/v1/citizens`: Create citizen
  - `GET /api/v1/citizens/search`: Search citizens

- **Licenses**
  - `GET /api/v1/licenses`: List licenses
  - `POST /api/v1/licenses`: Create license
  - `GET /api/v1/licenses/{license_id}/preview`: Generate license preview
  - `POST /api/v1/licenses/{license_id}/print`: Print license

- **Applications**
  - `GET /api/v1/applications`: List applications
  - `POST /api/v1/applications`: Create application
  - `POST /api/v1/applications/{application_id}/approve`: Approve application

- **External Database Integration**
  - `GET /api/v1/external/citizen/{id_number}`: Query external citizen database
  - `GET /api/v1/external/consolidated/{id_number}`: Query all external databases
  - `POST /api/v1/external/import-citizen/{id_number}`: Import citizen from external data

## Testing

### Setting up Test Environment

1. Create a test admin account:
   ```
   POST /api/v1/mock/setup-admin
   ```

2. Generate test data:
   ```
   POST /api/v1/mock/generate-data
   ```

## Database Schema

The database consists of the following main tables:

- `user`: System users (administrators, officers)
- `citizen`: Citizen information
- `license`: Driver's license records
- `licenseapplication`: License applications
- `transaction`: Financial transactions
- `auditlog`: Audit trail of system activities

## Deployment

The application is configured for deployment on Render. Connect your GitHub repository to Render and use the following settings:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `alembic upgrade head && uvicorn app.main:app --host=0.0.0.0 --port=$PORT`
- **Environment Variables**: Add the same variables as in the `.env` file

## Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control
- Comprehensive audit logging
- Input validation using Pydantic schemas

## License and Attribution

Developed for AMPRO license processing system.

## Contact

For support or inquiries, please contact [support@example.com](mailto:support@example.com). 