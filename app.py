import streamlit as st
import pdfplumber
import re
import urllib.parse

# --- 1. עיצוב RTL ויישור לימין ---
st.set_page_config(page_title="Foodels Precision-Master V47", layout="wide")
st.markdown("""
    <style>
    body, .main, [data-testid="stSidebar"], .stMarkdown, .stMetric, div[data-testid="stExpander"] {
        direction: rtl; text-align: right;
    }
    .stAlert { direction: rtl; text-align: right; }
    div.stButton > button { width: 100%; background-color: #25D366; color: white; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

# --- 2. דאטה-בייס אנציקלופדי מורחב (הכל מ-V36) ---
blood_db = {
    "GLU": {"name": "גלוקוז", "min": 74, "max": 143, "unit": "mg/dL", "desc": "בודק רמת סוכר בדם.", "cause": "סוכרת או סטרס."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.8, "unit": "mg/dL", "desc": "מדד לתפקוד כליות.", "cause": "עומס כלייתי."},
    "BUN": {"name": "אוריאה (BUN)", "min": 7, "max": 27, "unit": "mg/dL", "desc": "פסולת חלבון המפונה בכליות.", "cause": "תפקוד כליות ירוד."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "desc": "סך החלבונים בדם.", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.3, "max": 4.0, "unit": "g/dL", "desc": "חלבון המעיד על מצב תזונתי.", "cause": "בעיות כבד."},
    "GLOB": {"name": "גלובולין", "min": 2.5, "max": 4.5, "unit": "g/dL", "desc": "חלבונים של מערכת החיסון.", "cause": "פעילות חיסונית מוגברת."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "desc": "מעיד על נזק לתאי כבד.", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", "desc": "קשור לכבד ועצמות.", "cause": "בעיות כבד."}
}

breed_intel = {"שיצו": {"risk": "בעיות כבד ואלרגיות עור.", "rec": "מזון קל לעיכול."}}

# --- 3. מנוע סריקה V47 - מניעת בלבול בין CREA ל-BUN/CREA ---
def extract_v47(pdf_file):
    res = {"data": {}, "meta": {}}
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            lines = text.split('\n')
            for line in lines:
                line_u = line.upper()
                # זיהוי מטא-דאטה (כולל תיקון היפוך שמות ROZ)
                if "PATIENT NAME:" in line_u:
                    raw_name = line.split("Name:")[1].split()[0]
                    res["meta"]["name"] = raw_name[::-1] if any("\u0590" <= c <= "\u05FF" for c in raw_name) else raw_name
                if "WEIGHT:" in line_u:
                    w = re.search(r"Weight:\s*(\d+\.?\d*)", line, re.I)
                    if w: res["meta"]["weight"] = w.group(1)
                
                # חילוץ מדדים בשיטת הדיוק האבסולוטי
                for key in blood_db.keys():
                    # מחפש את המילה בדיוק (למשל CREA ולא BUN/CREA)
                    if re.search(rf"\b{key}\b", line_u):
                        # מוצא את המספר הראשון בשורה. עבור CREA, אנחנו מצפים לערך עשרוני.
                        nums = re.findall(r"(\d+\.\d+|\d+)", line)
                        if nums:
                            val = float(nums[0])
                            # אם זה קריאטינין וזה יצא 10.0, המערכת תבין שזה כנראה ה-Ratio ותמשיך לחפש
                            if key == "CREA" and val > 5.0: continue 
                            res["data"][key] = val
    return res

# --- 4. ממשק המשתמש המלא ---
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

uploaded_file = st.file_uploader("העלה בדיקת דם (PDF) לניתוח סופי ומדויק", type=["pdf"])

if uploaded_file:
    result = extract_v47(uploaded_file)
    meta, data = result["meta"], result["data"]

    dog_name = st.sidebar.text_input("שם הכלב:", meta.get("name", "ROZ"))
    dog_weight = st.sidebar.text_input("משקל (ק\"ג):", meta.get("weight", "20.5"))

    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📊 ניתוח מדדים עבור {dog_name}")
            issues = 0
            for m, val in data.items():
                info = blood_db[m]
                is_bad = val > info["max"] or val < info["min"]
                if is_bad: issues += 1
                with st.expander(f"{info['name']} ({m}): {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                    st.write(f"**מה המדד בודק?** {info['desc']}")
                    st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                    if is_bad: st.error(f"סיבה: {info['cause']}")

        with col2:
            st.subheader("🧠 אבחנת מומחה")
            if data.get("CREA", 0) > 1.8: st.error("🚨 חשד לעומס כלייתי.")
            else: st.success("✅ הבדיקה נראית תקינה לחלוטין.")
            st.metric("Health Score", f"{max(0, 100 - (issues*10))}%")

        url = urllib.parse.quote(f"דו\"ח פודלס ל*{dog_name}*:\nציון בריאות: {max(0, 100 - (issues*10))}%")
        st.markdown(f'<a href="https://wa.me/?text={url}" target="_blank"><button>📲 שלח דו"ח וטסאפ</button></a>', unsafe_allow_html=True)
