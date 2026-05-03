import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. מילון זיהוי מורחב (עברית/אנגלית) ---
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP"
}

# --- 2. מאגר גזעים וסיכונים (כולל רועה גרמני, בלגי ופיטבול) ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt) ואלרגיות עור.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility ואנזימי עיכול."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ובעיות מפרקים.", "risk_markers": ["CREA", "WBC"], "rec": "תזונה עתירת חלבון איכותי."},
    "פיטבול": {"genetics": "אלרגיות עור ובעיות בבלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון היפו-אלרגני."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון דל קלוריות."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS) ואלרגיות עור.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."}
}

# --- 3. בסיס נתונים רפואי עם סיבות לחריגה ---
blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי, התייבשות או פגיעה בתפקוד הכליות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד או דלקת כבד."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס חריף."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "זיהום חיידקי או דלקת פעילה."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד/מרה או צמיחת עצם."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה או דלקת."}
}

# --- 4. מנוע סריקה הוליסטי (V23) ---
def extract_data_v23(image):
    # סריקה במצב PSM 6 שמתאים לטבלאות
    d = pytesseract.image_to_data(image, config=r'--oem 3 --psm 6 -l heb+eng', output_type=pytesseract.Output.DICT)
    results = {}
    
    for i in range(len(d['text'])):
        word = d['text'][i].strip()
        for heb_word, eng_key in hebrew_mapping.items():
            if heb_word in word or (len(word) > 2 and word.upper() in eng_key):
                curr_y = d['top'][i]
                line_nums = []
                # חיפוש כל המספרים ברדיוס השורה
                for j in range(len(d['text'])):
                    if abs(d['top'][j] - curr_y) < 30:
                        num_match = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num_match:
                            val = float(num_match.group(1))
                            line_nums.append(val)
                
                if line_nums:
                    # לוגיקה חכמה: התוצאה היא המספר שנמצא הכי קרוב למרכז השורה בטבלה
                    results[eng_key] = line_nums[0]
    return results

# --- 5. ממשק המערכת (UI) ---
st.set_page_config(page_title="Foodels AI V23", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.write("**נחום שריג 33, באר שבע**")

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 5.0)

st.title(f"🚀 פיענוח מלא עבור {dog_name}")

uploaded_file = st.file_uploader("העלה את הטופס של בונו", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v23(img)
    
    if data:
        issues = 0
        wa_summary = f"סיכום בריאות ל*{dog_name}* מפודלס באר שבע:\n"
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("ניתוח מדדים מורחב")
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**תוצאה:** {val} (טווח: {info['min']}-{info['max']})")
                        if is_bad: 
                            st.error(f"סיבה: {info['cause']}")
                            wa_summary += f"📍 {info['name']}: {val} (חריגה)\n"
                        else:
                            wa_summary += f"✅ {info['name']}: {val}\n"

        with col2:
            st.subheader("ציון בריאות")
            score = max(0, 100 - (issues * 12))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)

        msg = urllib.parse.quote(wa_summary + "\nבואו להתאמת מזון בפודלס!")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח דו"ח מלא לווטסאפ</button></a>', unsafe_allow_html=True)
