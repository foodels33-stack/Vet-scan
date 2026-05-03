import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. מילון תרגום וזיהוי (עברית/אנגלית) ---
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "חלבון": "TP", "אלבומין": "ALB", "המוגלובין": "HGB",
    "אדומות": "RBC", "טסיות": "PLT"
}

# --- 2. מאגר ידע גנטי מדעי (פודלס Elite) ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ודרכי נשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "יורקשייר טרייר": {"genetics": "רגישות להיפוגליקמיה וקריסת קנה נשימה.", "risk_markers": ["GLU", "ALT"], "rec": "מזון תומך כבד."},
    "מלטיפו": {"genetics": "נטייה לבעיות ברכיים, אלרגיות מזון ובעיות עיכול.", "risk_markers": ["EOS", "AMYL"], "rec": "מזון היפו-אלרגני."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS), אלרגיות עור ובעיות גב.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."},
    "פומרניאן": {"genetics": "בעיות בלוטת התריס, נשירת שיער וקריסת קנה.", "risk_markers": ["CHOL", "WBC"], "rec": "מזון לטיפוח הפרווה."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Mobility ודל קלוריות."}
}

# --- 3. בסיס נתונים רפואי ---
blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "BUN": {"name": "אוריאה (Urea)", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות או פירוק חלבון."},
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "דלקת או זיהום."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד/מרה."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה."}
}

def get_adjusted_ranges(age):
    adj = {m: info.copy() for m, info in blood_db_base.items()}
    if age < 1.0:
        if "ALKP" in adj: adj["ALKP"]["max"] = 500
    elif age > 7.0:
        if "CREA" in adj: adj["CREA"]["max"] = 1.6
    return adj

def extract_data_omni(image):
    text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l heb+eng')
    lines = text.split('\n')
    results = {}
    for line in lines:
        for search_word, eng_key in hebrew_mapping.items():
            if search_word in line:
                # מוצא את כל המספרים בשורה ומנקה סימנים מיותרים
                nums = re.findall(r"(\d+\.?\d*)", line)
                if nums:
                    # בטופס של בונו, המספר הראשון אחרי השם הוא בדרך כלל התוצאה
                    results[eng_key] = float(nums[0])
    return results

# --- 4. ממשק המערכת (UI) ---
st.set_page_config(page_title="Foodels Omni-Machine V12", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל:", 0.1, 25.0, 5.0)

adj_db = get_adjusted_ranges(dog_age)
age_cat = "גור" if dog_age < 1 else ("סניור" if dog_age > 7 else "בוגר")

st.title(f"🚀 Omni-Machine: פיענוח חכם עבור {dog_name}")
st.write(f"**פודלס באר שבע** | {age_cat} | {dog_breed}")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 דגשים גנטיים ל{dog_breed}", expanded=True):
        st.write(breed_intelligence[dog_breed]['genetics'])
        st.info(f"💡 המלצה: {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את הטופס של בונו", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_omni(img)
    
    if data:
        issues = 0
        wa_text = f"סיכום בריאות ל*{dog_name}* מפודלס:\n"
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("תוצאות סריקה:")
            for m, val in data.items():
                if m in adj_db:
                    info = adj_db[m]
                    is_bad = val > info["max"] or val < info["min"]
                    is_genetic = dog_breed in breed_intelligence and m in breed_intelligence[dog_breed]["risk_markers"]
                    if is_bad: issues += 1
                    
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"סיבה: {info['cause']}")
                        if is_genetic: st.warning("⚠️ מדד זה קריטי לגזע זה!")
                        wa_text += f"{'📍' if is_bad else '✅'} {info['name']}: {val}\n"

        with col2:
            st.subheader("ציון בריאות")
            score = max(0, 100 - (issues * 12))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)

        encoded_wa = urllib.parse.quote(wa_text + "\nבואו להתאמת מזון בפודלס!")
        st.markdown(f'<a href="https://wa.me/?text={encoded_wa}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח סיכום מלא ללקוח</button></a>', unsafe_allow_html=True)
