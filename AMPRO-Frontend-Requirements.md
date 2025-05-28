# AMPRO License System - Frontend Development Guide

## Overview
This document provides comprehensive information for developing the frontend application for the AMPRO License System. The frontend will interact with the existing backend API to create a complete driver's license processing system.

## Backend API Information

### API Base URL
```
https://ampro-licence.onrender.com
```

### API Documentation
- Swagger UI: `https://ampro-licence.onrender.com/api/v1/docs`
- OpenAPI Specification: `https://ampro-licence.onrender.com/api/v1/openapi.json`

### Health Check Endpoints
- Root endpoint: `GET /` - Returns basic API information
- Health check: `GET /health` - Returns API health status

## Key Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/token` - Get new access token using refresh token
- `GET /api/v1/auth/me` - Get current user information

### Users
- `GET /api/v1/users/` - List all users (admin only)
- `POST /api/v1/users/` - Create new user (admin only)
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user (soft delete)

### Citizens
- `GET /api/v1/citizens/` - List all citizens
- `POST /api/v1/citizens/` - Create new citizen
- `GET /api/v1/citizens/search` - Search citizens by ID number or name
- `GET /api/v1/citizens/{citizen_id}` - Get citizen details
- `PUT /api/v1/citizens/{citizen_id}` - Update citizen
- `DELETE /api/v1/citizens/{citizen_id}` - Delete citizen (soft delete)
- `GET /api/v1/citizens/{citizen_id}/licenses` - Get all licenses for a citizen

### Licenses
- `GET /api/v1/licenses/` - List all licenses
- `POST /api/v1/licenses/` - Create new license
- `GET /api/v1/licenses/{license_id}` - Get license details
- `PUT /api/v1/licenses/{license_id}` - Update license
- `DELETE /api/v1/licenses/{license_id}` - Delete license (soft delete)
- `GET /api/v1/licenses/number/{license_number}` - Get license by license number
- `GET /api/v1/licenses/generate-number` - Generate a new license number
- `GET /api/v1/licenses/{license_id}/qr-code` - Generate QR code for a license
- `GET /api/v1/licenses/{license_id}/preview` - Generate license preview
- `POST /api/v1/licenses/{license_id}/print` - Print license

### Applications
- `GET /api/v1/applications/` - List all license applications
- `POST /api/v1/applications/` - Create new license application
- `GET /api/v1/applications/pending` - Get pending license applications
- `GET /api/v1/applications/{application_id}` - Get application details
- `PUT /api/v1/applications/{application_id}` - Update application
- `POST /api/v1/applications/{application_id}/approve` - Approve an application and create license
- `DELETE /api/v1/applications/{application_id}` - Delete application (soft delete)
- `GET /api/v1/applications/citizen/{citizen_id}` - Get applications for a specific citizen

### Transactions
- `GET /api/v1/transactions/` - List all transactions
- `GET /api/v1/transactions/{transaction_id}` - Get transaction details
- `GET /api/v1/transactions/ref/{transaction_ref}` - Get transaction by reference
- `GET /api/v1/transactions/citizen/{citizen_id}` - Get transactions for a citizen
- `GET /api/v1/transactions/license/{license_id}` - Get transactions for a license

### Audit
- `GET /api/v1/audit/` - List audit logs (admin only)
- `GET /api/v1/audit/{audit_id}` - Get specific audit log entry
- `GET /api/v1/audit/user/{user_id}` - Get audit logs for a specific user

### External Data
- `GET /api/v1/external/citizen/{id_number}` - Get external citizen data
- `GET /api/v1/external/driver/{id_number}` - Get external driver data
- `GET /api/v1/external/infringement/{id_number}` - Get external infringement data

## Data Models

### User Roles
- `admin`: System administrator
- `manager`: Department manager
- `officer`: License officer
- `clerk`: Administrative clerk

### License Categories
- `A`: Motorcycle
- `B`: Light vehicle (car)
- `C`: Heavy vehicle (truck)
- `EB`: Light articulated vehicle
- `EC`: Heavy articulated vehicle

### Application Status
- `SUBMITTED`: Initial application state
- `UNDER_REVIEW`: Application is being reviewed
- `DOCUMENTS_REQUESTED`: Additional documents requested
- `APPROVED`: Application approved
- `REJECTED`: Application rejected
- `CANCELLED`: Application cancelled

### License Status
- `ACTIVE`: Valid license
- `EXPIRED`: License has expired
- `SUSPENDED`: License temporarily invalid
- `REVOKED`: License permanently invalid
- `PENDING`: License is being processed

## Project Scope

### Key Features to Implement

#### 1. Authentication and User Management
- Login screen
- User profile management
- Role-based access control
- Password reset functionality

#### 2. Dashboard
- Summary of pending applications
- Recent activities
- Quick statistics (licenses issued, applications pending, etc.)
- Task queue for the logged-in user

#### 3. Citizen Management
- Register new citizens
- Search and view citizen details
- Update citizen information
- View citizen's licenses and applications
- Integration with external citizen database

#### 4. License Processing
- Create new licenses
- View license details with preview
- Print license functionality
- QR code generation
- License renewal workflow
- License status management

#### 5. Application Processing
- Submit new license applications
- Review applications
- Request additional documents
- Approve/reject applications
- Track application status

#### 6. Transaction and Audit Tracking
- View transaction history
- Track audit logs
- Generate reports

#### 7. Administration
- User management
- System configuration
- Audit log review

### UI/UX Requirements
- Clean, professional interface
- Mobile-responsive design
- Accessible design (WCAG compliance)
- Intuitive navigation
- Consistent visual language

## Technical Recommendations

### Frontend Framework
React with TypeScript is recommended for:
- Strong typing and bug prevention
- Component reusability
- Large ecosystem and community
- Industry standard

### UI Component Library Options
- Material UI: https://mui.com/
- Ant Design: https://ant.design/
- Chakra UI: https://chakra-ui.com/
- Tailwind CSS: https://tailwindcss.com/

### State Management
- Redux Toolkit or Context API
- React Query for server state management

### Form Handling
- Formik or React Hook Form
- Yup for validation

### Authentication
- JWT token-based authentication
- Secure storage in HttpOnly cookies or localStorage with proper refresh mechanisms

### API Integration
- Axios for HTTP requests
- Centralized API service layer

### Testing
- Jest for unit testing
- React Testing Library for component testing
- Cypress for end-to-end testing

## Development Workflow

### Recommended Setup
1. Create a new React TypeScript project
2. Set up routing (React Router)
3. Implement authentication
4. Create reusable UI components
5. Implement feature pages
6. Connect to API endpoints
7. Add state management
8. Implement testing
9. Deploy to hosting platform

### Deployment Options
- Vercel: https://vercel.com/
- Netlify: https://www.netlify.com/
- Render: https://render.com/

## Design Guidelines

### Color Scheme
- Primary: #1976d2 (Blue)
- Secondary: #dc004e (Pink)
- Success: #4caf50 (Green)
- Warning: #ff9800 (Orange)
- Error: #f44336 (Red)
- Background: #f5f5f5 (Light Gray)
- Text: #333333 (Dark Gray)

### Typography
- Primary Font: Roboto or Open Sans
- Headings: Bold, clear hierarchy
- Body: Regular weight, high readability

### Layout
- Clean, card-based interface
- Consistent spacing and alignment
- Clear visual hierarchy
- Responsive breakpoints for mobile, tablet, and desktop

## Getting Started

1. Create a new React project with TypeScript:
```bash
npx create-react-app ampro-frontend --template typescript
```

2. Add necessary dependencies:
```bash
npm install react-router-dom axios @mui/material @emotion/react @emotion/styled @mui/icons-material react-query formik yup
```

3. Set up the project structure:
```
src/
├── api/          # API services
├── assets/       # Static assets
├── components/   # Reusable components
├── contexts/     # React context providers
├── hooks/        # Custom hooks
├── layouts/      # Page layouts
├── pages/        # Top-level pages
├── types/        # TypeScript interfaces
├── utils/        # Utility functions
├── App.tsx       # Main application component
└── index.tsx     # Entry point
```

4. Configure environment variables:
Create a `.env` file with:
```
REACT_APP_API_URL=https://ampro-licence.onrender.com
```

5. Connect to the API and implement authentication first before building out other features.

## Additional Resources

- Backend API Repository: https://github.com/schuttebj/ampro
- React Documentation: https://reactjs.org/docs/getting-started.html
- TypeScript Documentation: https://www.typescriptlang.org/docs/ 