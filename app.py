import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. הגדרות ונתוני פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# מילון מיפוי וקיצורים (50 מדדים)
hebrew_mapping = {
    "GLU": "GLU", "CREA": "CREA", "BUN": "BUN", "BUN/CREA": "BUN_CREA",
    "TP": "TP", "ALB": "ALB", "GLOB": "GLOB", "ALT": "ALT", "ALKP": "ALKP",
    "HGB": "HGB", "WBC": "WBC", "RBC": "RBC", "PLT": "PLT", "AMYL": "AMYL", "CHOL": "CHOL"
}

# דאטה-בייס אנציקלופדי מלא
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס חריף."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "unit": "mg/dL", "desc": "תוצר לוואי של פעילות שרירים המפונה בכליות.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה (BUN)", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המיוצרת בכבד ומפונה בכליות.", "cause": "תפקוד כליות ירוד או תזונה עתירת חלבון."},
    "BUN_CREA": {"name": "יחס אוריאה/קריאטינין", "min": 10, "max": 25, "unit": "", "desc": "בודק את האיזון בין פינוי אוריאה לקריאטינין.", "cause": "חוסר איזון תפקודי בכליות."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או בעיות ספיגה.", "cause": "דלקת כרונית או זיהום."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "unit": "g/dL", "desc": "חלבון המיוצר בכבד. מעיד על תפקוד כבד ותזונה.", "cause": "בעיות כבד או איבוד חלבון."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון. עולה במצבי דלקת.", "cause": "פעילות חיסונית מוגברת."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "אנזים המצוי בתאי הכבד. מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד או דלקת כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."},
    "HGB": {"name": "המוגלובין", "min": 12, "max": 18, "unit": "g/dL", "desc": "חלבון נושא חמצן בדם. מדד לאנמיה.", "cause": "אנמיה או התייבשות."}
}

breed_intel = {
    "שיצו": {"risk": "בעיות כבד ואלרגיות עור.", "rec": "מזון קל לעיכול ותומך כבד."},
    "רועה בלגי (מלינואה)": {"risk": "בעיות מפרקים ורגישות בעיכול.", "rec": "חלבון איכותי ומזון מפרקים."},
    "רועה גרמני": {"risk": "דיספלסיה בירך ובעיות לבלב.", "rec": "אנזימי עיכול ומזון Mobility."},
    "מלטז": {"risk": "אבנים בדרכי השתן ומחלות לב.", "rec": "מזון Urinary."}
}

# --- 2. מנועי ה-Auto-Pilot והמומחה ---
def extract_pdf_v40(pdf_file):
    extracted = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = full_text.split('\n')
        for line in lines:
            # זיהוי מטא-דאטה אוטומטי
            if "Patient Name:" in line: extracted["meta"]["name"] = line.split("Name:")[1].split()[0]
            if "Weight:" in line: 
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line)
                if w: extracted["meta"]["weight"] = w.group(1)
            if "Age:" in line:
                a = re.search(r"Age:\s*(\d+)", line)
                if a: extracted["meta"]["age"] = a.group(1)
            if "Doctor:" in line: extracted["meta"]["doctor"] = line.split("Doctor:")[1].strip()
            if "Species:" in line: extracted["meta"]["species"] = "Canine"
            
            # זיהוי מדדים
            for key_word, eng_key in hebrew_mapping.items():
                if key_word in line.upper():
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums: extracted["data"][eng_key] = float(nums[0])
    return extracted

def get_expert_diagnosis(data, weight, age, breed):
    diag = []
    if data.get("CREA", 0) > 1.5 and data.get("BUN", 0) > 27:
        diag.append(f"🚨 **חשד כלייתי:** הצלבה בין קריאטינין לאוריאה. במשקל {weight} ק\"ג מומלץ מזון Renal.")
    if data.get("ALT", 0) > 125 or data.get("ALKP", 0) > 212:
        diag.append(f"🚨 **ממצא כבדי:** חריגה באנזימי כבד. בגזע {breed} יש לעקוב אחר תפקוד הכבד.")
    if not diag: diag.append("✅ **מצב יציב:** המערכות נראות מאוזנות בפיענוח המומחה.")
    return diag

# --- 3. ממשק המשתמש המלא ---
st.set_page_config(page_title="Foodels Ultimate Final V40", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

uploaded_file = st.file_uploader("העלה בדיקת דם (PDF) לסריקה אוטומטית מלאה", type=["pdf"])

if uploaded_file:
    result = extract_pdf_v40(uploaded_file)
    meta = result["meta"]
    data = result["data"]

    # תצוגה ועדכון אוטומטי
    dog_name = st.sidebar.text_input("שם הכלב:", meta.get("name", "בונו"))
    dog_breed = st.sidebar.selectbox("גזע:", list(breed_intel.keys()) + ["מעורב"])
    dog_age = st.sidebar.text_input("גיל:", meta.get("age", "5"))
    dog_weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "15.0"))
    doctor = st.sidebar.text_input("רופא:", meta.get("doctor", "שירה פסקן"))

    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📊 ניתוח מדדים עבור {dog_name}")
            issues_count = 0
            for m, val in data.items():
                if m in blood_db:
                    info = blood_db[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues_count += 1
                    with st.expander(f"{info['name']} ({m}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**מה המדד בודק?** {info['desc']}")
                        st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"**סיבה אפשרית:** {info['cause']}")

        with col2:
            st.subheader("🧠 אבחנת מומחה (הצלבות)")
            summary = get_expert_diagnosis(data, dog_weight, dog_age, dog_breed)
            for line in summary: st.write(line)
            
            if dog_breed in breed_intel:
                st.info(f"🧬 **גנטיקה של {dog_breed}:** {breed_intel[dog_breed]['risk']}\nהמלצה: {breed_intel[dog_breed]['rec']}")
            
            score = max(0, 100 - (issues_count * 10))
            st.metric("Health Score", f"{score}%")

        wa_msg = f"אבחנת פודלס ל*{dog_name}* (משקל: {dog_weight} ק\"ג):\n" + "\n".join(summary)
        url = urllib.parse.quote(wa_msg + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; font-weight: bold; width: 100%; cursor: pointer;">📲 שלח דו"ח אוטומטי מלא ללקוח</button></a>', unsafe_allow_html=True)
