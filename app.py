import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. נתוני ליבה: פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP", "RBC": "RBC", "HGB": "HGB", "PLT": "PLT"
}

breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ובעיות נשימה.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן (Struvite) ומחלות מסתמי לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון דל מינרלים (Urinary)."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility ואנזימי עיכול."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ובעיות מפרקים בעומס גבוה.", "risk_markers": ["CREA", "WBC"], "rec": "תזונה עתירת חלבון איכותי."},
    "פיטבול/אמסטף": {"genetics": "אלרגיות עור קשות ובעיות בבלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון היפו-אלרגני על בסיס דגים."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "risk_markers": ["CHOL", "GLU"], "rec": "מזון דל קלוריות."},
    "רועה אוסטרלי": {"genetics": "רגישות MDR1 ובעיות עיניים.", "risk_markers": ["ALT", "ALKP"], "rec": "נוגדי חמצון ותמיכה בכבד."}
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "RBC": {"name": "כדוריות אדומות", "min": 5.5, "max": 8.5, "unit": "M/uL", "cause": "דימום או בעיה במח העצם."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/uL", "cause": "זיהום או דלקת פעילה."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כליות או התייבשות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד או עצם."},
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה שומנית או מטבוליזם."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "unit": "g/dL", "cause": "תפקוד כבד או כליה."},
    "AMYL": {"name": "עמילאז", "min": 500, "max": 1500, "unit": "U/L", "cause": "בעיות לבלב."}
}

# --- 2. מנוע סריקה הוליסטי V30 ---
def extract_data_v30(image):
    d = pytesseract.image_to_data(image, config=r'--oem 3 --psm 6 -l heb+eng', output_type=pytesseract.Output.DICT)
    results = {}
    for i in range(len(d['text'])):
        word = d['text'][i].strip().upper()
        for key_word, eng_key in hebrew_mapping.items():
            if key_word in word or eng_key in word:
                curr_y = d['top'][i]
                line_nums = []
                for j in range(len(d['text'])):
                    if abs(d['top'][j] - curr_y) < 35:
                        num_match = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num_match:
                            val = float(num_match.group(1))
                            if 0.1 <= val <= 2000 and val != 6789123:
                                line_nums.append(val)
                if line_nums:
                    # לוגיקה חכמה: בטפסים צפופים התוצאה היא בדרך כלל המספר האחרון בשורה
                    results[eng_key] = line_nums[-1]
    return results

# --- 3. UI ---
st.set_page_config(page_title="Foodels Ultimate AI V30", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", list(breed_intelligence.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל:", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🚀 ה-Machine של פודלס: פיענוח מלא עבור {dog_name}")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 נקודות תורפה גנטיות ל{dog_breed}", expanded=True):
        st.write(f"**סיכונים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה את טופס הבדיקה לסריקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v30(img)
    if data:
        issues = 0
        wa_summary = f"סיכום בריאות ל*{dog_name}* מפודלס באר שבע:\n"
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("ניתוח מדדים וממצאים")
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.markdown(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"⚠️ **סיבה:** {info['cause']}")
                        wa_summary += f"{'📍' if is_bad else '✅'} {info['name']}: {val}\n"
        with col2:
            st.subheader("ציון בריאות")
            score = max(0, 100 - (issues * 10))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)
            if score < 85: st.warning("מומלץ ייעוץ תזונתי להתאמת מזון בחנות.")
        
        msg = urllib.parse.quote(wa_summary + f"\nבואו אלינו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח סיכום מלא ללקוח</button></a>', unsafe_allow_html=True)
