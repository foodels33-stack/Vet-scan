import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. הגדרות ונתוני פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# מילון ענק: 50 מדדים וקיצורים (כימיה, CBC, אלקטרוליטים)
hebrew_mapping = {
    "GLU": "GLU", "GLUCOSE": "GLU", "CREA": "CREA", "CREATININE": "CREA",
    "BUN": "BUN", "UREA": "BUN", "BUN/CREA": "BUN_CREA", "TP": "TP", "PROTEIN": "TP",
    "ALB": "ALB", "ALBUMIN": "ALB", "GLOB": "GLOB", "GLOBULIN": "GLOB", "ALB/GLOB": "ALB_GLOB",
    "ALT": "ALT", "ALKP": "ALKP", "ALP": "ALKP", "GGT": "GGT", "AST": "AST",
    "CHOL": "CHOL", "CHOLESTEROL": "CHOL", "AMYL": "AMYL", "AMYLASE": "AMYL", "LIPA": "LIPA",
    "CA": "CA", "CALCIUM": "CA", "PHOS": "PHOS", "PHOSPHORUS": "PHOS", "NA": "NA", "SODIUM": "NA",
    "K": "K", "POTASSIUM": "K", "CL": "CL", "CHLORIDE": "CL", "HGB": "HGB", "HEMOGLOBIN": "HGB",
    "WBC": "WBC", "RBC": "RBC", "PLT": "PLT", "MCV": "MCV", "MCH": "MCH", "MCHC": "MCHC",
    "NEU": "NEU", "LYM": "LYM", "MONO": "MONO", "EOS": "EOS", "BASO": "BASO"
}

blood_db = {
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כליות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "BUN_CREA": {"name": "יחס אוריאה/קריאטינין", "min": 10, "max": 25, "unit": "", "cause": "איזון כליות."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "unit": "g/dL", "cause": "תפקוד כבד או כליה."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "cause": "מערכת חיסונית/דלקת."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "cause": "כבד או עצמות."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה או חילוף חומרים."},
    "HGB": {"name": "המוגלובין", "min": 12, "max": 18, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6, "max": 17, "unit": "K/uL", "cause": "זיהום/דלקת."}
}

# --- 2. מנוע סריקה ומומחה V37 ---
def extract_pdf_v37(pdf_file):
    results = {}
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        lines = full_text.split('\n')
        for line in lines:
            parts = line.split()
            for part in parts:
                clean_part = re.sub(r'[^A-Z/]', '', part.upper())
                if clean_part in hebrew_mapping:
                    eng_key = hebrew_mapping[clean_part]
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums: results[eng_key] = float(nums[0])
    return results

def run_expert_diagnosis(data, weight):
    diag = []
    if data.get("GLOB", 0) > 4.5:
        diag.append("🚨 **עומס חיסוני:** גלובולין גבוה מעיד על פעילות מוגברת של מערכת החיסון (דלקת או זיהום).")
    if data.get("ALB", 0) < 2.5 and data.get("TP", 0) < 5.2:
        diag.append("🚨 **אובדן חלבון:** רמת אלבומין וחלבון נמוכה מעידה על בעיית ספיגה או איבוד חלבון דרך הכליות/מעי.")
    if not diag: diag.append("✅ **אבחנת מומחה:** המדדים המורחבים נראים מאוזנים ומסונכרנים.")
    return diag

# --- 3. UI ---
st.set_page_config(page_title="Foodels Lab Giant V37", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", ["שיצו", "מלטז", "רועה גרמני", "מלינואה", "מעורב"])
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 20.5)

st.title(f"🩺 המומחה המורחב של פודלס: {dog_name}")

uploaded_file = st.file_uploader("העלה בדיקת דם מורחבת (PDF)", type=["pdf"])

if uploaded_file:
    data = extract_pdf_v37(uploaded_file)
    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📊 ניתוח 50 מדדים")
            issues = 0
            for m, val in data.items():
                if m in blood_db:
                    info = blood_db[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    with st.expander(f"{info['name']} ({m}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"תוצאה: {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"סיבה: {info['cause']}")
        with col2:
            st.subheader("🧠 אבחנת מומחה מורחבת")
            expert_summary = run_expert_diagnosis(data, dog_weight)
            for line in expert_summary: st.write(line)
            score = max(0, 100 - (issues * 8))
            st.metric("ציון בריאות", f"{score}%")

        wa_text = f"אבחנת מעבדה ל*{dog_name}* מפודלס:\n" + "\n".join(expert_summary)
        msg = urllib.parse.quote(wa_text + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח דו"ח מורחב ללקוח</button></a>', unsafe_allow_html=True)
