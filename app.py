import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. הגדרות עיצוב RTL ויישור לימין ---
st.set_page_config(page_title="Foodels Absolute Precision V45", layout="wide")

st.markdown("""
    <style>
    body, .main, [data-testid="stSidebar"], .stMarkdown, .stMetric, div[data-testid="stExpander"] {
        direction: rtl; text-align: right;
    }
    .stAlert { direction: rtl; text-align: right; }
    div.stButton > button { width: 100%; background-color: #25D366; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס אנציקלופדי מורחב (50 מדדים) ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס חריף."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד מרכזי לתפקוד כליות ופינוי פסולת שריר.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה (BUN)", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד."},
    "BUN_CREA": {"name": "יחס אוריאה/קריאטינין", "min": 10, "max": 25, "unit": "", "desc": "יחס להערכת מקור הבעיה הכלייתית.", "cause": "חוסר איזון תפקודי."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או ספיגה.", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון כבד המעיד על מצב תזונתי.", "cause": "בעיות כבד או איבוד חלבון."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון.", "cause": "פעילות חיסונית מוגברת."},
    "ALB_GLOB": {"name": "יחס אלבומין/גלובולין", "min": 0.6, "max": 1.5, "unit": "", "desc": "עוזר לאבחן מחלות כרוניות.", "cause": "שינוי במאזן החלבונים."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."}
}

breed_intel = {
    "שיצו": {"risk": "בעיות כבד (Shunt) ואלרגיות עור.", "rec": "מזון קל לעיכול ותומך כבד."},
    "רועה בלגי (מלינואה)": {"risk": "בעיות מפרקים ורגישות בעיכול.", "rec": "חלבון איכותי ומזון מפרקים."},
    "רועה גרמני": {"risk": "דיספלסיה ובעיות לבלב.", "rec": "אנזימי עיכול ומזון Mobility."},
    "מלטז": {"risk": "אבנים בדרכי השתן ומחלות לב.", "rec": "מזון Urinary."}
}

# --- 3. מנוע סריקה משופר עם תיקון עשרוני (V45) ---
def extract_v45(pdf_file):
    res = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = full_text.split('\n')
        for line in lines:
            line_u = line.upper()
            # זיהוי מטא-דאטה
            if "PATIENT NAME:" in line_u: 
                raw_name = line.split("Name:")[1].split()[0]
                res["meta"]["name"] = raw_name[::-1] if any("\u0590" <= c <= "\u05FF" for c in raw_name) else raw_name
            if "WEIGHT:" in line_u:
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line, re.I)
                if w: res["meta"]["weight"] = w.group(1)
            if "AGE:" in line_u:
                a = re.search(r"Age:\s*(\d+)", line, re.I)
                if a: res["meta"]["age"] = a.group(1)
            if "DOCTOR:" in line_u: res["meta"]["doctor"] = line.split("Doctor:")[1].strip()

            # זיהוי מדדים עם תמיכה עשרונית מלאה
            for key in blood_db.keys():
                key_clean = key.replace("_", "/")
                if key_clean in line_u:
                    # תופס מספרים עם נקודה עשרונית בצורה מדויקת
                    nums = re.findall(r"(?<!\d)(\d+\.\d+|\d+)(?!\d)", line)
                    if nums: res["data"][key] = float(nums[0])
    return res

# --- 4. ממשק המערכת המלא ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

uploaded_file = st.file_uploader("העלה בדיקת דם (PDF) לסריקה אוטומטית מלאה", type=["pdf"])

if uploaded_file:
    result = extract_v45(uploaded_file)
    meta, data = result["meta"], result["data"]

    dog_name = st.sidebar.text_input("שם הכלב:", meta.get("name", "ROZ"))
    dog_breed = st.sidebar.selectbox("גזע:", list(breed_intel.keys()) + ["מעורב"])
    dog_weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "20.5"))
    dog_age = st.sidebar.text_input("גיל:", meta.get("age", "5"))
    doctor = st.sidebar.text_input("רופא:", meta.get("doctor", "שירה פסקן"))

    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📊 ניתוח מדדים עבור {dog_name}")
            issues = 0
            for m, val in data.items():
                if m in blood_db:
                    info = blood_db[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    with st.expander(f"{info['name']} ({m.replace('_','/')}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**מה המדד בודק?** {info['desc']}")
                        st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"**סיבה אפשרית:** {info['cause']}")
        
        with col2:
            st.subheader("🧠 אבחנה והצלבות")
            if data.get("CREA", 0) > 1.8 and data.get("BUN", 0) > 27:
                st.error(f"🚨 **חשד כלייתי:** הצלבה זוהתה. מומלץ ייעוץ תזונתי.")
            else: st.success("✅ המדדים שנבדקו נראים מאוזנים.")
            
            if dog_breed in breed_intel:
                st.info(f"🧬 **גנטיקה של {dog_breed}:** {breed_intel[dog_breed]['risk']}")
            
            score = max(0, 100 - (issues * 10))
            st.metric("Health Score", f"{score}%")

        wa_msg = f"אבחנת פודלס ל*{dog_name}* (משקל: {dog_weight} ק\"ג):\nציון בריאות: {score}%\n"
        url = urllib.parse.quote(wa_msg + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button>📲 שלח דו"ח אוטומטי מלא ללקוח</button></a>', unsafe_allow_html=True)
