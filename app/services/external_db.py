from typing import Dict, List, Optional, Any
from datetime import date, datetime, timedelta
import random
from faker import Faker

# Initialize faker for South African content
fake = Faker('en_ZA')


class ExternalCitizenDB:
    """
    Simulated external Citizen Identity Database.
    In a real implementation, this would connect to a government database.
    """
    
    @staticmethod
    def search_by_id_number(id_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for a citizen by ID number in the external database.
        """
        # In a real implementation, this would make an API call or database query
        # For simulation, we'll generate random data based on the ID number
        
        # South African ID structure: YYMMDD GSSS CAZ
        # YY = Year of birth
        # MM = Month of birth
        # DD = Day of birth
        # G = Gender (0-4 Female, 5-9 Male)
        # SSS = Sequence number for people born on the same day
        # C = Citizenship (0 = SA, 1 = Permanent resident)
        # A = Usually 8 (apartheid race classification, now fixed at 8)
        # Z = Control digit
        
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            return None
            
        # Generate consistent but random data based on the ID
        random.seed(id_number)  # Seed with ID for consistency
        
        # Extract info from ID
        yy = int(id_number[0:2])
        mm = int(id_number[2:4])
        dd = int(id_number[4:6])
        gender_digit = int(id_number[6])
        
        # Validate basic info
        if mm < 1 or mm > 12 or dd < 1 or dd > 31:
            return None
            
        # Determine gender
        gender = "female" if gender_digit < 5 else "male"
        
        # Determine birth year (adjust for century)
        year = 1900 + yy if yy >= 20 else 2000 + yy
        
        try:
            # Create birth date
            birth_date = date(year, mm, dd)
            
            # Make sure it's a valid date
            if birth_date > date.today():
                return None
        except ValueError:
            # Invalid date
            return None
            
        # Generate name based on gender
        if gender == "male":
            first_name = fake.first_name_male()
        else:
            first_name = fake.first_name_female()
            
        # Create a person
        person = {
            "id_number": id_number,
            "first_name": first_name,
            "last_name": fake.last_name(),
            "date_of_birth": birth_date,
            "gender": gender,
            "marital_status": random.choice(["single", "married", "divorced", "widowed"]),
            "address_line1": fake.street_address(),
            "address_line2": fake.secondary_address() if random.random() > 0.7 else None,
            "city": fake.city(),
            "state_province": fake.province(),
            "postal_code": fake.postcode(),
            "country": "South Africa",
            "birth_place": fake.city(),
            "nationality": "South African",
            "data_source": "National Identity Database"
        }
        
        return person


class ExternalDriverDB:
    """
    Simulated external Driver Database.
    In a real implementation, this would connect to a government database.
    """
    
    @staticmethod
    def search_by_id_number(id_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for a driver by ID number in the external database.
        """
        # In a real implementation, this would make an API call or database query
        # For simulation, we'll generate random data based on the ID number
        
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            return None
            
        # Generate consistent but random data based on the ID
        random.seed(id_number)  # Seed with ID for consistency
        
        # 80% chance of having driver information
        if random.random() > 0.2:
            # Get categories based on age
            yy = int(id_number[0:2])
            year = 1900 + yy if yy >= 20 else 2000 + yy
            birth_date = date(year, int(id_number[2:4]), int(id_number[4:6]))
            age = (date.today() - birth_date).days // 365
            
            # Determine available categories based on age
            categories = []
            if age >= 16:
                categories.append("A")  # Motorcycle
            if age >= 18:
                categories.append("B")  # Light vehicles
            if age >= 21:
                categories.extend(["C", "EB"])  # Heavy vehicles, Light articulated
            if age >= 25 and random.random() > 0.5:
                categories.append("EC")  # Heavy articulated
                
            if not categories:
                return None
                
            # Pick 1-3 random categories
            selected_categories = random.sample(
                categories, 
                min(len(categories), random.randint(1, 3))
            )
            
            # Determine if there are medical conditions
            has_medical = random.random() > 0.9
            medical_conditions = None
            if has_medical:
                conditions = [
                    "Visual impairment - corrective lenses required",
                    "Hearing impairment",
                    "Mobility restriction - modified controls required",
                    "Epilepsy - controlled with medication",
                    "Diabetes - regular monitoring required"
                ]
                medical_conditions = random.choice(conditions)
                
            # Determine if there are restrictions
            has_restrictions = random.random() > 0.8
            restrictions = None
            if has_restrictions:
                restriction_list = [
                    "Automatic transmission only",
                    "Daylight driving only",
                    "No highway driving",
                    "Maximum speed restriction: 80km/h",
                    "Specialized controls required"
                ]
                restrictions = random.choice(restriction_list)
            
            # Create driver record
            return {
                "id_number": id_number,
                "license_categories": selected_categories,
                "license_status": random.choice(["active", "expired", "suspended", "revoked"]),
                "first_issue_date": (date.today() - timedelta(days=random.randint(365, 365*20))),
                "test_results": {
                    "theoretical": random.randint(60, 100),
                    "practical": random.randint(60, 100)
                },
                "medical_conditions": medical_conditions,
                "restrictions": restrictions,
                "data_source": "Driver Licensing Database"
            }
        
        return None


class ExternalInfringementDB:
    """
    Simulated external Traffic Infringement Database.
    In a real implementation, this would connect to a government database.
    """
    
    @staticmethod
    def search_by_id_number(id_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for traffic infringements by ID number in the external database.
        """
        # In a real implementation, this would make an API call or database query
        # For simulation, we'll generate random data based on the ID number
        
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            return None
            
        # Generate consistent but random data based on the ID
        random.seed(id_number)  # Seed with ID for consistency
        
        # 30% chance of having infringements
        if random.random() > 0.7:
            # Generate 1-5 infringements
            num_infringements = random.randint(1, 5)
            
            infringement_types = [
                "Speeding",
                "Parking violation",
                "Running red light",
                "Driving without license",
                "Driving under influence",
                "Unsafe lane change",
                "Using cell phone while driving",
                "Failure to yield",
                "Overloaded vehicle",
                "Defective vehicle"
            ]
            
            infringement_statuses = [
                "paid",
                "unpaid",
                "disputed",
                "dismissed",
                "pending court"
            ]
            
            infringements = []
            for _ in range(num_infringements):
                # Generate date in past 3 years
                infringement_date = date.today() - timedelta(days=random.randint(1, 365*3))
                
                infringements.append({
                    "infringement_id": f"INF-{random.randint(10000, 99999)}",
                    "date": infringement_date,
                    "type": random.choice(infringement_types),
                    "location": f"{fake.city()}, {fake.street_name()}",
                    "status": random.choice(infringement_statuses),
                    "penalty_amount": random.randint(300, 5000),  # Amount in Rand
                    "points": random.randint(1, 6)
                })
            
            # Create infringement record
            return {
                "id_number": id_number,
                "infringement_count": len(infringements),
                "total_points": sum(inf["points"] for inf in infringements),
                "license_status": "active" if sum(inf["points"] for inf in infringements) < 12 else "suspended",
                "infringements": infringements,
                "data_source": "Traffic Infringement Database"
            }
        
        return None


def consolidate_citizen_data(id_number: str) -> Dict[str, Any]:
    """
    Consolidate data from all external databases.
    """
    result = {
        "success": False,
        "data": {},
        "sources": []
    }
    
    # Get data from Citizen Identity Database
    citizen_data = ExternalCitizenDB.search_by_id_number(id_number)
    if citizen_data:
        result["data"] = citizen_data
        result["sources"].append("citizen_db")
        result["success"] = True
    else:
        return result
    
    # Get data from Driver Database
    driver_data = ExternalDriverDB.search_by_id_number(id_number)
    if driver_data:
        result["data"]["driver_info"] = driver_data
        result["sources"].append("driver_db")
    
    # Get data from Infringement Database
    infringement_data = ExternalInfringementDB.search_by_id_number(id_number)
    if infringement_data:
        result["data"]["infringement_info"] = infringement_data
        result["sources"].append("infringement_db")
    
    return result 