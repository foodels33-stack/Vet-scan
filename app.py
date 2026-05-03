import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- V23: מאגר ידע גנטי ומחקרי מורחב ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ובעיות נשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד (Hepatic)."},
    "מלטז": {"genetics": "סיכון גבוה לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary) ובקרה על נתרן."},
    "יורקשייר טרייר": {"genetics": "רגישות להיפוגליקמיה וקריסת קנה נשימה.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות קטנות ותכופות ומזון תומך כבד."},
    "מלטיפו": {"genetics": "נטייה לבעיות מפרקים, אלרגיות מזון ובעיות עיכול.", "risk_markers": ["EOS", "AMYL"], "rec": "מזון היפו-אלרגני ותוספי מפרקים."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS), אלרגיות עור ובעיות עמוד שדרה.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון איכותי מפורק ומשקל מבוקר."},
    "פומרניאן": {"genetics": "בעיות בלוטת התריס, נשירת שיער וקריסת קנה.", "risk_markers": ["CHOL", "WBC"], "rec": "מזון לטיפוח הפרווה ותמיכה חיסונית."},
    "צ'יוואווה": {"genetics": "מחלות לב, היפוגליקמיה ובעיות שיניים.", "risk_markers": ["GLU", "ALT"], "rec": "מזון דנטלי ותזונה שומרת סוכר."},
    "פאג": {"genetics": "סיכון לעודף משקל, בעיות נשימה ודלקות עור.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון מופחת קלוריות (Weight Management)."},
    "דקל (תחש)": {"genetics": "סיכון גבוה לפריצות דיסק (IVDD) ובעיות שיניים.", "risk_markers": ["CREA", "ALKP"], "rec": "שמירה על משקל נמוך ותמיכה במפרקים."},
    "ביגל": {"genetics": "נטייה להשמנה, אפילפסיה ובעיות בלוטת התריס.", "risk_markers": ["CHOL", "ALKP"], "rec": "מזון לניהול משקל ופעילות גופנית."},
    "לברדור/גולדן": {"genetics": "סיכון למפרקי ירך, השמנה וגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Mobility ותפריט דל קלוריות."}
}

blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "cause": "עומס על הכליות או התייבשות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cause": "פגיעה בתאי כבד או רעלים."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", "cause": "סוכרת, סטרס או צריכת פחמימות."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "cause": "בעיות כבד, מרה או צמיחת עצם."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "cause": "נוכחות זיהום או דלקת."},
    "EOS": {"name": "אאוזינופילים", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "cause": "אלרגיה (מזון/סביבה) או טפילים."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה שומנית או בעיה מטבולית."},
    "AMYL": {"name": "עמילאז (לבלב)", "min": 500, "max": 1500, "unit": "U/L", "cause": "דלקת בלבלב או קושי בעיכול."},
    "BUN": {"name": "אוריאה (Urea)", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד או פירוק חלבון גבוה."}
}

def get_adjusted_ranges(age):
    adjusted = {}
    for m, info in blood_db_base.items():
        new_info = info.copy()
        if age < 1.0:
            if m == "ALKP": new_info["max"] = 500
            if m == "GLU": new_info["min"] = 85
        elif age > 7.0:
            if m == "CREA": new_info["max"] = 1.6
        adjusted[m] = new_info
    return adjusted

def extract_data(image):
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    clean_text = re.sub(r'[^a-zA-Z0-9.\s:]', ' ', text)
    results = {}
    for marker in blood_db_base.keys():
        pattern = rf"{marker}.*?(\d+\.?\d*)"
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match: results[marker] = float(match.group(1))
    return results

# --- UI ---
st.set_page_config(page_title="Foodels AI V23", layout="wide")

st.sidebar.title("🧬 פרופיל רפואי")
dog_name = st.sidebar.text_input("שם הכלב:", "באדי")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל (שנים):", 0.1, 25.0, 5.0)

adjusted_db = get_adjusted_ranges(dog_age)

st.title(f"🐾 Foodels Intelligence V23 - דוח {dog_name}")
st.markdown(f"**פודלס באר שבע** | גזע: {dog_breed}")

if dog_breed in breed_intelligence:
    with st.expander(f"🔬 ניתוח גנטי: {dog_breed}", expanded=True):
        st.write(f"**נקודות תורפה:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה צילום בדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data(img)
    if data:
        issues = 0
        whatsapp_msg = f"סיכום בריאות ל*{dog_name}* מפודלס:\n\n"
        col1, col2 = st.columns([2, 1])
        with col1:
            for m, val in data.items():
                info = adjusted_db[m]
                is_issue = val > info["max"] or val < info["min"]
                if is_issue: issues += 1
                color = "red" if is_issue else "green"
                with st.expander(f"{info['name']}: {val}", expanded=is_issue):
                    st.markdown(f"**תוצאה:** :{color}[{val}] (טווח: {info['min']}-{info['max']})")
                    whatsapp_msg += f"📍 {info['name']}: {val} ({'חריגה' if is_issue else 'תקין'})\n"
        with col2:
            score = max(0, 100 - (issues * 15))
            st.metric("מדד בריאות", f"{score}%")
            st.progress(score / 100)

        encoded_msg = urllib.parse.quote(whatsapp_msg + "\nנשמח לעזור לכם בפודלס!")
        st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח סיכום לווטסאפ</button></a>', unsafe_allow_html=True)
