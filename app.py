import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. מילון זיהוי ומיפוי מורחב ---
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP"
}

# --- 2. מאגר גזעים מורחב (הגרסה המלאה) ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt) ואלרגיות עור.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility ואנזימי עיכול."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ובעיות מפרקים בעומס גבוה.", "risk_markers": ["CREA", "WBC"], "rec": "תזונה עתירת חלבון איכותי."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון דל קלוריות וסיוע למפרקים."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS) ואלרגיות עור.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."},
    "פיטבול": {"genetics": "אלרגיות עור ובעיות בבלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון היפו-אלרגני."},
    "רועה אוסטרלי": {"genetics": "רגישות לתרופות (MDR1) ובעיות עיניים.", "risk_markers": ["ALT", "ALKP"], "rec": "נוגדי חמצון ותמיכה בכבד."}
}

# --- 3. בסיס נתונים רפואי עם סיבות לחריגה ---
blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי, התייבשות או פגיעה בתפקוד הכליות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד, דלקת כבד או חשיפה לרעלים."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת, סטרס חריף (נפוץ בבדיקות) או צריכת פחמימות גבוהה."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד, תזונה עתירת חלבון או דימום במערכת העיכול."},
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה (אם נמוך) או התייבשות ומחסור בחמצן (אם גבוה)."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "זיהום חיידקי, דלקת פעילה או תגובה חיסונית חריפה."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה, דלקת או איבוד דם חריף."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות בכבד/מרה, צמיחת עצם בגורים או מחלת קושינג."}
}

def extract_data_v16(image):
    # סריקה מקיפה שמוציאה את כל הטקסט מהתמונה
    text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l heb+eng')
    lines = text.split('\n')
    results = {}
    
    for line in lines:
        for heb_word, eng_key in hebrew_mapping.items():
            if heb_word in line or (len(heb_word) > 3 and eng_key in line.upper()):
                # חיפוש מספרים בשורה - לוקח את המספר הראשון שאינו טווח הנורמה
                nums = re.findall(r"(\d+\.?\d*)", line)
                if nums:
                    results[eng_key] = float(nums[0])
    return results

# --- 4. ממשק המערכת (UI) ---
st.set_page_config(page_title="Foodels AI V16 - Iron Logic", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.write("**חנות חיות פודלס - באר שבע**")

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🚀 פיענוח מדעי מלא עבור {dog_name}")
st.write(f"גזע: **{dog_breed}** | גיל: **{dog_age}** | משקל: **{dog_weight}** ק\"ג")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 נקודות תורפה גנטיות ל{dog_breed}", expanded=True):
        st.write(f"**סיכונים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את טופס הבדיקה (image_525647db)", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v16(img)
    
    if data:
        issues = 0
        wa_summary = f"סיכום בדיקה ל*{dog_name}* מפודלס באר שבע:\n"
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("ניתוח מדדים מורחב")
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.markdown(f"**תוצאה:** {val} {info['unit']} (טווח נורמה: {info['min']}-{info['max']})")
                        if is_bad: 
                            st.error(f"⚠️ **סיבה אפשרית:** {info['cause']}")
                            wa_summary += f"📍 {info['name']}: {val} (חריגה)\n"
                        else:
                            wa_summary += f"✅ {info['name']}: {val}\n"

        with col2:
            st.subheader("ציון בריאות כללי")
            score = max(0, 100 - (issues * 12))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)
            if score < 85: st.warning("מומלץ ייעוץ תזונתי להתאמת מזון תומך.")

        msg = urllib.parse.quote(wa_summary + "\nנחכה לכם בפודלס, נחום שריג 33!")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח דו"ח מלא ללקוח</button></a>', unsafe_allow_html=True)
    else:
        st.error("לא זוהו מדדים. וודא שהצילום ישר וברור.")
