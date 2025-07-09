import streamlit as st
import time

# --- Paracetamol Overdose Decision Logic Class ---
# This class contains all the clinical logic from your provided script.
# It is used by the Streamlit UI to perform calculations and make decisions.
class ParacetamolOverdoseDecision:
    def __init__(self):
        """Initialize the decision algorithm with updated thresholds and constants."""
        # General Overdose Parameters
        self.significant_dose_threshold = 75  # mg/kg
        self.high_risk_dose_threshold = 150  # mg/kg
        self.blood_test_wait_time_hours = 4  # hours
        self.late_presentation_threshold = 24  # hours
        self.paracetamol_detection_threshold = 5  # mg/L
        
        # Liver/Kidney Function Thresholds
        self.inr_threshold = 1.3
        self.alt_upper_limit_normal = 33  # IU/L
        self.creatinine_threshold_absolute = 109 # µmol/L
        self.creatinine_previous_abnormal_threshold = 100 # µmol/L
        self.creatinine_threshold_percentage_increase = 0.10 # 10%

        # NAC Continuation (SNAP Guidance) Thresholds
        self.nac_cont_paracetamol_level = 10 # mg/L
        self.nac_cont_alt_doubled_from_admission_factor = 2
        self.nac_cont_alt_twice_uln_factor = 2

        # Nomogram treatment line
        self.nomogram_data = {
            4: 100, 5: 82, 6: 70, 7: 60, 8: 50, 9: 40, 10: 35, 11: 30,
            12: 25, 13: 20, 14: 18, 15: 15
        }

        # NAC dosing based on weight ranges
        self.nac_dosing = {
            (40, 49): {'weight_range': '40-49 kg', 'dose1_mg': 4600, 'vol1_ml': 23, 'rate1_mlhr': 112, 'dose2_mg': 9000, 'vol2_ml': 45, 'rate2_mlhr': 105},
            (50, 59): {'weight_range': '50-59 kg', 'dose1_mg': 5600, 'vol1_ml': 28, 'rate1_mlhr': 114, 'dose2_mg': 11000, 'vol2_ml': 55, 'rate2_mlhr': 106},
            (60, 69): {'weight_range': '60-69 kg', 'dose1_mg': 6600, 'vol1_ml': 33, 'rate1_mlhr': 117, 'dose2_mg': 13000, 'vol2_ml': 65, 'rate2_mlhr': 107},
            (70, 79): {'weight_range': '70-79 kg', 'dose1_mg': 7600, 'vol1_ml': 38, 'rate1_mlhr': 119, 'dose2_mg': 15000, 'vol2_ml': 75, 'rate2_mlhr': 108},
            (80, 89): {'weight_range': '80-89 kg', 'dose1_mg': 8600, 'vol1_ml': 43, 'rate1_mlhr': 122, 'dose2_mg': 17000, 'vol2_ml': 85, 'rate2_mlhr': 109},
            (90, 99): {'weight_range': '90-99 kg', 'dose1_mg': 9600, 'vol1_ml': 48, 'rate1_mlhr': 124, 'dose2_mg': 19000, 'vol2_ml': 95, 'rate2_mlhr': 110},
            (100, 109): {'weight_range': '100-109 kg', 'dose1_mg': 10600, 'vol1_ml': 53, 'rate1_mlhr': 127, 'dose2_mg': 21000, 'vol2_ml': 105, 'rate2_mlhr': 111},
            (110, 999): {'weight_range': '>109 kg', 'dose1_mg': 11000, 'vol1_ml': 55, 'rate1_mlhr': 128, 'dose2_mg': 22000, 'vol2_ml': 110, 'rate2_mlhr': 111}
        }

    def calculate_dose_per_kg(self, dose_mg, weight):
        if weight > 0:
            return dose_mg / weight
        return 0

    def get_paracetamol_treatment_threshold(self, hours):
        if hours < 4 or hours > 15:
            return None
        if hours in self.nomogram_data:
            return self.nomogram_data[hours]
        else:
            hour_floor = int(hours)
            hour_ceil = hour_floor + 1
            if hour_floor in self.nomogram_data and hour_ceil in self.nomogram_data:
                threshold_floor = self.nomogram_data[hour_floor]
                threshold_ceil = self.nomogram_data[hour_ceil]
                fraction = hours - hour_floor
                return round(threshold_floor + fraction * (threshold_ceil - threshold_floor), 1)
            return None

    def get_nac_dosing(self, weight):
        for (min_weight, max_weight), dosing in self.nac_dosing.items():
            if min_weight <= weight <= max_weight:
                return dosing
        return self.nac_dosing[(110, 999)]

    def is_significant_dose_self_harm(self, patient_data):
        if not patient_data['is_dose_reliable']:
            return True
        dose_per_kg = self.calculate_dose_per_kg(patient_data['dose_mg'], patient_data['weight'])
        return dose_per_kg >= self.significant_dose_threshold

    def make_initial_decision(self, patient_data):
        dose_per_kg = self.calculate_dose_per_kg(patient_data['dose_mg'], patient_data['weight'])
        patient_data['dose_per_kg'] = dose_per_kg
        
        if patient_data['is_self_harm']:
            return self._handle_self_harm_overdose(patient_data, dose_per_kg)
        else:
            return self._handle_therapeutic_excess(patient_data, dose_per_kg)

    def _handle_self_harm_overdose(self, patient_data, dose_per_kg):
        time_hours = patient_data['time_hours']
        if not self.is_significant_dose_self_harm(patient_data):
            return {'recommendation': 'DELAY_BLOODS_SELF_HARM', 'reason': 'Self-harm context - despite dose being below significant threshold, bloods required at 4 hours post ingestion.', 'blood_tests_needed': True, 'blood_delay_hours': self.blood_test_wait_time_hours}
        if time_hours > self.late_presentation_threshold:
            return {'recommendation': 'LATE_PRESENTATION', 'reason': 'Late presentation (>24 hours). Take bloods immediately and assess for clinical signs.', 'blood_tests_needed': True, 'clinical_signs_needed': True}
        elif patient_data['is_staggered']:
            return {'recommendation': 'START_NAC_DELAY_BLOODS', 'reason': 'Self-harm: Staggered overdose or timing unclear - start NAC immediately, take bloods at 4 hours.', 'blood_tests_needed': True, 'blood_delay_hours': 4}
        else:
            if dose_per_kg >= self.high_risk_dose_threshold and time_hours >= 7:
                return {'recommendation': 'START_NAC_DELAY_BLOODS', 'reason': f'Self-harm: Acute overdose >= {self.high_risk_dose_threshold} mg/kg and >=7 hours post ingestion - start NAC immediately.', 'blood_tests_needed': True, 'blood_delay_hours': 4}
            elif time_hours < self.blood_test_wait_time_hours:
                return {'recommendation': 'DELAY_BLOODS_SELF_HARM', 'reason': f'Self-harm: <{self.blood_test_wait_time_hours} hours post ingestion - delay bloods until {self.blood_test_wait_time_hours} hours.', 'blood_tests_needed': True, 'blood_delay_hours': self.blood_test_wait_time_hours}
            elif time_hours >= self.blood_test_wait_time_hours:
                return {'recommendation': 'TAKE_BLOODS_DECIDE', 'reason': 'Self-harm: >=4 hours post ingestion - take bloods to determine NAC need.', 'blood_tests_needed': True}
        return {'recommendation': 'REVIEW_CASE', 'reason': 'Unhandled self-harm scenario.'}

    def _handle_therapeutic_excess(self, patient_data, dose_per_kg):
        licensed_dose_24hr = 4000
        if patient_data['is_symptomatic']:
            return {'recommendation': 'REFER_HOSPITAL_SYMPTOMATIC', 'reason': 'Patient is symptomatic. Refer to hospital for assessment. Consider NAC if clinical features of hepatic injury.', 'blood_tests_needed': True}
        if (patient_data['dose_mg'] > licensed_dose_24hr) and (dose_per_kg >= self.significant_dose_threshold):
            return {'recommendation': 'REFER_HOSPITAL_HIGH_DOSE_EXCESS', 'reason': f"Ingested > licensed dose AND >= {self.significant_dose_threshold} mg/kg in 24 hours. Check bloods at least 4 hours after last ingestion.", 'blood_tests_needed': True, 'blood_delay_hours': 4}
        if (patient_data['dose_mg'] > licensed_dose_24hr) and (dose_per_kg < self.significant_dose_threshold):
            return {'recommendation': 'CONSIDER_BLOODS_LOW_RISK_EXCESS', 'reason': f"Ingested > licensed dose but < {self.significant_dose_threshold} mg/kg/24 hours. Risk is small, but blood tests may be considered.", 'blood_tests_needed': True}
        if (patient_data['dose_mg'] <= licensed_dose_24hr) and (dose_per_kg < self.significant_dose_threshold):
            return {'recommendation': 'NO_ACTION_THERAPEUTIC', 'reason': 'Dose consistently less than licensed dose and < 75 mg/kg. No further assessment needed.', 'blood_tests_needed': False}
        return {'recommendation': 'REVIEW_CASE', 'reason': 'Unhandled therapeutic excess scenario.'}

    def assess_nac_indication(self, patient_data, blood_results, clinical_signs={}):
        time_hours = patient_data['time_hours']
        paracetamol_level = blood_results['paracetamol_level']
        inr = blood_results['inr']
        alt = blood_results['alt']

        if clinical_signs.get('has_jaundice') or clinical_signs.get('has_liver_tenderness'):
             return True, "NAC is indicated due to clinical signs of liver injury (jaundice or tenderness)."

        if inr > self.inr_threshold or alt > self.alt_upper_limit_normal:
            return True, f"NAC is indicated due to abnormal liver function (INR > {self.inr_threshold} or ALT > {self.alt_upper_limit_normal} IU/L)."
        
        if patient_data['is_self_harm']:
            if patient_data['is_staggered']:
                if paracetamol_level > self.paracetamol_detection_threshold:
                    return True, f"NAC is indicated for staggered ingestion with detectable paracetamol (>{self.paracetamol_detection_threshold} mg/L)."
            else:
                if 4 <= time_hours <= 15:
                    treatment_threshold = self.get_paracetamol_treatment_threshold(time_hours)
                    if treatment_threshold and paracetamol_level >= treatment_threshold:
                        return True, f"NAC is indicated as paracetamol level ({paracetamol_level} mg/L) is on or above the treatment line ({treatment_threshold} mg/L)."
                elif time_hours > 15:
                    if paracetamol_level > self.paracetamol_detection_threshold:
                        return True, f"NAC is indicated for ingestion >15 hours ago with detectable paracetamol (>{self.paracetamol_detection_threshold} mg/L)."
        
        if not patient_data['is_self_harm']:
             if paracetamol_level >= self.nac_cont_paracetamol_level:
                 return True, f"NAC is indicated for therapeutic excess with paracetamol level >= {self.nac_cont_paracetamol_level} mg/L."
        
        return False, "No indication for NAC based on current blood results and clinical context."

    def assess_nac_continuation(self, reassessment_bloods, admission_bloods):
        if not admission_bloods:
            return False, "Error: Admission blood results not available for comparison."
        reasons = []
        continue_nac = False
        if reassessment_bloods['paracetamol_level'] >= self.nac_cont_paracetamol_level:
            reasons.append(f"Paracetamol level is >= {self.nac_cont_paracetamol_level} mg/L")
            continue_nac = True
        if reassessment_bloods['alt'] >= (admission_bloods['alt'] * self.nac_cont_alt_doubled_from_admission_factor):
            reasons.append("ALT has doubled (or more) from the admission value")
            continue_nac = True
        if reassessment_bloods['alt'] > (self.alt_upper_limit_normal * self.nac_cont_alt_twice_uln_factor):
            reasons.append(f"ALT is more than twice the upper limit of normal (> {self.alt_upper_limit_normal * 2} IU/L)")
            continue_nac = True
        if reassessment_bloods['inr'] > admission_bloods['inr']:
            reasons.append("INR has increased from the admission value")
            continue_nac = True
        if continue_nac:
            return True, "Continue NAC. Reason(s): " + "; ".join(reasons) + "."
        else:
            return False, "Criteria for NAC continuation not met. Stop NAC and recheck bloods in 4-6 hours."

# --- Streamlit UI Application ---

# Initialize the logic class
decision_tool = ParacetamolOverdoseDecision()

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'patient_data'
    st.session_state.patient_data = {}
    st.session_state.initial_decision = {}
    st.session_state.admission_bloods = None
    st.session_state.clinical_signs = {}
    st.session_state.reassessment_bloods = None

st.set_page_config(layout="wide", page_title="Paracetamol Overdose Decision Tool")
st.title("Paracetamol Overdose Decision Tool")

# --- Function to reset the app ---
def reset_app():
    st.session_state.step = 'patient_data'
    st.session_state.patient_data = {}
    st.session_state.initial_decision = {}
    st.session_state.admission_bloods = None
    st.session_state.clinical_signs = {}
    st.session_state.reassessment_bloods = None

# --- Function to display NAC protocol ---
def display_nac_protocol(weight, bag_type="initial"):
    dosing = decision_tool.get_nac_dosing(weight)
    st.subheader("N-ACETYLCYSTEINE (NAC) DOSING PROTOCOL")
    st.write(f"**Patient weight:** {weight} kg ({dosing['weight_range']})")
    
    with st.expander(f"View {bag_type.capitalize()} Infusion Protocol", expanded=True):
        if bag_type == "initial":
            st.markdown("##### FIRST INFUSION (Run over 2 hours)")
            st.json({'NAC dose (mg)': dosing['dose1_mg'], 'NAC volume (ml)': dosing['vol1_ml'], 'Add to': '200 ml of 5% glucose', 'Total volume (ml)': 200 + dosing['vol1_ml'], 'Infusion rate (ml/hr)': dosing['rate1_mlhr']})
            st.markdown("##### SECOND INFUSION (Run over 10 hours)")
            st.json({'NAC dose (mg)': dosing['dose2_mg'], 'NAC volume (ml)': dosing['vol2_ml'], 'Add to': '1000 ml of 5% glucose', 'Total volume (ml)': 1000 + dosing['vol2_ml'], 'Infusion rate (ml/hr)': dosing['rate2_mlhr']})
            st.info("At the end of the 12-hour infusion, re-assess with blood tests.")
        elif bag_type == "continuation":
            st.markdown("##### CONTINUATION INFUSION (Run over 10 hours)")
            st.json({'NAC dose (mg)': dosing['dose2_mg'], 'NAC volume (ml)': dosing['vol2_ml'], 'Add to': '1000 ml of 5% glucose', 'Total volume (ml)': 1000 + dosing['vol2_ml'], 'Infusion rate (ml/hr)': dosing['rate2_mlhr']})
            st.info("At the end of this 10-hour bag, re-assess with blood tests.")

# --- Step 1: Patient Data Input ---
if st.session_state.step == 'patient_data':
    st.header("Step 1: Patient Information")
    with st.form(key='patient_form'):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Patient Age (years)", min_value=0, step=1)
            dose_mg = st.number_input("Paracetamol Dose Taken (mg)", min_value=0)
            is_self_harm = st.radio("Overdose Context", ('Self-Harm', 'Therapeutic Excess')) == 'Self-Harm'
        with col2:
            weight = st.number_input("Patient Weight (kg)", min_value=0.0, format="%.1f")
            time_hours = st.number_input("Time Since Overdose (hours)", min_value=0.0, format="%.1f")
        
        if is_self_harm:
            st.subheader("Self-Harm Details")
            col3, col4 = st.columns(2)
            with col3:
                is_staggered = st.checkbox("Staggered overdose or timing unclear?")
            with col4:
                is_dose_reliable = st.checkbox("Is the reported dose reliable?", value=True)
            is_symptomatic = False # Not relevant for this path
        else:
            st.subheader("Therapeutic Excess Details")
            is_symptomatic = st.checkbox("Is the patient symptomatic (nausea, vomiting, abdominal pain)?")
            is_staggered = False
            is_dose_reliable = True

        submit_button = st.form_submit_button(label='Analyze Initial Risk')

        if submit_button:
            if age < 18:
                st.error("This tool is for patients aged 18 years and above only.")
            elif weight <= 0 or dose_mg <= 0:
                st.error("Weight and Dose must be positive values.")
            else:
                st.session_state.patient_data = {
                    'age': age, 'weight': weight, 'dose_mg': dose_mg, 'time_hours': time_hours,
                    'is_self_harm': is_self_harm, 'is_staggered': is_staggered,
                    'is_dose_reliable': is_dose_reliable, 'is_symptomatic': is_symptomatic
                }
                st.session_state.initial_decision = decision_tool.make_initial_decision(st.session_state.patient_data)
                st.session_state.step = 'initial_recommendation'
                st.experimental_rerun()

# --- Step 2: Initial Recommendation ---
if st.session_state.step == 'initial_recommendation':
    st.header("Step 2: Initial Recommendation")
    decision = st.session_state.initial_decision
    st.info(f"**Outcome:** {decision['recommendation'].replace('_', ' ')}")
    st.warning(f"**Reason:** {decision['reason']}")

    if 'START_NAC' in decision['recommendation']:
        display_nac_protocol(st.session_state.patient_data['weight'], bag_type="initial")

    if decision.get('blood_tests_needed'):
        if st.button('Proceed to Enter Blood Results'):
            st.session_state.step = 'blood_results'
            st.experimental_rerun()
    
    st.button("Start Over", on_click=reset_app)

# --- Step 3: Blood Results Input ---
if st.session_state.step == 'blood_results':
    st.header("Step 3: Enter Blood Results")
    with st.form(key='blood_form'):
        st.subheader("Admission Bloods")
        if st.session_state.initial_decision.get('clinical_signs_needed'):
            st.write("Please perform a clinical assessment for late presentation.")
            has_jaundice = st.checkbox("Is jaundice present?")
            has_liver_tenderness = st.checkbox("Is liver tenderness present?")
            st.session_state.clinical_signs = {'has_jaundice': has_jaundice, 'has_liver_tenderness': has_liver_tenderness}
        
        col1, col2 = st.columns(2)
        with col1:
            paracetamol_level = st.number_input("Plasma Paracetamol (mg/L)", min_value=0.0, format="%.1f")
            alt = st.number_input("ALT (IU/L)", min_value=0)
        with col2:
            inr = st.number_input("INR", min_value=0.0, format="%.1f")
            creatinine_current = st.number_input("Current Creatinine (µmol/L)", min_value=0)

        submit_bloods = st.form_submit_button("Analyze Bloods")

        if submit_bloods:
            st.session_state.admission_bloods = {
                'paracetamol_level': paracetamol_level, 'inr': inr, 'alt': alt,
                'creatinine_current': creatinine_current
            }
            st.session_state.step = 'final_recommendation'
            st.experimental_rerun()

    st.button("Start Over", on_click=reset_app)

# --- Step 4: Final Recommendation (Post-Bloods) ---
if st.session_state.step == 'final_recommendation':
    st.header("Step 4: Final Recommendation (Post-Admission Bloods)")
    nac_already_started = 'START_NAC' in st.session_state.initial_decision['recommendation']
    nac_is_indicated, reason = decision_tool.assess_nac_indication(st.session_state.patient_data, st.session_state.admission_bloods, st.session_state.clinical_signs)
    
    if nac_is_indicated:
        if nac_already_started:
            st.success("Action: CONTINUE N-acetylcysteine (NAC) infusion.")
        else:
            st.success("Action: START N-acetylcysteine (NAC) immediately.")
            display_nac_protocol(st.session_state.patient_data['weight'], bag_type="initial")
        st.info(f"**Reason:** {reason}")
        if st.button("Proceed to 12-Hour Re-assessment"):
            st.session_state.step = 'reassessment'
            st.experimental_rerun()
    else:
        if nac_already_started:
            st.error("Action: STOP N-acetylcysteine (NAC) infusion.")
        else:
            st.error("Action: DO NOT start N-acetylcysteine (NAC).")
        st.warning(f"**Reason:** {reason}")

    st.button("Start Over", on_click=reset_app)

# --- Step 5: 12-Hour Re-assessment ---
if st.session_state.step == 'reassessment':
    st.header("Step 5: 12-Hour Re-assessment")
    st.info("Enter blood results taken after the initial 12-hour NAC infusion.")
    with st.form(key='reassessment_form'):
        col1, col2 = st.columns(2)
        with col1:
            paracetamol_level = st.number_input("Re-assessment Paracetamol (mg/L)", min_value=0.0, format="%.1f")
            alt = st.number_input("Re-assessment ALT (IU/L)", min_value=0)
        with col2:
            inr = st.number_input("Re-assessment INR", min_value=0.0, format="%.1f")
            creatinine_current = st.number_input("Re-assessment Creatinine (µmol/L)", min_value=0)
        
        submit_reassessment = st.form_submit_button("Analyze Re-assessment Bloods")

        if submit_reassessment:
            reassessment_bloods = {
                'paracetamol_level': paracetamol_level, 'inr': inr, 'alt': alt,
                'creatinine_current': creatinine_current
            }
            continue_nac, reason = decision_tool.assess_nac_continuation(reassessment_bloods, st.session_state.admission_bloods)
            
            if continue_nac:
                st.success("Action: CONTINUE NAC with a further 10-hour infusion.")
                st.info(f"**Reason:** {reason}")
                display_nac_protocol(st.session_state.patient_data['weight'], bag_type="continuation")
            else:
                st.error("Action: STOP N-acetylcysteine (NAC) infusion.")
                st.warning(f"**Reason:** {reason}")
                st.info("Consider re-checking bloods in 4-6 hours if clinically concerned.")
            
            st.session_state.step = 'complete' # End of this path
            st.experimental_rerun()
    
    st.button("Start Over", on_click=reset_app)

if st.session_state.step == 'complete':
    st.header("Assessment Complete")
    st.button("Start New Assessment", on_click=reset_app)

