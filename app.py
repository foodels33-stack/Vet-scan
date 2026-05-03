import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- מאגר ידע מדעי: גנטיקה וסיכונים לפי גזע ---
breed_intelligence = {
    "שיצו": {
        "genetics": "נטייה ל-Portosystemic Shunt (בעיית כלי דם בכבד) ודלקות בקרנית.",
        "risk_markers": ["ALT", "ALKP"],
        "recommendation": "מזון דל חלבון וקל לעיכול לתמיכה בכבד."
    },
    "מלטז": {
        "genetics": "נטייה ל-White Dog Shaker Syndrome ומחלות במסתמי הלב (MVD).",
        "risk_markers": ["CREA", "BUN"],
        "recommendation": "מזון דל נתרן ומינרלים מאוזנים למניעת אבנים."
    },
    "יורקשייר טרייר": {
        "genetics": "סיכון גבוה לקריסת קנה נשימה (Tracheal Collapse) ו-Liver Shunts.",
        "risk_markers": ["GLU", "ALT"],
        "recommendation": "שמירה על משקל תקין למניעת עומס נשימתי ומזון תומך כבד."
    },
    "בולדוג צרפתי": {
        "genetics": "תסמונת בראכיצפאלית (נשימה) ובעיות בעמוד השדרה (IVDD).",
        "risk_markers": ["WBC", "EOS"],
        "recommendation": "חלבון היפו-אלרגני למניעת דלקות עור ומשקל מבוקר."
    },
    "מלטיפו": {
        "genetics": "נטייה לבעיות ברכיים (Luxating Patella) ואפילפסיה אידיופטית.",
        "risk_markers": ["AMYL", "GLU"],
        "recommendation": "תוספי גלוקוזאמין למפרקים ומזון דל פחמימות."
    },
    "צ'יוואווה": {
        "genetics": "נטייה למחלות לב (Mitral Valve) והיפוגליקמיה חריפה.",
        "risk_markers": ["GLU", "ALT"],
        "recommendation": "ארוחות קטנות ותכופות לשמירה על רמת סוכר."
    }
}

# בסיס נתונים של מדדים - טווחים בסיסיים
blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "cause": "עומס כלייתי או התייבשות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cause": "פגיעה בתאי כבד או רעלים."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "cause": "בעיות כבד או צמיחת עצם."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "cause": "זיהום או דלקת."},
    "EOS": {"name": "אאוזינופילים (אלרגיה)", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "cause": "אלרגיה או טפילים."},
    "AMYL": {"name": "עמילאז (לבלב)", "min": 500, "max": 1500, "unit": "U/L", "cause": "דלקת בלבלב או קושי בעיכול."}
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

# --- ממשק משתמש (UI) ---
st.set_page_config(page_title="Foodels AI V7 - Scientific Analysis", layout="centered")

st.sidebar.image("https://foodels.co.il/logo.png", width=120) # לוגו פודלס
st.sidebar.header("📊 פרופיל רפואי")
dog_name = st.sidebar.text_input("שם הכלב:", "באדי")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 3.0)

# חישוב טווחים
age_label = "גור" if dog_age < 1 else ("סניור" if dog_age > 7 else "בוגר")
adjusted_db = get_adjusted_ranges(dog_age)

st.title(f"🐾 פיענוח מדעי עבור {dog_name}")
st.write(f"**חנות חיות פודלס - באר שבע** | סטטוס: {age_label} | גזע: {dog_breed}")
st.divider()

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 מחקר גנטי: נקודות תורפה ל{dog_breed}", expanded=True):
        st.write(f"**מידע מדעי:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצה תזונתית מונעת:** {breed_intelligence[dog_breed]['recommendation']}")

uploaded_file = st.file_uploader("העלה את טופס בדיקת הדם", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data(img)
    
    if data:
        st.subheader("نتוצות הבדיקה והצלבה גנטית:")
        whatsapp_summary = f"סיכום מדעי ל*{dog_name}* מפודלס:\n"
        
        for m, val in data.items():
            info = adjusted_db[m]
            is_issue = val > info["max"] or val < info["min"]
            is_genetic_risk = dog_breed in breed_intelligence and m in breed_intelligence[dog_breed]["risk_markers"]
            
            color = "red" if is_issue else "green"
            icon = "🚨" if is_issue else "✅"
            
            with st.expander(f"{info['name']}: {val} {icon}", expanded=is_issue):
                if is_genetic_risk:
                    st.warning(f"⚠️ **תשומת לב:** מדד זה מזוהה כנקודת תורפה גנטית בגזע {dog_breed}.")
                
                st.markdown(f"**תוצאה:** :{color}[{val} {info['unit']}]")
                st.write(f"**טווח תקין ל{age_label}:** {info['min']} - {info['max']}")
                
                if is_issue:
                    st.error(f"הסבר רפואי: {info['cause']}")
                    whatsapp_summary += f"📍 {info['name']}: {val} (חריגה)\n"
                else:
                    whatsapp_summary += f"✅ {info['name']}: {val}\n"

        # כפתור ווטסאפ
        msg = urllib.parse.quote(whatsapp_summary + "\nנשמח להתאים לכם מזון רפואי בחנות!")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; font-weight: bold;">📲 שלח דו"ח מדעי ללקוח</button></a>', unsafe_allow_html=True)
    else:
        st.error("לא נמצאו נתונים לסריקה.")
