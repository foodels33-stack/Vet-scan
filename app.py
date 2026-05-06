import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- עיצוב RTL ויישור לימין ---
st.set_page_config(page_title="Foodels Neural V44", layout="wide")
st.markdown("""
    <style>
    body, .main, [data-testid="stSidebar"], .stMarkdown, .stMetric, div[data-testid="stExpander"] {
        direction: rtl; text-align: right;
    }
    .stAlert { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# דאטה-בייס אנציקלופדי עם כל המדדים מהטופס
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם. חיוני לאבחון סוכרת וסטרס.", "cause": "סוכרת או סטרס."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד מרכזי לתפקוד כליות.", "cause": "עומס כלייתי או התייבשות."},
    "BUN": {"name": "אוריאה (BUN)", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד."},
    "BUN_CREA": {"name": "יחס אוריאה/קריאטינין", "min": 10, "max": 25, "unit": "", "desc": "יחס המשמש להערכת מקור הבעיה הכלייתית.", "cause": "חוסר איזון תפקודי."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם. מעיד על דלקת או בעיות ספיגה.", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון כבד המעיד על מצב תזונתי ותפקוד.", "cause": "בעיות כבד או איבוד חלבון."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון. עולה בדלקת.", "cause": "פעילות חיסונית מוגברת."},
    "ALB_GLOB": {"name": "יחס אלבומין/גלובולין", "min": 0.6, "max": 1.5, "unit": "", "desc": "יחס העוזר להבחין בין סוגי מחלות כרוניות.", "cause": "שינוי במאזן החלבונים."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד, דרכי מרה ועצמות.", "cause": "בעיות בדרכי מרה או כבד."}
}

def fix_hebrew_english_mix(text):
    """מתקן את היפוך הטקסט באנגלית (כמו ROZ שהופך לזור)"""
    if re.search(r'[a-zA-Z]', text):
        return text[::-1] if any("\u0590" <= c <= "\u05FF" for c in text) else text
    return text

def extract_neural_v44(pdf_file):
    res = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        lines = text.split('\n')
        for line in lines:
            line_u = line.upper()
            if "PATIENT NAME:" in line_u: 
                raw_name = line.split("Name:")[1].split()[0]
                res["meta"]["name"] = fix_hebrew_english_mix(raw_name)
            if "WEIGHT:" in line_u:
                w = re.search(r"Weight:\s*(\d+\.?\d*)", line, re.I)
                if w: res["meta"]["weight"] = w.group(1)
            
            for key in blood_db.keys():
                key_clean = key.replace("_", "/")
                if key_clean in line_u:
                    nums = re.findall(r"(\d+\.?\d*)", line)
                    if nums: res["data"][key] = float(nums[0])
    return res

# --- ממשק משתמש ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

uploaded_file = st.file_uploader("העלה בדיקת דם (PDF) לסריקה מדויקת", type=["pdf"])

if uploaded_file:
    result = extract_neural_v44(uploaded_file)
    meta = result["meta"]
    data = result["data"]

    st.sidebar.text_input("שם הכלב:", meta.get("name", "ROZ"))
    st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "20.5"))

    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📊 ניתוח מדדים עבור {meta.get('name', 'ROZ')}")
            for m, val in data.items():
                info = blood_db[m]
                is_bad = val > info["max"] or val < info["min"]
                with st.expander(f"{info['name']} ({m.replace('_','/')}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                    st.write(f"**מה המדד בודק?** {info['desc']}")
                    st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                    if is_bad: st.error(f"**סיבה:** {info['cause']}")
        
        with col2:
            st.subheader("🧠 אבחנת מומחה")
            if any(data.get(k, 0) > blood_db[k]["max"] for k in data):
                st.error("🚨 נמצאו חריגות בבדיקה.")
            else: st.success("✅ כל המדדים בטווח התקין.")
            score = max(0, 100 - (len([k for k,v in data.items() if v > blood_db[k]['max']]) * 10))
            st.metric("Health Score", f"{score}%")

        url = urllib.parse.quote(f"אבחנת פודלס ל*{meta.get('name', 'ROZ')}*:\nציון בריאות: {score}%\n{SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button style="width:100%; height:50px; background-color:#25D366; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">📲 שלח דו"ח ללקוח</button></a>', unsafe_allow_html=True)
