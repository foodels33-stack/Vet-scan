import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# מילון זיהוי מורחב - סנייפר V11
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "חלבון": "TP", "אלבומין": "ALB", "המוגלובין": "HGB",
    "אדומות": "RBC", "טסיות": "PLT"
}

# נתוני גזעים וסיכונים (מבוסס מחקר)
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ודרכי נשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "יורקשייר טרייר": {"genetics": "רגישות להיפוגליקמיה וקריסת קנה נשימה.", "risk_markers": ["GLU", "ALT"], "rec": "מזון תומך כבד."},
    "מלטיפו": {"genetics": "נטייה לבעיות ברכיים, אלרגיות מזון ובעיות עיכול.", "risk_markers": ["EOS", "AMYL"], "rec": "מזון היפו-אלרגני."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS), אלרגיות עור ובעיות גב.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."},
    "פומרניאן": {"genetics": "בעיות בלוטת התריס, נשירת שיער וקריסת קנה.", "risk_markers": ["CHOL", "WBC"], "rec": "מזון לטיפוח הפרווה."},
    "צ'יוואווה": {"genetics": "מחלות לב (Mitral Valve), היפוגליקמיה ושיניים.", "risk_markers": ["GLU", "ALT"], "rec": "ארוחות תכופות."},
    "פאג": {"genetics": "עודף משקל, בעיות נשימה ודלקות בעור.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Weight Management."},
    "דקל (תחש)": {"genetics": "פריצות דיסק (IVDD) ובעיות שיניים.", "risk_markers": ["CREA", "ALKP"], "rec": "שמירה על משקל נמוך."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון Mobility ודל קלוריות."}
}

blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL"},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L"},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 110, "unit": "mg/dL"},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L"},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL"},
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL"},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL"},
    "PLT": {"name": "טסיות PLT", "min": 200, "max": 500, "unit": "K/µL"}
}

def extract_data_sniper(image):
    # סריקה משופרת heb+eng
    text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6 -l heb+eng')
    lines = text.split('\n')
    results = {}
    
    for line in lines:
        for search_word, eng_key in hebrew_mapping.items():
            if search_word in line:
                # מוציא את כל המספרים מהשורה ולוקח את הראשון שמתאים לערך תוצאה
                nums = re.findall(r"(\d+\.?\d*)", line)
                if nums:
                    # בדרך כלל התוצאה היא המספר הראשון או השני בשורה בטפסים כאלו
                    results[eng_key] = float(nums[0])
    return results

# --- UI המכונה ---
st.set_page_config(page_title="Foodels AI V11 - Sniper Edition", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל:", 0.1, 25.0, 5.0)

st.title(f"🚀 פיענוח Sniper ל{dog_name}")
st.write(f"חנות חיות פודלס | באר שבע | נחום שריג 33")

uploaded_file = st.file_uploader("העלה את הטופס של בונו", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_sniper(img)
    
    if data:
        issues = 0
        col1, col2 = st.columns([2, 1])
        with col1:
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    st.write(f"**{info['name']}**: {val} {'🚨' if is_bad else '✅'}")
        
        with col2:
            score = max(0, 100 - (issues * 12))
            st.metric("ציון בריאות", f"{score}%")
            st.progress(score / 100)
            
        st.success(f"זוהו {len(data)} מדדים בהצלחה!")
    else:
        st.error("לא זוהו מדדים. נסה לצלם מול מקור אור חזק יותר.")
