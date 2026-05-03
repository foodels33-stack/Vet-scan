import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- מפת תרגום וזיהוי (עברית/אנגלית) ---
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "חלבון": "TP", "ALB": "ALB", "אלבומין": "ALB"
}

# --- מאגר ידע גנטי מדעי ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ודרכי נשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן (Struvite) ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "יורקשייר טרייר": {"genetics": "רגישות להיפוגליקמיה וקריסת קנה נשימה.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות קטנות ומזון תומך כבד."},
    "מלטיפו": {"genetics": "נטייה לבעיות ברכיים, אלרגיות מזון ובעיות עיכול.", "risk_markers": ["EOS", "AMYL"], "rec": "מזון היפו-אלרגני."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS), אלרגיות עור ובעיות גב.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."},
    "פומרניאן": {"genetics": "בעיות בלוטת התריס, נשירת שיער וקריסת קנה.", "risk_markers": ["CHOL", "WBC"], "rec": "מזון לטיפוח הפרווה."},
    "צ'יוואווה": {"genetics": "מחלות לב (Mitral Valve), היפוגליקמיה ובעיות שיניים.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות תכופות."},
    "פאג": {"genetics": "עודף משקל, בעיות נשימה ודלקות בעור הקפלים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Weight Management."},
    "דקל (תחש)": {"genetics": "פריצות דיסק (IVDD) ובעיות שיניים.", "risk_markers": ["CREA", "ALKP"], "rec": "שמירה על משקל נמוך."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Mobility ודל קלוריות."}
}

blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "cause": "עומס על הכליות או התייבשות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cause": "פגיעה בתאי כבד או רעלים."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", "cause": "סוכרת, סטרס או תזונה פחמימתית."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "cause": "בעיות כבד או צמיחת עצם."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "cause": "זיהום או דלקת."},
    "EOS": {"name": "אאוזינופילים", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "cause": "אלרגיה או טפילים."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה שומנית או בעיה מטבולית."},
    "AMYL": {"name": "עמילאז (לבלב)", "min": 500, "max": 1500, "unit": "U/L", "cause": "דלקת בלבלב או קושי בעיכול."}
}

def get_adjusted_ranges(age):
    adj = {m: info.copy() for m, info in blood_db_base.items()}
    if age < 1.0:
        if "ALKP" in adj: adj["ALKP"]["max"] = 500
        if "GLU" in adj: adj["GLU"]["min"] = 85
    elif age > 7.0:
        if "CREA" in adj: adj["CREA"]["max"] = 1.6
    return adj

def extract_data_final(image):
    # שימוש ב-heb ו-eng יחד לסריקת הטופס ששלחת
    config = r'--oem 3 --psm 6 -l heb+eng'
    text = pytesseract.image_to_string(image, config=config)
    results = {}
    
    # חיפוש לפי מפת המילים
    for search_word, eng_key in hebrew_mapping.items():
        pattern = rf"{search_word}.*?(\d+\.?\d*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[eng_key] = float(match.group(1))
    return results

# --- ממשק המערכת ---
st.set_page_config(page_title="Foodels AI Machine - Final V10", layout="wide")

st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.write("נחום שריג 33, באר שבע")
dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("בחר גזע:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל (שנים):", 0.1, 25.0, 5.0)

adj_db = get_adjusted_ranges(dog_age)
age_status = "גור" if dog_age < 1 else ("סניור" if dog_age > 7 else "בוגר")

st.title(f"🚀 מכונת הפיענוח של פודלס: {dog_name}")
st.write(f"סטטוס: **{age_status}** | גזע: **{dog_breed}**")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 מחקר גנטי ל{dog_breed}", expanded=True):
        st.write(f"**דגשים מדעיים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת מניעה:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את הטופס לסריקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_final(img)
    
    if data:
        issues = 0
        wa_text = f"סיכום בריאות ל*{dog_name}* מפודלס:\n"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            for m, val in data.items():
                info = adj_db[m]
                is_bad = val > info["max"] or val < info["min"]
                is_genetic = dog_breed in breed_intelligence and m in breed_intelligence[dog_breed]["risk_markers"]
                if is_bad: issues += 1
                
                with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                    if is_genetic: st.warning("⚠️ זהו מדד קריטי לגזע זה!")
                    st.markdown(f"**תוצאה:** :{'red' if is_bad else 'green'}[{val} {info['unit']}]")
                    if is_bad: 
                        st.write(f"**סיבה:** {info['cause']}")
                        wa_text += f"📍 {info['name']}: {val} (חריגה)\n"
                    else: wa_text += f"✅ {info['name']}: {val}\n"

        with col2:
            st.subheader("Health Score")
            score = max(0, 100 - (issues * 15))
            st.metric("ציון בריאות", f"{score}%")
            st.progress(score / 100)
            if score < 80: st.error("מומלץ ייעוץ תזונתי דחוף.")

        encoded_wa = urllib.parse.quote(wa_text + "\nבואו להתאים מזון בפודלס!")
        st.markdown(f'<a href="https://wa.me/?text={encoded_wa}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 20px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer;">📲 שלח דוח מכונה ללקוח</button></a>', unsafe_allow_html=True)
    else:
        st.error("לא זוהו מדדים. וודא שהצילום ברור.")
