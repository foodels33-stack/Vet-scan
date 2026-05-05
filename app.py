import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. הגדרות ונתוני פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "ALT": "ALT", "ALKP": "ALKP", "לבנות": "WBC", "WBC": "WBC", "המוגלובין": "HGB",
    "אדומות": "RBC", "טסיות": "PLT", "אלבומין": "ALB", "חלבון": "TP", "עמילאז": "AMYL", "כולסטרול": "CHOL"
}

breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt), אלרגיות עור ובעיות נשימה.", "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות מסתמי לב.", "rec": "מזון Urinary."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "rec": "מזון Mobility ואנזימי עיכול."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ובעיות מפרקים.", "rec": "חלבון איכותי."},
    "פיטבול/אמסטף": {"genetics": "אלרגיות עור ובעיות בלוטת התריס.", "rec": "מזון היפו-אלרגני."},
    "לברדור/גולדן": {"genetics": "מפרקי ירך, השמנה ונטייה לגידולים.", "rec": "מזון דל קלוריות."},
    "רועה אוסטרלי": {"genetics": "רגישות MDR1 ובעיות עיניים.", "rec": "נוגדי חמצון ותמיכה בכבד."}
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "sane_max": 25, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "RBC": {"name": "כדוריות אדומות", "min": 5.5, "max": 8.5, "sane_max": 15, "unit": "M/uL", "cause": "דימום או בעיה במח העצם."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "sane_max": 100, "unit": "K/uL", "cause": "זיהום או דלקת פעילה."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "sane_max": 15, "unit": "mg/dL", "cause": "עומס כליות או פגיעה בתפקוד."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "sane_max": 200, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "sane_max": 2000, "unit": "U/L", "cause": "פגיעה בתאי כבד או דלקת."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "sane_max": 3000, "unit": "U/L", "cause": "בעיות כבד או עצם."},
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "sane_max": 600, "unit": "mg/dL", "cause": "סוכרת או סטרס חריף."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "sane_max": 1000, "unit": "mg/dL", "cause": "תזונה שומנית או בעיה מטבולית."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "sane_max": 15, "unit": "g/dL", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "sane_max": 10, "unit": "g/dL", "cause": "תפקוד כבד או כליה."},
    "AMYL": {"name": "עמילאז", "min": 500, "max": 1500, "sane_max": 5000, "unit": "U/L", "cause": "בעיות בלבלב."}
}

# --- 2. מנוע המומחה: הצלבות ודיאגנוזה ---
def run_expert_diagnosis(data, breed, weight, age):
    diag = []
    if data.get("CREA", 0) > 1.5 or data.get("BUN", 0) > 27:
        diag.append(f"🚨 **חשד לכשל כלייתי:** הצלבה בין קריאטינין לאוריאה. במשקל {weight} ק\"ג מומלץ מעבר למזון רפואי.")
    if data.get("ALT", 0) > 100 or data.get("ALKP", 0) > 150:
        diag.append(f"🚨 **ממצא כבדי:** חריגה באנזימי כבד. בגזע {breed} מומלץ לתמוך עם תוספי כבד.")
    if data.get("GLU", 0) > 110 and age > 8:
        diag.append("🚨 **חשד מטבולי:** רמת סוכר גבוהה בגיל מבוגר מחייבת מעקב סוכרת.")
    if not diag: diag.append("✅ **מצב יציב:** לא זוהו הצלבות חריגות בין מערכות הגוף.")
    return diag

# --- 3. מנוע סריקה מאומת (V34) ---
def extract_v34(image):
    d = pytesseract.image_to_data(image, config=r'--oem 3 --psm 6 -l heb+eng', output_type=pytesseract.Output.DICT)
    results = {}
    for i in range(len(d['text'])):
        word = d['text'][i].strip().upper()
        for key_word, eng_key in hebrew_mapping.items():
            if key_word in word or eng_key in word:
                curr_y = d['top'][i]
                potential_vals = []
                for j in range(len(d['text'])):
                    if abs(d['top'][j] - curr_y) < 30:
                        num = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num:
                            val = float(num.group(1))
                            sane_limit = blood_db_base.get(eng_key, {}).get('sane_max', 5000)
                            if 0.1 <= val <= sane_limit and val != 6789123:
                                potential_vals.append(val)
                if potential_vals:
                    results[eng_key] = potential_vals[-1]
    return results

# --- 4. ממשק המערכת ---
st.set_page_config(page_title="Foodels Legacy V34", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🩺 מומחה הפיענוח של פודלס: {dog_name}")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 רקע גנטי ודגשים: {dog_breed}", expanded=True):
        st.write(f"**סיכונים:** {breed_intelligence[dog_breed]['genetics']}")
        st.info(f"💡 **המלצת פודלס:** {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה טופס לבדיקה אבחנתית", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_v34(img)
    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📊 מדדי מעבדה מאומתים")
            issues_count = 0
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues_count += 1
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"**תוצאה:** {val} {info['unit']} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"⚠️ **סיבה אפשרית:** {info['cause']}")

        with col2:
            st.subheader("🧠 אבחנת מומחה (הצלבות)")
            expert_summary = run_expert_diagnosis(data, dog_breed, dog_weight, dog_age)
            for line in expert_summary: st.write(line)
            
            score = max(0, 100 - (issues_count * 8))
            st.metric("ציון בריאות כללי", f"{score}%")
            st.progress(score / 100)

        wa_text = f"אבחנת מומחה ל*{dog_name}* מפודלס באר שבע:\n" + "\n".join(expert_summary)
        msg = urllib.parse.quote(wa_text + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח אבחנה מלאה ללקוח</button></a>', unsafe_allow_html=True)
