# Printer Role Implementation - AMPRO License System

## Overview

This document describes the implementation of the **PRINTER** role for the AMPRO license system. This role allows dedicated printer operators to access only print job processing functions, providing a secure and focused interface for license printing operations.

## Role-Based Access Control (RBAC) System

### User Roles

The system now supports the following roles:

- **ADMIN**: Full system access (equivalent to is_superuser=True)
- **MANAGER**: Department management, user oversight
- **OFFICER**: License processing, application review
- **PRINTER**: Print job processing only ⭐ **NEW**
- **VIEWER**: Read-only access

### Role Hierarchy

```
ADMIN (Full Access)
├── MANAGER (Department oversight)
├── OFFICER (Application processing)
├── PRINTER (Print jobs only) ⭐ NEW
└── VIEWER (Read-only)
```

## Backend Implementation

### 1. Database Changes

#### New User Model Fields
```python
class User(BaseModel):
    # ... existing fields ...
    role = Column(Enum(UserRole), default=UserRole.OFFICER, nullable=False)
```

#### Migration
- **File**: `alembic/versions/005_add_user_roles.py`
- **Changes**: 
  - Adds `UserRole` enum with 5 roles
  - Adds `role` column to `user` table
  - Migrates existing superusers to ADMIN role

### 2. Security Module Enhancements

#### New Access Control Functions
```python
# app/core/security.py

async def get_current_printer_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current active printer user."""

def require_roles(allowed_roles: List[UserRole]):
    """Dependency factory for role-based access control."""

async def get_current_manager_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current active manager user."""

async def get_current_officer_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current active officer user (can process applications)."""
```

### 3. Printer-Specific API Endpoints

#### New API Routes: `/api/v1/printer/`

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/printer/dashboard` | GET | Get printer dashboard data | PRINTER + |
| `/printer/queue` | GET | Get print queue for operator | PRINTER + |
| `/printer/jobs/assigned` | GET | Get jobs assigned to current user | PRINTER + |
| `/printer/jobs/{id}/start` | POST | Start a print job | PRINTER + |
| `/printer/jobs/{id}/complete` | POST | Complete a print job | PRINTER + |
| `/printer/jobs/{id}/application` | GET | Get application details for printing | PRINTER + |
| `/printer/statistics` | GET | Get printer statistics | PRINTER + |
| `/printer/printers` | GET | Get available printers | PRINTER + |

*PRINTER + means PRINTER role or higher (ADMIN)*

#### Key Features

1. **Role-Based Security**: All endpoints require PRINTER role or superuser
2. **User Isolation**: Operators only see jobs assigned to them
3. **Complete Workflow**: Start → Print → Complete with quality checks
4. **Audit Logging**: All actions are logged for security
5. **Application Access**: View citizen/license data for printing context

### 4. Database Schema Updates

```sql
-- Add role enum
CREATE TYPE userrole AS ENUM ('admin', 'manager', 'officer', 'printer', 'viewer');

-- Add role column
ALTER TABLE "user" ADD COLUMN role userrole NOT NULL DEFAULT 'officer';

-- Update existing superusers
UPDATE "user" SET role = 'admin' WHERE is_superuser = true;
```

## Frontend Implementation

### 1. New Printer Dashboard Component

#### File: `src/pages/PrinterDashboard.tsx`

**Features:**
- **User Info Display**: Shows printer operator details
- **Statistics Cards**: Assigned jobs, currently printing, completed today
- **Print Queue Table**: Interactive job management
- **Action Buttons**: Start printing, complete jobs, view applications
- **Print File Access**: Download PDFs for printing
- **Quality Control**: Mark jobs as passed/failed with notes

#### Key UI Components:
- Statistics dashboard with real-time counts
- Interactive print queue with status indicators
- Modal dialogs for starting/completing jobs
- Application details viewer with citizen information
- Printer selection and quality check forms

### 2. API Service Integration

#### File: `src/api/services.ts`

```typescript
export const printerService = {
  getDashboard: async (): Promise<any> => { ... },
  getPrintQueue: async (skip = 0, limit = 50): Promise<any> => { ... },
  startPrintJob: async (printJobId: number, startData: any): Promise<any> => { ... },
  completePrintJob: async (printJobId: number, completeData: any): Promise<any> => { ... },
  getApplicationForPrintJob: async (printJobId: number): Promise<any> => { ... },
  // ... more methods
};
```

### 3. Routing and Access Control

#### Protected Routes
```typescript
// Printer-only routes
<Route element={<ProtectedRoute requiredRole="printer" />}>
  <Route element={<MainLayout />}>
    <Route path="/printer" element={<PrinterDashboard />} />
  </Route>
</Route>
```

## User Management

### Creating Printer Users

#### Option 1: Using the Creation Script
```bash
cd "AMPRO Licence"
python create_printer_user.py
```

#### Option 2: Programmatically
```python
from app.crud.crud_user import user as user_crud
from app.models.user import UserRole
from app.schemas.user import UserCreate

user_data = UserCreate(
    username="printer1",
    email="printer1@agency.com", 
    password="secure_password",
    full_name="Print Operator 1",
    role=UserRole.PRINTER,
    department="Printing"
)

new_user = user_crud.create(db, obj_in=user_data)
```

#### Option 3: Via API (Admin Required)
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "printer1",
    "email": "printer1@agency.com",
    "password": "secure_password",
    "full_name": "Print Operator 1",
    "role": "printer",
    "department": "Printing"
  }'
```

## Security Features

### 1. Role-Based Access Control
- Printer users can **ONLY** access print-related functions
- No access to application creation/modification
- No access to user management
- No access to system administration

### 2. User Isolation
- Operators only see jobs assigned specifically to them
- Cannot view or modify other operators' work
- Secure job assignment workflow

### 3. Audit Trail
All printer actions are logged:
- Dashboard access
- Print queue viewing
- Job starting/completion
- Application viewing
- Statistical access

### 4. Data Protection
- Limited citizen data exposure (only during active print jobs)
- Secure file access for print PDFs
- Quality control with required sign-offs

## Operational Workflow

### 1. Print Job Assignment (Admin/Manager)
```
1. Admin assigns print job to printer operator
2. Job appears in operator's queue with "assigned" status
3. Operator receives notification (if implemented)
```

### 2. Print Job Processing (Printer Operator)
```
1. Login with PRINTER role credentials
2. Access /printer dashboard
3. View assigned jobs in queue
4. Select job and click "Start Printing"
5. Choose printer from available list
6. Monitor printing process
7. Complete job with quality check
8. Add notes if needed
9. Job marked as completed
```

### 3. Quality Control
```
- Quality Check: Pass/Fail options
- Notes field for issues or observations
- Failed jobs can be reassigned or flagged
- Complete audit trail maintained
```

## Integration Points

### 1. Existing Workflow System
- Integrates with existing print job management
- Uses existing PrintJob model and CRUD operations
- Maintains compatibility with workflow dashboard

### 2. File Management
- Uses existing file service for PDF access
- Secure download links for print files
- Supports front, back, and combined PDF formats

### 3. Audit System
- All actions logged to existing audit_log table
- Maintains security and compliance requirements
- Searchable and reportable audit trail

## Testing

### Manual Testing Checklist

1. **User Creation**
   - [ ] Run `python create_printer_user.py`
   - [ ] Verify user created with PRINTER role
   - [ ] Confirm login works

2. **Dashboard Access**
   - [ ] Login with printer credentials
   - [ ] Navigate to `/printer`
   - [ ] Verify dashboard loads with user info
   - [ ] Check statistics display

3. **Print Job Processing**
   - [ ] Assign job to printer (as admin)
   - [ ] View job in printer queue
   - [ ] Start job with printer selection
   - [ ] Complete job with quality check
   - [ ] Verify audit logs

4. **Security Verification**
   - [ ] Confirm no access to `/workflow`
   - [ ] Confirm no access to `/admin`
   - [ ] Confirm no access to application CRUD
   - [ ] Verify only assigned jobs visible

## Deployment

### 1. Database Migration
```bash
# Apply the role migration
alembic upgrade head
```

### 2. Backend Deployment
- Deploy updated backend with new printer endpoints
- Verify role-based security is working
- Test printer API endpoints

### 3. Frontend Deployment
- Deploy updated frontend with printer dashboard
- Verify routing and authentication
- Test printer-specific UI components

### 4. User Setup
- Create initial printer operator accounts
- Assign appropriate permissions
- Train operators on new interface

## Monitoring and Maintenance

### 1. Performance Monitoring
- Monitor printer dashboard response times
- Track print job completion rates
- Monitor concurrent printer sessions

### 2. Security Monitoring
- Review audit logs for unauthorized access attempts
- Monitor role-based access compliance
- Track user authentication patterns

### 3. Operational Metrics
- Print job processing times
- Quality check pass/fail rates
- Operator productivity metrics
- Printer utilization statistics

## Troubleshooting

### Common Issues

1. **Login Issues**
   - Verify user has PRINTER role assigned
   - Check user is_active status
   - Verify password correctness

2. **Dashboard Not Loading**
   - Check backend printer endpoints are deployed
   - Verify API authentication tokens
   - Check browser console for errors

3. **No Print Jobs Visible**
   - Confirm jobs are assigned to the specific user
   - Check print job status (should be 'assigned' or 'printing')
   - Verify user permissions

4. **Cannot Start Print Jobs**
   - Verify job status is 'assigned'
   - Check printer availability
   - Confirm user owns the assigned job

## Future Enhancements

### Potential Improvements
1. **Real-time Notifications**: Push notifications for new job assignments
2. **Mobile Support**: Mobile-responsive printer dashboard
3. **Printer Status Integration**: Real-time printer status monitoring
4. **Batch Processing**: Support for bulk print job operations
5. **Performance Analytics**: Detailed printer operator performance metrics
6. **Auto-Assignment**: Automatic job assignment based on workload
7. **Print Preview**: Preview functionality before printing
8. **Barcode Scanning**: Barcode-based job tracking

---

## Summary

The PRINTER role implementation provides a secure, focused interface for license printing operations while maintaining the system's security and audit requirements. This role-based approach ensures that printer operators have exactly the access they need without compromising system security or data integrity.

The implementation includes:
✅ **Backend API** with secure role-based endpoints
✅ **Frontend Dashboard** with intuitive printer operator interface
✅ **User Management** with easy account creation
✅ **Security Controls** with comprehensive access restrictions
✅ **Audit Logging** for complete operational transparency
✅ **Integration** with existing workflow and file systems

This solution scales well for large-scale license printing operations while maintaining operational security and compliance requirements. 