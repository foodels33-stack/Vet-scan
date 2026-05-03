import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. מילון זיהוי עברי/אנגלי מורחב ---
hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP"
}

# --- 2. מאגר גזעים וסיכונים גנטיים מורחב ---
breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt) ואלרגיות עור.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility ואנזימי עיכול."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ובעיות מפרקים בעומס.", "risk_markers": ["CREA", "WBC"], "rec": "תזונה עתירת חלבון איכותי."},
    "פיטבול": {"genetics": "אלרגיות עור ובעיות בבלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון היפו-אלרגני."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון דל קלוריות וסיוע למפרקים."},
    "בולדוג צרפתי": {"genetics": "בעיות נשימה (BOAS) ואלרגיות עור.", "risk_markers": ["WBC", "EOS"], "rec": "חלבון מפורק ומשקל מבוקר."},
    "רועה אוסטרלי": {"genetics": "רגישות MDR1 ובעיות עיניים.", "risk_markers": ["ALT", "ALKP"], "rec": "נוגדי חמצון ותמיכה בכבד."}
}

blood_db_base = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כלייתי, התייבשות או פגיעה בתפקוד הכליות."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד, דלקת כבד או חשיפה לרעלים."},
    "GLU": {"name": "גלוקוז (סוכר)", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת, סטרס חריף או צריכת פחמימות גבוהה."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד או תזונה עתירת חלבון."},
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה (אם נמוך) או התייבשות (אם גבוה)."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/µL", "cause": "זיהום חיידקי או דלקת פעילה."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד/מרה או צמיחת עצם."},
    "PLT": {"name": "טסיות (PLT)", "min": 200, "max": 500, "unit": "K/µL", "cause": "בעיות קרישה או דלקת."}
}

# --- 3. מנוע סריקה מרחבי חכם (Anchor-Value Logic) ---
def extract_data_v18(image):
    d = pytesseract.image_to_data(image, config=r'--oem 3 --psm 6 -l heb+eng', output_type=pytesseract.Output.DICT)
    results = {}
    
    # מיפוי כל המילים והמספרים לפי קואורדינטות
    for i in range(len(d['text'])):
        word = d['text'][i].strip()
        for heb_word, eng_key in hebrew_mapping.items():
            if heb_word in word or (len(word) > 2 and word.upper() in eng_key):
                curr_y = d['top'][i]
                line_nums = []
                # מחפש את כל המספרים באותה שורה
                for j in range(len(d['text'])):
                    if abs(d['top'][j] - curr_y) < 25:
                        num_match = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num_match:
                            line_nums.append(float(num_match.group(1)))
                
                # לוגיקה לבחירת המספר הנכון (התוצאה בדרך כלל בין שם המדד לטווח הנורמה)
                if line_nums:
                    if len(line_nums) >= 1:
                        results[eng_key] = line_nums[0] # לוקח את המספר הראשון אחרי השם
    return results

# --- 4. ממשק המערכת (UI) ---
st.set_page_config(page_title="Foodels AI V18 - The Beast", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.write("**פודלס באר שבע | נחום שריג 33**")

dog_name = st.sidebar.text_input("שם הכלב:", "טוסי")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🚀 פיענוח מדעי מלא עבור {dog_name}")
st.write(f"גזע: **{dog_breed}** | גיל: **{dog_age}** | משקל: **{dog_weight}** ק\"ג")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 נקודות תורפה גנטיות ל{dog_breed}", expanded=True):
        st.write(f"**סיכונים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את טופס הבדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v18(img)
    
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
            st.subheader("ציון בריאות")
            score = max(0, 100 - (issues * 12))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)
            if score < 85: st.warning("מומלץ ייעוץ תזונתי להתאמת מזון תומך.")

        msg = urllib.parse.quote(wa_summary + "\nנחכה לכם בפודלס!")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח דו"ח מלא ללקוח</button></a>', unsafe_allow_html=True)
