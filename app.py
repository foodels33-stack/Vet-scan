import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- מאגר ידע גנטי מדעי מורחב ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ובעיות בדרכי הנשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן (Struvite) ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "יורקשייר טרייר": {"genetics": "רגישות גבוהה להיפוגליקמיה וקריסת קנה נשימה.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות קטנות ומזון תומך כבד."},
    "מלטיפו": {"genetics": "נטייה לבעיות ברכיים, אלרגיות מזון ובעיות עיכול.", "risk_markers": ["EOS", "AMYL"], "rec": "מזון היפו-אלרגני וסיוע למפרקים."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה חסימתיות (BOAS), אלרגיות עור ועיוותי חוליות.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון איכותי מפורק ומשקל מבוקר."},
    "פומרניאן": {"genetics": "בעיות בלוטת התריס, נשירת שיער (Alopecia X) וקריסת קנה.", "risk_markers": ["CHOL", "WBC"], "rec": "מזון לטיפוח הפרווה ותמיכה חיסונית."},
    "צ'יוואווה": {"genetics": "מחלות לב (Mitral Valve), היפוגליקמיה ובעיות שיניים.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות תכופות ותמיכה דנטלית."},
    "פאג": {"genetics": "סיכון לעודף משקל, בעיות נשימה ודלקות בעור הקפלים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון מופחת קלוריות (Weight Management)."},
    "דקל (תחש)": {"genetics": "סיכון גבוה לפריצות דיסק (IVDD) ובעיות שיניים.", "risk_markers": ["CREA", "ALKP"], "rec": "שמירה על משקל נמוך ותמיכה במפרקים."},
    "ביגל": {"genetics": "נטייה להשמנה, אפילפסיה ובעיות בלוטת התריס.", "risk_markers": ["CHOL", "ALKP"], "rec": "מזון לניהול משקל ופעילות גופנית."},
    "לברדור/גולדן": {"genetics": "סיכון למפרקי ירך, השמנה וגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Mobility ותפריט דל קלוריות."}
}

blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "cause": "עומס על הכליות או התייבשות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cause": "פגיעה בתאי כבד או חשיפה לרעלים."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", "cause": "סוכרת, סטרס חריף או צריכת פחמימות."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "cause": "בעיות בכבד, בדרכי המרה או גדילת עצם."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "cause": "נוכחות זיהום, דלקת או תגובה חיסונית."},
    "EOS": {"name": "אאוזינופילים", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "cause": "אלרגיה (מזון/סביבה) או טפילים."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה שומנית מדי או בעיה מטבולית."},
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

# --- UI Layout ---
st.set_page_config(page_title="Foodels AI V9 - The Machine", layout="wide")

st.sidebar.title("🐾 פרופיל רפואי")
dog_name = st.sidebar.text_input("שם הכלב:", "באדי")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל (שנים):", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 8.0)

age_cat = "גור" if dog_age < 1 else ("סניור" if dog_age > 7 else "בוגר")
adjusted_db = get_adjusted_ranges(dog_age)

st.title(f"🐾 Foodels Lab - פיענוח מדעי: {dog_name}")
st.markdown(f"**נחום שריג 33, באר שבע** | סטטוס: {age_cat} | גזע: {dog_breed}")

if dog_breed in breed_intelligence:
    with st.expander(f"🔬 נקודות תורפה ל{dog_breed}", expanded=True):
        st.write(f"**מידע מדעי:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה צילום בדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data(img)
    
    if data:
        issues_count = 0
        whatsapp_msg = f"סיכום בריאות ל*{dog_name}* מפודלס באר שבע:\n\n"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("ניתוח מדדים:")
            for m, val in data.items():
                info = adjusted_db[m]
                is_issue = val > info["max"] or val < info["min"]
                is_genetic = dog_breed in breed_intelligence and m in breed_intelligence[dog_breed]["risk_markers"]
                
                if is_issue: issues_count += 1
                color = "red" if is_issue else "green"
                icon = "🚨" if is_issue else "✅"
                
                with st.expander(f"{info['name']}: {val} {icon}", expanded=is_issue):
                    if is_genetic: st.warning("⚠️ מדד זה קריטי במיוחד לגזע זה!")
                    st.markdown(f"**תוצאה:** :{color}[{val} {info['unit']}] (טווח: {info['min']}-{info['max']})")
                    if is_issue: 
                        st.error(f"סיבה אפשרית: {info['cause']}")
                        whatsapp_msg += f"📍 {info['name']}: {val} (חריגה)\n"
                    else:
                        whatsapp_msg += f"✅ {info['name']}: {val}\n"

        with col2:
            st.subheader("מדד בריאות")
            health_score = max(0, 100 - (issues_count * 15))
            st.metric("Health Score", f"{health_score}%")
            st.progress(health_score / 100)
            if health_score < 80: st.warning("נדרשת התאמת מזון רפואי.")
            else: st.success("מצב תקין!")

        encoded_msg = urllib.parse.quote(whatsapp_msg + "\nנשמח להתאים לכם מזון רפואי בחנות!")
        st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer;">📲 שלח סיכום מכונה ללקוח</button></a>', unsafe_allow_html=True)
