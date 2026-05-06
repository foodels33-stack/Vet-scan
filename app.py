import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. תיקון עברית ועיצוב RTL מלא ---
st.markdown("""
    <style>
    .main, .stMarkdown, div[data-testid="stExpander"], .stMetric {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stSidebar"] { direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #25D366; color: white; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס אנציקלופדי מורחב (טווחים מעודכנים) ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס חריף."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד מרכזי לתפקוד כליות.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד או תזונה עתירת חלבון."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או בעיות ספיגה.", "cause": "דלקת כרונית או זיהום."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון המיוצר בכבד. מעיד על תפקוד כבד ותזונה.", "cause": "בעיות כבד או איבוד חלבון."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון. עולה במצבי דלקת.", "cause": "פעילות חיסונית מוגברת."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד או דלקת."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."}
}

breed_intel = {
    "שיצו": {"risk": "בעיות כבד (Shunt) ואלרגיות עור.", "rec": "מזון קל לעיכול ותומך כבד."},
    "רועה בלגי (מלינואה)": {"risk": "בעיות מפרקים ורגישות עיכול.", "rec": "חלבון איכותי ומזון מפרקים."},
    "רועה גרמני": {"risk": "דיספלסיה ובעיות לבלב.", "rec": "אנזימי עיכול ומזון Mobility."},
    "מלטז": {"risk": "אבנים בדרכי השתן ומחלות לב.", "rec": "מזון Urinary."}
}

hebrew_mapping = {"GLU": "GLU", "CREA": "CREA", "BUN": "BUN", "TP": "TP", "ALB": "ALB", "GLOB": "GLOB", "ALT": "ALT", "ALKP": "ALKP"}

# --- 3. מנוע סריקה ואבחנה ---
def extract_v42(pdf_file):
    extracted = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = text.split('\n')
        for line in lines:
            if "Patient Name:" in line: extracted["meta"]["name"] = line.split("Name:")[1].split()[0]
            if "Weight:" in line: 
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line)
                if w: extracted["meta"]["weight"] = w.group(1)
            if "Age:" in line:
                a = re.search(r"Age:\s*(\d+)", line)
                if a: extracted["meta"]["age"] = a.group(1)
            
            for key, eng_key in hebrew_mapping.items():
                if key in line.upper():
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums: extracted["data"][eng_key] = float(nums[0])
    return extracted

# --- 4. ממשק המשתמש ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

st.title("🩺 המומחה המדויק של פודלס")
uploaded_file = st.file_uploader("העלה בדיקת דם (PDF)", type=["pdf"])

if uploaded_file:
    res = extract_v42(uploaded_file)
    meta = res["meta"]
    data = res["data"]

    dog_name = st.sidebar.text_input("שם הכלב:", meta.get("name", "בונו"))
    dog_breed = st.sidebar.selectbox("גזע:", list(breed_intel.keys()) + ["מעורב"])
    dog_weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "15.0"))
    dog_age = st.sidebar.text_input("גיל:", meta.get("age", "5"))

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
                    with st.expander(f"{info['name']} ({m}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**מה המדד בודק?** {info['desc']}")
                        st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"**סיבה אפשרית:** {info['cause']}")
        
        with col2:
            st.subheader("🧠 אבחנת מומחה")
            if data.get("CREA", 0) > 1.8 or data.get("BUN", 0) > 27:
                st.error(f"🚨 **חשד כלייתי:** הצלבה זוהתה. מומלץ ייעוץ תזונתי.")
            else: st.success("✅ המערכות נראות מאוזנות.")
            
            if dog_breed in breed_intel:
                st.info(f"🧬 **גנטיקה של {dog_breed}:** {breed_intel[dog_breed]['risk']}")
            
            score = max(0, 100 - (issues * 10))
            st.metric("Health Score", f"{score}%")

        wa_msg = f"אבחנת פודלס ל*{dog_name}*:\nציון בריאות: {score}%\n"
        url = urllib.parse.quote(wa_msg + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button>📲 שלח דו"ח אוטומטי מלא ללקוח</button></a>', unsafe_allow_html=True)
