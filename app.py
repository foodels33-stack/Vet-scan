import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. מילון משוריין ומורחב (הוספתי עוד קיצורים רפואיים נפוצים) ---
hebrew_mapping = {
    "קריאטינין": "CREA", "CREATININE": "CREA", "אוריאה": "BUN", "UREA": "BUN",
    "גלוקוז": "GLU", "GLUCOSE": "GLU", "סוכר": "GLU", "ALT": "ALT", "GPT": "ALT",
    "ALKP": "ALKP", "ALP": "ALKP", "פוספטאזה": "ALKP", "WBC": "WBC", "לבנות": "WBC",
    "המוגלובין": "HGB", "HGB": "HGB", "טסיות": "PLT", "PLATELETS": "PLT", "PLT": "PLT",
    "כולסטרול": "CHOL", "CHOLESTEROL": "CHOL", "AMYLASE": "AMYL", "עמילאז": "AMYL",
    "ALBUMIN": "ALB", "אלבומין": "ALB", "PROTEIN": "TP", "חלבון": "TP", "TP": "TP"
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "זיהום או דלקת."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה."},
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד או עצם."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה או בעיה מטבולית."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "cause": "דלקת או בעיית ספיגה."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "cause": "בעיות כבד או כליה."},
    "AMYL": {"name": "עמילאז", "min": 500, "max": 1500, "unit": "U/L", "cause": "בעיות לבלב."}
}

# --- 2. מנוע סריקה אבחנתי V27 ---
def extract_data_v27(image):
    # סריקה גולמית של כל הדף
    full_text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l heb+eng')
    lines = full_text.split('\n')
    results = {}
    raw_debug = []
    
    for line in lines:
        if line.strip():
            raw_debug.append(line.strip())
            for key_word, eng_key in hebrew_mapping.items():
                if key_word in line.upper():
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums:
                        # לוקח את המספר האחרון בשורה כתוצאה (מתעלם מהטווחים אם הם בסוגריים בסוף)
                        val = float(nums[-1] if len(nums) > 1 else nums[0])
                        results[eng_key] = val
    return results, raw_debug

# --- 3. UI ---
st.set_page_config(page_title="Foodels Diagnostic V27", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.write("**נחום שריג 33, באר שבע**")

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", ["שיצו", "מלטז", "רועה גרמני", "פיטבול", "מלינואה", "מעורב"])

uploaded_file = st.file_uploader("העלה את הטופס המקורי (image_525647db)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data, debug_log = extract_data_v27(img)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("ניתוח מדדים")
        if data:
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    st.write(f"{'🚨' if is_bad else '✅'} **{info['name']}**: {val} (טווח: {info['min']}-{info['max']})")
        else:
            st.error("לא זוהו מדדים במילון.")

    with col2:
        with st.expander("🔍 לוג סריקה גולמי (למפתחים בלבד)"):
            for log in debug_log:
                st.text(log)

    if data:
        wa_msg = urllib.parse.quote(f"סיכום ל{dog_name} מפודלס באר שבע...")
        st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%;">שלח ווטסאפ</button></a>', unsafe_allow_html=True)
