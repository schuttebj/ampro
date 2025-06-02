from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app import crud
from app.models.license import Application, ApplicationStatus
from app.models.user import User


class AutomationRule:
    """
    Represents an approval rule for automated application processing
    """
    def __init__(
        self,
        rule_id: str,
        name: str,
        enabled: bool = True,
        priority: int = 1,
        conditions: Optional[Dict[str, Any]] = None,
        actions: Optional[Dict[str, Any]] = None
    ):
        self.rule_id = rule_id
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.conditions = conditions or {}
        self.actions = actions or {}


class AutomationService:
    """
    Service for rule-based automation and batch processing logic.
    This service performs the actual automation work - notifications are handled separately.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.default_rules = self._load_default_rules()

    def _load_default_rules(self) -> List[AutomationRule]:
        """Load default automation rules"""
        return [
            AutomationRule(
                rule_id="standard_driver_license",
                name="Standard Driver License - Verified Applications",
                enabled=True,
                priority=1,
                conditions={
                    "license_categories": ["B", "A1", "A2"],
                    "require_payment_verified": True,
                    "require_documents_verified": True,
                    "require_medical_verified": True,
                    "max_age_limit": 75,
                    "min_age_limit": 18
                },
                actions={
                    "auto_approve": True,
                    "priority_level": "normal",
                    "add_notes": "Auto-approved via standard verification rule"
                }
            ),
            AutomationRule(
                rule_id="commercial_license_enhanced",
                name="Commercial License - Enhanced Verification",
                enabled=True,
                priority=2,
                conditions={
                    "license_categories": ["C", "D", "CE", "DE"],
                    "require_payment_verified": True,
                    "require_documents_verified": True,
                    "require_medical_verified": True,
                    "require_biometric_enrollment": True,
                    "max_age_limit": 65
                },
                actions={
                    "auto_approve": False,
                    "priority_level": "high",
                    "add_notes": "Commercial license requires enhanced verification"
                }
            ),
            AutomationRule(
                rule_id="senior_citizen_review",
                name="Senior Citizen - Manual Review Required",
                enabled=True,
                priority=3,
                conditions={
                    "min_age_limit": 75
                },
                actions={
                    "auto_approve": False,
                    "priority_level": "high",
                    "add_notes": "Senior citizen application requires manual review"
                }
            )
        ]

    def evaluate_application_against_rules(
        self, 
        application_id: int,
        rules: Optional[List[AutomationRule]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single application against automation rules
        
        Returns:
            Dict containing rule evaluation results
        """
        application = crud.license_application.get(self.db, id=application_id)
        if not application:
            return {
                "application_id": application_id,
                "matched_rule": None,
                "auto_approve": False,
                "notes": "Application not found",
                "error": True
            }

        evaluation_rules = rules or self.default_rules
        
        # Sort rules by priority
        sorted_rules = sorted([r for r in evaluation_rules if r.enabled], key=lambda x: x.priority)

        for rule in sorted_rules:
            if self._application_matches_rule(application, rule):
                return {
                    "application_id": application_id,
                    "matched_rule": {
                        "id": rule.rule_id,
                        "name": rule.name,
                        "priority": rule.priority
                    },
                    "auto_approve": rule.actions.get("auto_approve", False),
                    "priority_level": rule.actions.get("priority_level", "normal"),
                    "notes": rule.actions.get("add_notes", ""),
                    "error": False
                }

        return {
            "application_id": application_id,
            "matched_rule": None,
            "auto_approve": False,
            "notes": "No matching rules found - requires manual review",
            "error": False
        }

    def _application_matches_rule(self, application: Application, rule: AutomationRule) -> bool:
        """Check if an application matches a specific rule's conditions"""
        conditions = rule.conditions

        # Check license category
        if "license_categories" in conditions:
            required_categories = conditions["license_categories"]
            if required_categories and application.applied_category not in required_categories:
                return False

        # Check verification requirements
        if conditions.get("require_payment_verified", False) and not application.payment_verified:
            return False
        if conditions.get("require_documents_verified", False) and not application.documents_verified:
            return False
        if conditions.get("require_medical_verified", False) and not application.medical_verified:
            return False

        # Check age limits (if citizen data available)
        if application.citizen and application.citizen.date_of_birth:
            citizen_age = self._calculate_age(application.citizen.date_of_birth)
            if "min_age_limit" in conditions and citizen_age < conditions["min_age_limit"]:
                return False
            if "max_age_limit" in conditions and citizen_age > conditions["max_age_limit"]:
                return False

        # Check excluded categories
        if "exclude_categories" in conditions:
            excluded = conditions["exclude_categories"]
            if excluded and application.applied_category in excluded:
                return False

        # Check biometric enrollment requirement
        if conditions.get("require_biometric_enrollment", False):
            # This would check against biometric enrollment status
            # Implementation depends on your biometric system
            pass

        return True

    def _calculate_age(self, date_of_birth: datetime) -> int:
        """Calculate age from date of birth"""
        today = datetime.utcnow()
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.fromisoformat(date_of_birth.replace('Z', '+00:00'))
        
        age = today.year - date_of_birth.year
        if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
            age -= 1
        return age

    def process_batch_applications(
        self,
        application_ids: List[int],
        collection_point: Optional[str] = None,
        notes: Optional[str] = None,
        preview_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple applications using automation rules
        
        Returns:
            Dict containing batch processing results
        """
        results = {
            "total": len(application_ids),
            "auto_approved": 0,
            "manual_review": 0,
            "failed": 0,
            "rules_applied": {},
            "auto_approval_candidates": [],
            "manual_review_candidates": [],
            "failed_applications": []
        }

        for app_id in application_ids:
            try:
                evaluation = self.evaluate_application_against_rules(app_id)
                
                if evaluation["error"]:
                    results["failed"] += 1
                    results["failed_applications"].append({
                        "application_id": app_id,
                        "reason": evaluation["notes"]
                    })
                    continue

                if evaluation["auto_approve"] and evaluation["matched_rule"]:
                    # Auto-approval candidate
                    results["auto_approval_candidates"].append({
                        "application_id": app_id,
                        "rule": evaluation["matched_rule"],
                        "notes": evaluation["notes"],
                        "priority_level": evaluation["priority_level"]
                    })
                    results["auto_approved"] += 1
                    
                    # Count rule applications
                    rule_id = evaluation["matched_rule"]["id"]
                    results["rules_applied"][rule_id] = results["rules_applied"].get(rule_id, 0) + 1
                    
                    # Actually approve if not in preview mode
                    if not preview_mode:
                        self._approve_application(
                            app_id, 
                            collection_point or "Main Office",
                            evaluation["notes"],
                            rule_id
                        )
                else:
                    # Manual review required
                    results["manual_review_candidates"].append({
                        "application_id": app_id,
                        "reason": evaluation["notes"],
                        "matched_rule": evaluation["matched_rule"]
                    })
                    results["manual_review"] += 1

            except Exception as e:
                results["failed"] += 1
                results["failed_applications"].append({
                    "application_id": app_id,
                    "reason": f"Processing error: {str(e)}"
                })

        return results

    def _approve_application(
        self, 
        application_id: int, 
        collection_point: str,
        notes: str,
        applied_rule: str
    ) -> bool:
        """
        Actually approve an application
        """
        try:
            application = crud.license_application.get(self.db, id=application_id)
            if not application:
                return False

            # Update application status
            application.status = ApplicationStatus.APPROVED.value
            application.review_notes = notes
            application.reviewed_at = datetime.utcnow()
            application.collection_point = collection_point
            
            # Add metadata about automation
            if not application.metadata:
                application.metadata = {}
            application.metadata.update({
                "auto_approved": True,
                "applied_rule": applied_rule,
                "automation_timestamp": datetime.utcnow().isoformat()
            })

            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            return False

    def smart_assign_applications(
        self,
        assignment_type: str,  # 'printer', 'user', 'location'
        assignment_criteria: Dict[str, Any],
        application_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Smart assignment of applications based on criteria
        """
        if application_ids is None:
            # Get pending applications if none specified
            applications = self.db.query(crud.license_application.model)\
                .filter(crud.license_application.model.status == ApplicationStatus.APPROVED.value)\
                .all()
            application_ids = [app.id for app in applications]

        results = {
            "assignment_type": assignment_type,
            "total_processed": len(application_ids),
            "successful_assignments": 0,
            "failed_assignments": 0,
            "assignments": []
        }

        for app_id in application_ids:
            try:
                assignment_target = self._determine_assignment_target(
                    app_id, assignment_type, assignment_criteria
                )
                
                if assignment_target:
                    # Perform the assignment
                    success = self._execute_assignment(app_id, assignment_type, assignment_target)
                    if success:
                        results["successful_assignments"] += 1
                        results["assignments"].append({
                            "application_id": app_id,
                            "assigned_to": assignment_target,
                            "assignment_type": assignment_type
                        })
                    else:
                        results["failed_assignments"] += 1
                else:
                    results["failed_assignments"] += 1
                    
            except Exception as e:
                results["failed_assignments"] += 1

        return results

    def _determine_assignment_target(
        self, 
        application_id: int, 
        assignment_type: str, 
        criteria: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine the best assignment target based on criteria
        """
        # This would implement smart assignment logic
        # For now, return a mock assignment
        if assignment_type == "printer":
            return criteria.get("default_printer", "Printer_001")
        elif assignment_type == "user":
            return criteria.get("default_user", "admin")
        elif assignment_type == "location":
            return criteria.get("default_location", "Main Office")
        return None

    def _execute_assignment(self, application_id: int, assignment_type: str, target: str) -> bool:
        """
        Execute the actual assignment
        """
        try:
            application = crud.license_application.get(self.db, id=application_id)
            if not application:
                return False

            if assignment_type == "printer":
                # Assign to print queue with specific printer
                if not application.metadata:
                    application.metadata = {}
                application.metadata["assigned_printer"] = target
            elif assignment_type == "location":
                application.collection_point = target
            
            self.db.commit()
            return True
            
        except Exception:
            self.db.rollback()
            return False

    def get_automation_statistics(self) -> Dict[str, Any]:
        """
        Get automation performance statistics
        """
        # This would calculate real statistics from the database
        return {
            "total_rules": len(self.default_rules),
            "active_rules": len([r for r in self.default_rules if r.enabled]),
            "automation_rate": 75.5,  # Percentage of applications auto-processed
            "avg_processing_time": 2.3,  # Average minutes
            "successful_automations_today": 45,
            "failed_automations_today": 3,
            "top_performing_rules": [
                {"rule_id": "standard_driver_license", "applications_processed": 32},
                {"rule_id": "commercial_license_enhanced", "applications_processed": 8}
            ]
        } 