import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. הגדרות עיצוב RTL ויישור לימין ---
st.set_page_config(page_title="Foodels Omega Final V43", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .main {
        font-family: 'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stExpander"], .stMetric, .stMarkdown {
        direction: rtl;
        text-align: right;
    }
    .stAlert { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס אנציקלופדי מורחב ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס חריף."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד מרכזי לתפקוד כליות.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד או תזונה עתירת חלבון."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או בעיות ספיגה.", "cause": "דלקת כרונית או זיהום."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון המיוצר בכבד. מעיד על תפקוד כבד ותזונה.", "cause": "בעיות כבד או איבוד חלבון."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."}
}

breed_intel = {
    "שיצו": {"risk": "בעיות כבד (Shunt) ואלרגיות עור.", "rec": "מזון קל לעיכול ותומך כבד."},
    "רועה בלגי (מלינואה)": {"risk": "בעיות מפרקים ורגישות בעיכול.", "rec": "חלבון איכותי ומזון מפרקים."},
    "רועה גרמני": {"risk": "דיספלסיה ובעיות לבלב.", "rec": "אנזימי עיכול ומזון Mobility."},
    "מלטז": {"risk": "אבנים בדרכי השתן ומחלות לב.", "rec": "מזון Urinary."}
}

# --- 3. מנוע סריקה V43 ---
def extract_v43(pdf_file):
    res = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = text.split('\n')
        for line in lines:
            line_u = line.upper()
            if "PATIENT NAME:" in line_u: res["meta"]["name"] = line.split("Name:")[1].split()[0]
            if "WEIGHT:" in line_u: 
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line, re.I)
                if w: res["meta"]["weight"] = w.group(1)
            if "AGE:" in line_u:
                a = re.search(r"Age:\s*(\d+)", line, re.I)
                if a: res["meta"]["age"] = a.group(1)
            
            for key in blood_db.keys():
                if key in line_u:
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums: res["data"][key] = float(nums[0])
    return res

# --- 4. ממשק ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

st.title("🩺 המומחה המדויק של פודלס")
uploaded_file = st.file_uploader("העלה בדיקת דם (PDF)", type=["pdf"])

if uploaded_file:
    result = extract_v43(uploaded_file)
    meta = result["meta"]
    data = result["data"]

    name = st.sidebar.text_input("שם הכלב:", meta.get("name", "זוט"))
    breed = st.sidebar.selectbox("גזע:", list(breed_intel.keys()) + ["מעורב"])
    weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "20.5"))
    age = st.sidebar.text_input("גיל (שנים):", meta.get("age", "8"))

    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📊 ניתוח מדדים עבור {name}")
            issues = 0
            for m, val in data.items():
                info = blood_db[m]
                is_bad = val > info["max"] or val < info["min"]
                if is_bad: issues += 1
                with st.expander(f"{info['name']} ({m}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                    st.write(f"**מה המדד בודק?** {info['desc']}")
                    st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                    if is_bad: st.error(f"**סיבה:** {info['cause']}")
        
        with col2:
            st.subheader("🧠 אבחנה והצלבות")
            if data.get("CREA", 0) > 1.8 or data.get("BUN", 0) > 27:
                st.error("🚨 חשד כלייתי: נמצאה הצלבה בין המדדים.")
            else: st.success("✅ המערכות נראות מאוזנות.")
            
            if breed in breed_intel:
                st.info(f"🧬 גנטיקה של {breed}: {breed_intel[breed]['risk']}")
            
            score = max(0, 100 - (issues * 10))
            st.metric("Health Score", f"{score}%")

        wa_msg = f"אבחנה ל*{name}* מפודלס:\nציון בריאות: {score}%\n"
        url = urllib.parse.quote(wa_msg + f"\nכתובת: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button style="width:100%; height:50px; background-color:#25D366; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">📲 שלח דו"ח מלא ללקוח</button></a>', unsafe_allow_html=True)
