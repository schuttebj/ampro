# AMPRO Licence - Notification System Architecture

## Overview
The AMPRO Licence notification system has been designed with a **unified notification approach** that leverages specialized domain services for business logic while keeping all notification creation centralized.

## 🏗️ Architecture Design

### Unified Notification with Domain Services
Following AMPRO's principle of separation of concerns, the notification system combines:

```
📁 app/
├── 📁 services/
│   ├── 📄 notification_service.py          # ALL notification creation methods
│   ├── 📄 automation_service.py            # Rule processing & batch automation logic
│   └── 📄 iso_compliance_check_service.py  # ISO validation & compliance logic
│
├── 📁 api/v1/endpoints/
│   └── 📄 notifications.py                 # ALL notification endpoints (core + automation + ISO)
│
├── 📁 models/
│   └── 📄 notification.py                  # Unified notification models
│
└── 📁 schemas/
    └── 📄 notification.py                  # Unified notification schemas
```

## 🔧 Core Components

### 1. Unified Notification Service (`notification_service.py`)
**Responsibility**: ALL notification creation and management

```python
class NotificationService:
    """
    Comprehensive notification service that handles ALL notification types.
    Uses specialized domain services for business logic, then creates notifications.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.automation_service = AutomationService(db)
        self.iso_service = ISOComplianceCheckService(db)
    
    # Core notification methods
    - create_from_audit_log()
    - create_from_transaction()
    - create_workflow_notification()
    
    # Automation notification methods (calls AutomationService)
    - create_batch_processing_notification()
    - create_rule_engine_notification()
    - create_smart_assignment_notification()
    
    # ISO compliance notification methods (calls ISOComplianceCheckService)
    - create_iso_compliance_notification()
    - create_validation_notification()
    - create_bulk_compliance_notification()
    - create_auto_remediation_notification()
    
    # Management methods
    - get_user_notifications()
    - mark_as_read()
    - bulk_update_status()
    - get_notification_stats()
```

### 2. Automation Service (`automation_service.py`)
**Responsibility**: Rule-based automation and batch processing business logic

```python
class AutomationService:
    """
    Service for rule-based automation and batch processing logic.
    This service performs the actual automation work - notifications are handled separately.
    """
    
    # Business logic methods
    - evaluate_application_against_rules()
    - process_batch_applications()
    - smart_assign_applications()
    - get_automation_statistics()
    
    # Rule management
    - _application_matches_rule()
    - _approve_application()
    - _execute_assignment()
```

**Use Cases**:
- Rule evaluation and application
- Batch processing of applications
- Smart assignment algorithms
- Automation performance tracking

### 3. ISO Compliance Check Service (`iso_compliance_check_service.py`)
**Responsibility**: ISO 18013 compliance validation and checking logic

```python
class ISOComplianceCheckService:
    """
    Service for ISO 18013 compliance validation and checking logic.
    This service performs the actual compliance checks - notifications are handled separately.
    """
    
    # Validation methods
    - validate_license_compliance()
    - bulk_validate_licenses()
    - auto_remediate_compliance_issues()
    - get_compliance_statistics()
    
    # Individual validation checks
    - _validate_mrz()
    - _validate_security_features()
    - _validate_biometric_data()
    - _validate_chip_data()
    - _validate_digital_signature()
    - _validate_physical_standards()
```

**Use Cases**:
- Comprehensive ISO compliance validation
- Individual validation processes (MRZ, biometric, security, chip)
- Auto-remediation of compliance issues
- Bulk compliance operations
- Compliance scoring and analytics

## 🛣️ API Endpoint Structure

### Unified Endpoints (`/api/v1/notifications/`)
```
# Core notification management
GET    /                    # Get user notifications
GET    /stats              # Get notification statistics  
PUT    /{id}/read          # Mark notification as read
PUT    /bulk               # Bulk update notifications
GET    /preferences        # Get user preferences
PUT    /preferences        # Update user preferences
POST   /workflow           # Create workflow notification
WS     /ws/{user_id}       # WebSocket real-time connection

# Basic workflow integration
POST   /trigger/application-approved/{id}
POST   /trigger/print-completed/{batch_id}

# Automation notification endpoints
POST   /automation/batch-processing      # Batch processing notifications
POST   /automation/rule-engine          # Rule engine notifications
POST   /automation/smart-assignment     # Smart assignment notifications
GET    /automation/stats                # Automation notification stats

# ISO compliance notification endpoints
POST   /iso/compliance-validation       # ISO compliance notifications
POST   /iso/validation                  # Validation notifications
POST   /iso/bulk-compliance             # Bulk compliance operations
POST   /iso/auto-remediation            # Auto-remediation notifications
GET    /iso/compliance-stats            # ISO compliance stats
```

## 📊 Integration Flow

### Automation Flow
```python
# 1. Frontend calls automation endpoint
POST /api/v1/notifications/automation/batch-processing
{
    "batch_type": "approval",
    "application_ids": [1, 2, 3, 4, 5],
    "collection_point": "Main Office"
}

# 2. NotificationService calls AutomationService for business logic
results = self.automation_service.process_batch_applications(
    application_ids=application_ids,
    collection_point=collection_point
)

# 3. NotificationService creates notification based on results
notification = crud.notification.create(self.db, obj_in=notification_create)

# 4. Real-time WebSocket notification sent to user
```

### ISO Compliance Flow
```python
# 1. Frontend calls ISO compliance endpoint
POST /api/v1/notifications/iso/compliance-validation
{
    "license_id": 12345,
    "iso_standard": "ISO_18013_1",
    "full_validation": true
}

# 2. NotificationService calls ISOComplianceCheckService for validation
compliance_result = self.iso_service.validate_license_compliance(
    license_id=license_id,
    iso_standard=iso_standard,
    full_validation=full_validation
)

# 3. NotificationService creates notification based on compliance result
notification = crud.notification.create(self.db, obj_in=notification_create)

# 4. Critical failures automatically notify compliance officers
```

## 🎯 Benefits of This Architecture

### 1. **Unified Notification Management**
- **Single Source**: All notifications go through one service
- **Consistent API**: Uniform notification structure and endpoints
- **Centralized Logic**: Notification preferences, delivery, and management in one place

### 2. **Separation of Business Logic**
- **Domain Expertise**: AutomationService focuses on automation logic
- **ISO Expertise**: ISOComplianceCheckService focuses on compliance validation
- **Clean Boundaries**: Business logic separated from notification concerns

### 3. **Following AMPRO Patterns**
- **Consistent Architecture**: Matches existing service patterns
- **Integration Ready**: Works with existing AMPRO infrastructure
- **Familiar Structure**: Developers know this pattern

### 4. **Scalability & Maintainability**
- **Independent Growth**: Domain services can evolve independently
- **Easy Testing**: Business logic can be tested separately from notifications
- **Clear Responsibilities**: Each service has a single, well-defined purpose

## 📈 Real-World Usage Examples

### Frontend Integration (ApplicationReview.tsx)
```typescript
// Frontend calls unified notification API
const response = await api.post('/api/v1/notifications/automation/batch-processing', {
  batch_type: 'approval',
  application_ids: selectedApplications,
  collection_point: bulkCollectionPoint,
  preview_mode: false
});

// Backend automatically:
// 1. Uses AutomationService to process applications
// 2. Creates appropriate notifications
// 3. Sends real-time updates via WebSocket
```

### Frontend Integration (ISOCompliance.tsx)
```typescript
// Frontend calls unified notification API
const response = await api.post('/api/v1/notifications/iso/compliance-validation', {
  license_id: licenseId,
  iso_standard: 'ISO_18013_1',
  full_validation: true,
  notify_compliance_officers: true
});

// Backend automatically:
// 1. Uses ISOComplianceCheckService to validate license
// 2. Creates compliance notifications
// 3. Notifies compliance officers if critical issues found
```

## ✅ Implementation Status

### ✅ Complete
- [x] Unified notification service with all methods
- [x] Separate automation service for business logic
- [x] Separate ISO compliance service for validation logic
- [x] Consolidated API endpoints in single file
- [x] Proper enum patterns (no data mismatch issues)
- [x] WebSocket real-time integration
- [x] Audit log integration
- [x] Domain service integration

### 🔄 Next Steps
- [ ] Database migration for notification tables
- [ ] User model relationship updates  
- [ ] CRUD operations implementation
- [ ] Router registration in main API
- [ ] Frontend integration testing

This architecture provides a **clean, unified, and well-organized** notification system that keeps all notification logic centralized while leveraging specialized domain services for complex business operations. The approach follows AMPRO's existing patterns while supporting both current automation features and ISO compliance requirements. 