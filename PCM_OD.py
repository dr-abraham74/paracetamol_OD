class ParacetamolOverdoseDecision:
    def __init__(self):
        """Initialize the decision algorithm with default thresholds"""
        # These parameters can be easily modified later
        self.high_risk_dose_threshold = 150  # mg/kg
        self.moderate_risk_dose_threshold = 75  # mg/kg
        self.immediate_treatment_time_hours = 8  # hours since overdose
        self.blood_test_wait_time_hours = 4  # hours since overdose
        
    def get_patient_data(self):
        """Collect patient information from console input"""
        print("=== Paracetamol Overdose Treatment Decision Tool ===\n")
        
        try:
            # Get basic patient information
            age = int(raw_input("Enter patient age (years): "))
            weight = float(raw_input("Enter patient weight (kg): "))
            
            # Get overdose details
            dose_mg = float(raw_input("Enter paracetamol dose taken (mg): "))
            time_hours = float(raw_input("Enter time since overdose (hours): "))
            
            # Check if staggered overdose with validation
            while True:
                staggered_input = raw_input("Was this a staggered overdose? (Y/N): ")
                staggered_clean = staggered_input.upper().strip()
                if staggered_clean in ['Y', 'N']:
                    is_staggered = staggered_clean == 'Y'
                    break
                else:
                    print("Please enter Y or N only")
            
            return {
                'age': age,
                'weight': weight,
                'dose_mg': dose_mg,
                'time_hours': time_hours,
                'is_staggered': is_staggered
            }
            
        except ValueError:
            print("Error: Please enter valid numeric values")
            return None
        except Exception as e:
            print("Error collecting patient data: " + str(e))
            return None
    
    def calculate_dose_per_kg(self, dose_mg, weight):
        """Calculate paracetamol dose per kg body weight"""
        return dose_mg / weight
    
    def make_treatment_decision(self, patient_data):
        """
        Make treatment recommendation based on patient data
        This is where the decision logic can be easily modified
        """
        dose_per_kg = self.calculate_dose_per_kg(patient_data['dose_mg'], patient_data['weight'])
        
        # Decision logic - can be easily modified
        if patient_data['is_staggered']:
            # Staggered overdose - different approach
            return self._handle_staggered_overdose(patient_data, dose_per_kg)
        else:
            # Single acute overdose
            return self._handle_acute_overdose(patient_data, dose_per_kg)
    
    def _handle_staggered_overdose(self, patient_data, dose_per_kg):
        """Handle staggered overdose cases"""
        decision = {
            'dose_per_kg': dose_per_kg,
            'recommendation': 'START_NAC',
            'reason': 'Staggered overdose - start NAC immediately due to unpredictable absorption'
        }
        return decision
    
    def _handle_acute_overdose(self, patient_data, dose_per_kg):
        """Handle acute single overdose cases"""
        time_hours = patient_data['time_hours']
        
        # High risk dose
        if dose_per_kg >= self.high_risk_dose_threshold:
            if time_hours <= self.immediate_treatment_time_hours:
                reason = 'High risk dose (' + str(round(dose_per_kg, 1)) + ' mg/kg) within ' + str(self.immediate_treatment_time_hours) + ' hours'
                decision = {
                    'dose_per_kg': dose_per_kg,
                    'recommendation': 'START_NAC',
                    'reason': reason
                }
            else:
                decision = {
                    'dose_per_kg': dose_per_kg,
                    'recommendation': 'WAIT_FOR_BLOODS',
                    'reason': 'High risk dose but >8 hours - check paracetamol levels and liver function'
                }
        
        # Moderate risk dose
        elif dose_per_kg >= self.moderate_risk_dose_threshold:
            if time_hours <= self.blood_test_wait_time_hours:
                reason = 'Moderate risk dose - wait ' + str(self.blood_test_wait_time_hours) + ' hours for blood levels'
                decision = {
                    'dose_per_kg': dose_per_kg,
                    'recommendation': 'WAIT_FOR_BLOODS',
                    'reason': reason
                }
            else:
                decision = {
                    'dose_per_kg': dose_per_kg,
                    'recommendation': 'WAIT_FOR_BLOODS',
                    'reason': 'Check paracetamol levels and liver function tests'
                }
        
        # Low risk dose
        else:
            reason = 'Low risk dose (' + str(round(dose_per_kg, 1)) + ' mg/kg) - unlikely to cause toxicity'
            decision = {
                'dose_per_kg': dose_per_kg,
                'recommendation': 'NO_ACTION',
                'reason': reason
            }
        
        return decision
    
    def display_results(self, patient_data, decision):
        """Display the treatment recommendation"""
        print("\n" + "="*50)
        print("TREATMENT RECOMMENDATION")
        print("="*50)
        
        print("Patient: " + str(patient_data['age']) + " years old")
        print("Weight: " + str(patient_data['weight']) + " kg")
        print("Dose taken: " + str(patient_data['dose_mg']) + " mg")
        print("Time since overdose: " + str(patient_data['time_hours']) + " hours")
        print("Staggered overdose: " + ("Yes" if patient_data['is_staggered'] else "No"))
        print("Dose per kg: " + str(round(decision['dose_per_kg'], 1)) + " mg/kg")
        
        print("\nRECOMMENDATION: " + decision['recommendation'])
        print("REASON: " + decision['reason'])
        
        # Additional guidance based on recommendation
        if decision['recommendation'] == 'START_NAC':
            print("\n! START N-ACETYLCYSTEINE (NAC) IMMEDIATELY")
            print("- Follow standard NAC protocol")
            print("- Monitor liver function tests")
        elif decision['recommendation'] == 'WAIT_FOR_BLOODS':
            print("\n* OBTAIN BLOOD TESTS")
            print("- Paracetamol level (plot on nomogram if <24hrs)")
            print("- Liver function tests (ALT, AST)")
            print("- Consider NAC if levels indicate risk")
        elif decision['recommendation'] == 'NO_ACTION':
            print("\n+ NO IMMEDIATE TREATMENT REQUIRED")
            print("- Provide supportive care")
            print("- Advise patient to return if symptoms develop")
        
        print("\n! DISCLAIMER: This is a decision support tool only.")
        print("Always consider full clinical context and local guidelines.")
    
    def update_parameters(self):
        """Allow modification of decision parameters"""
        print("\n=== Update Decision Parameters ===")
        print("Current high risk threshold: " + str(self.high_risk_dose_threshold) + " mg/kg")
        print("Current moderate risk threshold: " + str(self.moderate_risk_dose_threshold) + " mg/kg")
        print("Current immediate treatment time: " + str(self.immediate_treatment_time_hours) + " hours")
        
        try:
            new_high = raw_input("Enter new high risk threshold (current: " + str(self.high_risk_dose_threshold) + "): ").strip()
            if new_high:
                self.high_risk_dose_threshold = float(new_high)
            
            new_moderate = raw_input("Enter new moderate risk threshold (current: " + str(self.moderate_risk_dose_threshold) + "): ").strip()
            if new_moderate:
                self.moderate_risk_dose_threshold = float(new_moderate)
                
            new_time = raw_input("Enter new immediate treatment time (current: " + str(self.immediate_treatment_time_hours) + "): ").strip()
            if new_time:
                self.immediate_treatment_time_hours = float(new_time)
                
            print("Parameters updated successfully!")
            
        except ValueError:
            print("Error updating parameters. Please enter valid numbers.")
    
    def run(self):
        """Main program loop"""
        while True:
            print("\n" + "="*50)
            print("1. Assess patient")
            print("2. Update parameters")
            print("3. Exit")
            choice = raw_input("Select option (1-3): ").strip()
            
            if choice == '1':
                patient_data = self.get_patient_data()
                if patient_data:
                    decision = self.make_treatment_decision(patient_data)
                    self.display_results(patient_data, decision)
            
            elif choice == '2':
                self.update_parameters()
            
            elif choice == '3':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please select 1, 2, or 3.")


# Main execution
if __name__ == "__main__":
    # Create and run the decision algorithm
    decision_tool = ParacetamolOverdoseDecision()
    decision_tool.run()