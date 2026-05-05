import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. נתוני חנות פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP"
}

breed_intelligence = {
    "שיצו": {"genetics": "בעיות כבד (Shunt), אלרגיות עור.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול."},
    "מלטז": {"genetics": "אבנים בדרכי השתן ומחלות לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון Urinary."},
    "רועה גרמני": {"genetics": "דיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ומפרקים.", "risk_markers": ["CREA", "WBC"], "rec": "חלבון איכותי."},
    "פיטבול/אמסטף": {"genetics": "אלרגיות עור ובעיות בלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון על בסיס דגים."},
    "רועה אוסטרלי": {"genetics": "רגישות MDR1 ובעיות עיניים.", "risk_markers": ["ALT", "ALKP"], "rec": "נוגדי חמצון."}
}

# בסיס נתונים מורחב ל-12 מדדים
blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "זיהום או דלקת פעילה."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה או דלקת."},
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד או דלקת."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד או צמיחת עצם."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה עתירת שומן או בעיה מטבולית."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "cause": "דלקת כרונית או בעיות ספיגה."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "cause": "בעיות כבד או כליה."},
    "AMYL": {"name": "עמילאז", "min": 500, "max": 1500, "unit": "U/L", "cause": "בעיות בלבלב או בעיכול."}
}

def extract_data_v26(image):
    full_text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l heb+eng')
    lines = full_text.split('\n')
    results = {}
    for line in lines:
        for heb_word, eng_key in hebrew_mapping.items():
            if heb_word in line or eng_key in line.upper():
                nums = re.findall(r"(\d+\.?\d*)", line)
                if nums:
                    # בטופס של רוקי, התוצאה היא בדרך כלל המספר האחרון בשורה
                    val = float(nums[-1])
                    results[eng_key] = val
    return results

# --- UI ---
st.set_page_config(page_title="Foodels Omega V26", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "רוקי")
dog_breed = st.sidebar.selectbox("גזע:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל:", 0.1, 25.0, 8.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 38.0)

st.title(f"🚀 המכונה המלאה של פודלס: {dog_name}")

if dog_breed in breed_intelligence:
    with st.expander("🧬 דגשים גנטיים והמלצות", expanded=True):
        st.write(f"**סיכונים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את צילום המסך המלא", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v26(img)
    if data:
        issues = 0
        wa_text = f"סיכום בדיקה ל*{dog_name}* מפודלס באר שבע:\n"
        col1, col2 = st.columns([2, 1])
        with col1:
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"תוצאה: {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"סיבה: {info['cause']}")
                        wa_text += f"{'📍' if is_bad else '✅'} {info['name']}: {val}\n"
        with col2:
            score = max(0, 100 - (issues * 8)) # שקלול לפי 12 מדדים
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)
            if score < 85: st.warning("מומלץ ייעוץ תזונתי בחנות.")

        msg = urllib.parse.quote(wa_text + f"\nבואו אלינו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח סיכום מלא ללקוח</button></a>', unsafe_allow_html=True)
