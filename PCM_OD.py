import streamlit as st

class ParacetamolOverdoseDecision:
    def __init__(self):
        """Initialize the decision algorithm with default thresholds"""
        # These parameters can be easily modified later
        self.high_risk_dose_threshold = 150  # mg/kg
        self.moderate_risk_dose_threshold = 75  # mg/kg
        self.immediate_treatment_time_hours = 8  # hours since overdose
        self.blood_test_wait_time_hours = 4  # hours since overdose
    
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

def main():
    st.set_page_config(
        page_title="Paracetamol Overdose Calculator",
        page_icon="💊",
        layout="wide"
    )
    
    st.title("🏥 Paracetamol Overdose Treatment Decision Tool")
    st.markdown("---")
    
    # Initialize the decision tool
    decision_tool = ParacetamolOverdoseDecision()
    
    # Sidebar for parameters
    st.sidebar.header("⚙️ Decision Parameters")
    st.sidebar.markdown("Adjust the clinical thresholds:")
    
    decision_tool.high_risk_dose_threshold = st.sidebar.number_input(
        "High Risk Dose Threshold (mg/kg)", 
        value=150.0, 
        min_value=1.0, 
        max_value=500.0,
        help="Dose above which immediate NAC is recommended"
    )
    
    decision_tool.moderate_risk_dose_threshold = st.sidebar.number_input(
        "Moderate Risk Dose Threshold (mg/kg)", 
        value=75.0, 
        min_value=1.0, 
        max_value=300.0,
        help="Dose above which blood tests are required"
    )
    
    decision_tool.immediate_treatment_time_hours = st.sidebar.number_input(
        "Immediate Treatment Time (hours)", 
        value=8.0, 
        min_value=1.0, 
        max_value=24.0,
        help="Time window for immediate NAC treatment"
    )
    
    decision_tool.blood_test_wait_time_hours = st.sidebar.number_input(
        "Blood Test Wait Time (hours)", 
        value=4.0, 
        min_value=1.0, 
        max_value=12.0,
        help="Minimum time to wait before blood tests"
    )
    
    # Main input form
    st.header("📋 Patient Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Patient Age (years)", min_value=1, max_value=120, value=30)
        weight = st.number_input("Patient Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1)
    
    with col2:
        dose_mg = st.number_input("Paracetamol Dose Taken (mg)", min_value=1.0, max_value=50000.0, value=1000.0, step=100.0)
        time_hours = st.number_input("Time Since Overdose (hours)", min_value=0.1, max_value=48.0, value=2.0, step=0.1)
    
    is_staggered = st.checkbox("Was this a staggered overdose?", help="Multiple doses taken over time rather than a single large dose")
    
    # Calculate button
    if st.button("🔍 Calculate Treatment Recommendation", type="primary"):
        # Prepare patient data
        patient_data = {
            'age': age,
            'weight': weight,
            'dose_mg': dose_mg,
            'time_hours': time_hours,
            'is_staggered': is_staggered
        }
        
        # Make decision
        decision = decision_tool.make_treatment_decision(patient_data)
        
        # Display results
        st.markdown("---")
        st.header("📊 Treatment Recommendation")
        
        # Patient summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Patient Age", str(age) + " years")
            st.metric("Weight", str(weight) + " kg")
        with col2:
            st.metric("Dose Taken", str(dose_mg) + " mg")
            st.metric("Time Since Overdose", str(time_hours) + " hours")
        with col3:
            st.metric("Dose per kg", str(round(decision['dose_per_kg'], 1)) + " mg/kg")
            st.metric("Staggered Overdose", "Yes" if is_staggered else "No")
        
        # Recommendation
        st.markdown("### 🎯 Recommendation")
        
        if decision['recommendation'] == 'START_NAC':
            st.error("🚨 **START N-ACETYLCYSTEINE (NAC) IMMEDIATELY**")
            st.write("**Reason:** " + decision['reason'])
            st.markdown("""
            **Action Required:**
            - Start NAC protocol immediately
            - Follow standard NAC dosing guidelines
            - Monitor liver function tests
            - Obtain baseline bloods if not already done
            """)
            
        elif decision['recommendation'] == 'WAIT_FOR_BLOODS':
            st.warning("🩸 **OBTAIN BLOOD TESTS**")
            st.write("**Reason:** " + decision['reason'])
            st.markdown("""
            **Action Required:**
            - Paracetamol level (plot on nomogram if < 24 hours)
            - Liver function tests (ALT, AST, Bilirubin)
            - Consider NAC if levels indicate risk
            - Monitor patient clinically
            """)
            
        elif decision['recommendation'] == 'NO_ACTION':
            st.success("✅ **NO IMMEDIATE TREATMENT REQUIRED**")
            st.write("**Reason:** " + decision['reason'])
            st.markdown("""
            **Action Required:**
            - Provide supportive care
            - Advise patient to return if symptoms develop
            - Consider safety netting advice
            - Document assessment clearly
            """)
        
        # Disclaimer
        st.markdown("---")
        st.warning("""
        ⚠️ **IMPORTANT DISCLAIMER:** 
        This is a clinical decision support tool only. Always consider the full clinical context, 
        patient factors, and local guidelines. This tool does not replace clinical judgment and 
        should be used alongside appropriate medical assessment.
        """)

if __name__ == "__main__":
    main()
