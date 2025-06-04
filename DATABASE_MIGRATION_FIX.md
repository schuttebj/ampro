# Database Migration Fix for Enhanced Fields

## Problem Summary

The frontend was experiencing 500 errors when trying to access the backend API because the database schema was out of sync with the code models. Specifically, the following columns were missing from the production database:

### Missing Columns in `citizen` table:
- `identification_type` - for different ID types (RSA ID, Traffic Register, Foreign ID)
- `country_of_issue` - for foreign IDs
- `nationality` - citizen nationality  
- `middle_name`, `initials` - additional name fields
- `marital_status` - marital status enum
- `official_language` - SA official language preference
- Enhanced contact fields: `phone_home`, `phone_daytime`, `phone_cell`, `fax_number`
- Enhanced address fields: postal and street address components
- `preferred_address_type` - address preference
- `birth_place` - place of birth
- Enhanced photo management fields

### Missing Columns in `licenseapplication` table:
- `transaction_type` - type of license transaction
- `photograph_attached`, `photograph_count` - Section A fields
- `previous_license_refusal`, `refusal_details` - Section B fields  
- `card_notice_status`, `police_report_station`, etc. - Section C fields
- All Section D declaration fields (legal and medical declarations)
- `information_true_correct`, `applicant_signature_date` - declaration completion
- `is_draft`, `submitted_at` - draft management

## Solution

### 1. Migration File Created
Created `alembic/versions/022_add_enhanced_citizen_and_transaction_fields.py` that:

- ✅ Creates required enum types (`identificationtype`, `transactiontype`, etc.)
- ✅ Adds all missing fields to `citizen` table with appropriate defaults
- ✅ Adds all missing fields to `licenseapplication` table with appropriate defaults
- ✅ Sets proper constraints and relationships
- ✅ Includes rollback functionality in `downgrade()`

### 2. Deployment Script Created
Created `deploy_enhanced_fields.py` that:

- ✅ Checks database connection
- ✅ Creates database backup (production would use pg_dump)
- ✅ Applies the migration using Alembic
- ✅ Verifies new fields exist in database
- ✅ Provides detailed logging and error handling

## Deployment Instructions

### Step 1: Apply Migration to Production

Run the deployment script on the production server:

```bash
# In the AMPRO Licence directory
python deploy_enhanced_fields.py
```

**OR** apply the migration manually:

```bash
# Check current migration state
alembic current

# Apply the migration
alembic upgrade head

# Verify new state
alembic current
```

### Step 2: Verify Backend Works

After applying the migration, verify the backend API endpoints work:

```bash
# Test citizen endpoint
curl https://ampro-licence.onrender.com/api/v1/citizens/

# Test applications endpoint  
curl https://ampro-licence.onrender.com/api/v1/applications/

# Test fees endpoint
curl https://ampro-licence.onrender.com/api/v1/fees/
```

### Step 3: Verify Frontend Works

1. Visit https://ampro-platform.vercel.app
2. Navigate to Applications → New Application
3. Verify the enhanced form loads without errors
4. Test citizen search functionality
5. Test form sections and validation

## Migration Details

### New Enum Types Added:
- `identificationtype` - RSA ID, Traffic Register, Foreign ID
- `officiallanguage` - All 11 SA official languages
- `addresstype` - Postal vs Street address preference
- `transactiontype` - All SA license transaction types
- `cardnoticestatus` - Card status options (theft, loss, etc.)

### Enhanced Citizen Model Features:
- ✅ Support for different ID types and foreign documents
- ✅ Comprehensive name handling (first, middle, last, initials)
- ✅ Enhanced contact information (multiple phone types, fax)
- ✅ Separate postal and street addresses
- ✅ SA-specific fields (official language, nationality)
- ✅ Enhanced photo management for ISO compliance

### Enhanced License Application Features:
- ✅ South African license application form sections A-D
- ✅ Transaction type-specific form sections
- ✅ Comprehensive declaration handling
- ✅ Draft management and auto-save
- ✅ Fee calculation integration

## Rollback Instructions

If issues occur, the migration can be rolled back:

```bash
# Rollback to previous migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade 021
```

## Files Modified/Created

### Backend (AMPRO Licence):
- ✅ `alembic/versions/022_add_enhanced_citizen_and_transaction_fields.py` - Migration file
- ✅ `deploy_enhanced_fields.py` - Deployment script
- ✅ `DATABASE_MIGRATION_FIX.md` - This documentation

### Frontend (Previously Fixed):
- ✅ `src/App.tsx` - Fixed ApplicationView reference
- ✅ `src/pages/admin/FeeManagement.tsx` - Fixed window.confirm usage
- ✅ `src/pages/applications/EnhancedApplicationForm.tsx` - Fixed Yup schema
- ✅ `src/pages/applications/ApplicationSections.tsx` - Fixed interface mismatch

## Expected Results After Migration

1. **Backend API**: No more 500 errors for missing columns
2. **Frontend**: Enhanced application form works properly
3. **Citizen Management**: Full SA citizen data model support
4. **License Applications**: Complete SA form sections A-D support
5. **Fee Calculation**: Dynamic fees based on transaction type and age
6. **Draft Management**: Auto-save and resume application functionality

## Monitoring

After deployment, monitor:

1. **Backend Logs**: Check for any remaining database errors
2. **Frontend Console**: Verify no CORS or API errors
3. **Application Flow**: Test complete license application process
4. **Performance**: Ensure new fields don't impact query performance

## Support

If issues occur after migration:

1. Check backend logs at https://ampro-licence.onrender.com
2. Verify migration state: `alembic current`
3. Test database connectivity: `python -c "from app.database import engine; print(engine)"`
4. Contact development team with specific error messages

---

**Migration Status**: ✅ Ready for Production Deployment  
**Risk Level**: Low (includes rollback capability)  
**Estimated Downtime**: < 5 minutes  
**Testing Required**: Yes (verify frontend and backend integration) 