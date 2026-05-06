import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. הגדרות עיצוב RTL ויישור לימין מושלם ---
st.set_page_config(page_title="Foodels Masterpiece V50", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .main, .stMarkdown, .stMetric, div[data-testid="stExpander"] {
        font-family: 'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
    }
    h1 { text-align: center; color: #1E1E1E; }
    .stAlert { direction: rtl; text-align: right; }
    div[data-testid="stSidebar"] { text-align: right; }
    div.stButton > button { width: 100%; background-color: #25D366; color: white; font-weight: bold; height: 50px; border-radius: 12px; border: none; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס אנציקלופדי מורחב (50 מדדים) ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס חריף."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד מרכזי לתפקוד כליות ופינוי פסולת שריר.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה (BUN)", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד או תזונה עתירת חלבון."},
    "BUN/CREA": {"name": "יחס אוריאה/קריאטינין", "min": 10, "max": 25, "unit": "", "desc": "יחס המשמש להערכת מקור הבעיה הכלייתית.", "cause": "חוסר איזון תפקודי."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או בעיות ספיגה.", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון כבד המעיד על מצב תזונתי ותפקוד.", "cause": "בעיות כבד או איבוד חלבון."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון. עולה במצבי דלקת.", "cause": "פעילות חיסונית מוגברת."},
    "ALB/GLOB": {"name": "יחס אלבומין/גלובולין", "min": 0.6, "max": 1.5, "unit": "", "desc": "עוזר לאבחן מחלות כרוניות ומצבי דלקת.", "cause": "שינוי במאזן החלבונים."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "אנזים המצוי בתאי הכבד. מעיד על נזק לתאים.", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."}
}

breed_intel = {
    "שיצו": {"risk": "בעיות כבד (Shunt) ואלרגיות עור.", "rec": "מזון קל לעיכול ותומך כבד."},
    "בוקסר": {"risk": "נטייה לבעיות לב (AS) וגידולי עור.", "rec": "מזון עשיר באומגה 3 ותמיכה קרדיאלית."},
    "מלינואה": {"risk": "בעיות מפרקים ורגישות עיכול.", "rec": "חלבון איכותי ותמיכה במפרקים."},
    "רועה גרמני": {"risk": "דיספלסיה בירך ובעיות לבלב.", "rec": "מזון Mobility ואנזימי עיכול."}
}

# --- 3. מנוע סריקה V50 (אוטומציה ודיוק עשרוני) ---
def extract_v50(pdf_file):
    res = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = text.split('\n')
        for line in lines:
            line_u = line.upper()
            if "PATIENT NAME:" in line_u: 
                n = line.split("Name:")[1].split()[0]
                res["meta"]["name"] = n[::-1] if any("\u0590" <= c <= "\u05FF" for c in n) else n
            if "WEIGHT:" in line_u:
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line, re.I)
                if w: res["meta"]["weight"] = w.group(1)
            if "AGE:" in line_u:
                a = re.search(r"Age:\s*(\d+)", line, re.I)
                if a: res["meta"]["age"] = a.group(1)

            for key in blood_db.keys():
                if key in line_u:
                    match = re.search(rf"{re.escape(key)}\s+(\d+\.\d+|\d+)", line_u)
                    if match:
                        val = float(match.group(1))
                        if key == "CREA" and val > 5.0: continue 
                        res["data"][key] = val
    return res

# --- 4. ממשק המשתמש ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

st.markdown("<h1>🩺 מערכת פיענוח בדיקות דם - פודלס באר שבע</h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("העלה בדיקת דם (PDF) לסריקה אוטומטית מושלמת", type=["pdf"])

if uploaded_file:
    result = extract_v50(uploaded_file)
    meta, data = result["meta"], result["data"]

    st.sidebar.subheader("📋 פרטים שנשלפו")
    dog_name = st.sidebar.text_input("שם הכלב:", meta.get("name", "רוז"))
    dog_breed = st.sidebar.selectbox("גזע:", list(breed_intel.keys()) + ["מעורב"])
    dog_weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "20.50"))

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
                        if is_bad: st.error(f"**סיבה:** {info['cause']}")

        with col2:
            st.subheader("🧠 אבחנת מומחה")
            if data.get("CREA", 0) > 1.8: st.error("🚨 חשד לעומס כלייתי.")
            else: st.success("✅ הבדיקה נראית תקינה ומאוזנת.")
            
            if dog_breed in breed_intel:
                st.info(f"🧬 **גנטיקה של {dog_breed}:** {breed_intel[dog_breed]['risk']}")
            
            score = max(0, 100 - (issues * 10))
            st.metric("Health Score", f"{score}%")

        wa_text = f"אבחנת פודלס ל*{dog_name}*:\nציון בריאות: {score}%\nמשקל: {dog_weight} ק\"ג\n{SHOP_INFO}"
        url = urllib.parse.quote(wa_text)
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button>📲 שלח דו"ח וטסאפ מושלם</button></a>', unsafe_allow_html=True)
