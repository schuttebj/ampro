# Enum Fix for AMPRO License System

## Problem Description

The AMPRO License System was experiencing enum data mismatches that caused the following error:

```
LookupError: 'queued' is not among the defined enum values. Enum name: printjobstatus. 
Possible values: QUEUED, ASSIGNED, PRINTING, ..., CANCELLED
```

This occurred because:
1. The database contained lowercase enum values (e.g., 'queued', 'assigned')
2. The Python code expected uppercase enum values (e.g., 'QUEUED', 'ASSIGNED')
3. Previous SQL workarounds masked the issue but didn't fix the root cause

## Solution Implemented

### 1. Database Migration (014_comprehensive_enum_fix.py)

A comprehensive Alembic migration that:
- Converts the `printjob.status` column to text temporarily
- Updates all existing lowercase values to uppercase
- Recreates the enum type with correct uppercase values
- Converts the column back to the proper enum type
- Sets the correct default value

### 2. Code Cleanup

Removed SQL workarounds and restored proper enum handling in:
- `app/crud/crud_print_job.py` - Removed `cast()` and `text()` workarounds
- `app/api/v1/endpoints/workflow.py` - Replaced raw SQL insertions with proper CRUD operations

### 3. Deployment Tools

- `deploy_enum_fix.py` - Automated deployment script
- `014_comprehensive_enum_fix.py` - Database migration
- This README with deployment instructions

## Deployment Instructions

### For Development/Local Environment

1. **Backup your database** (important!):
   ```bash
   pg_dump your_database_name > backup_before_enum_fix.sql
   ```

2. **Pull the latest code**:
   ```bash
   git pull origin main
   ```

3. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the enum fix**:
   ```bash
   cd "AMPRO Licence"
   python deploy_enum_fix.py
   ```

5. **Restart your application server**

6. **Test the print queue functionality**

### For Production Environment

1. **Schedule maintenance window** - This migration modifies enum types

2. **Backup the production database**:
   ```bash
   pg_dump production_db > backup_before_enum_fix_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Deploy the code** to your production servers

4. **Run the migration**:
   ```bash
   cd /path/to/AMPRO-Licence
   python deploy_enum_fix.py
   ```

5. **Restart the application services**

6. **Monitor logs** for any enum-related errors

7. **Test critical functions** like viewing the print queue

### Manual Migration (if automated script fails)

If the automated deployment fails, you can run the migration manually:

```bash
cd "AMPRO Licence"
alembic upgrade 014
```

Or run the SQL directly:

```sql
-- Check current enum values
SELECT DISTINCT status FROM printjob;

-- Run the fix (if needed)
\i fix_database_enum_data.sql
```

## Verification

After deployment, verify the fix worked:

1. **Check enum values in database**:
   ```sql
   SELECT status, COUNT(*) FROM printjob GROUP BY status;
   ```
   Expected output: All status values should be uppercase (QUEUED, ASSIGNED, etc.)

2. **Test the print queue API**:
   ```bash
   curl -X GET "http://your-server/api/v1/workflow/print-queue"
   ```

3. **Check application logs** for enum-related errors

## Files Changed

### New Files
- `alembic/versions/014_comprehensive_enum_fix.py` - Database migration
- `deploy_enum_fix.py` - Deployment script  
- `ENUM_FIX_README.md` - This documentation

### Modified Files
- `app/crud/crud_print_job.py` - Removed SQL workarounds, restored proper enum handling
- `app/api/v1/endpoints/workflow.py` - Replaced raw SQL with proper CRUD operations

## Rollback Plan

If issues occur after deployment:

1. **Immediate rollback** (restores previous code):
   ```bash
   git revert HEAD
   # Deploy previous version
   ```

2. **Database rollback** (if migration causes issues):
   ```bash
   alembic downgrade 013
   ```

3. **Restore from backup** (last resort):
   ```bash
   psql your_database < backup_before_enum_fix.sql
   ```

## Testing Checklist

After deployment, verify these functions work:

- [ ] View print queue: `/api/v1/workflow/print-queue`
- [ ] Create test print job: `/api/v1/workflow/test/create-test-print-job`
- [ ] Assign print job to user
- [ ] Start print job
- [ ] Complete print job
- [ ] View print statistics
- [ ] View applications without print jobs

## Support

If you encounter issues:

1. Check the application logs for specific error messages
2. Verify database enum values match Python enum definitions
3. Ensure all services restarted after migration
4. Contact development team with specific error details

## Technical Details

### Enum Definitions

**PrintJobStatus** (Python):
```python
class PrintJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED" 
    PRINTING = "PRINTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
```

**Database Enum** (PostgreSQL):
```sql
CREATE TYPE printjobstatus AS ENUM (
    'QUEUED', 'ASSIGNED', 'PRINTING', 
    'COMPLETED', 'FAILED', 'CANCELLED'
);
```

The key fix was ensuring the database enum values exactly match the Python enum values. 