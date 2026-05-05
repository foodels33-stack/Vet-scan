import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. הגדרות ליבה: פודלס באר שבע ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "אלט": "ALT", "ALT": "ALT", "ALKP": "ALKP", "פוספטאזה": "ALKP",
    "לבנות": "WBC", "WBC": "WBC", "אאוזינופילים": "EOS", "כולסטרול": "CHOL",
    "עמילאז": "AMYL", "המוגלובין": "HGB", "אדומות": "RBC", "טסיות": "PLT",
    "אלבומין": "ALB", "חלבון": "TP"
}

breed_intelligence = {
    "שיצו": {"genetics": "נטייה לבעיות כבד (Shunt) ואלרגיות עור.", "risk_markers": ["ALT", "EOS"], "rec": "מזון קל לעיכול ותומך כבד."},
    "מלטז": {"genetics": "סיכון לאבנים בדרכי השתן ומחלות לב.", "risk_markers": ["CREA", "BUN"], "rec": "מזון Urinary."},
    "רועה גרמני": {"genetics": "נטייה לדיספלסיה בירך ובעיות עיכול (EPI).", "risk_markers": ["AMYL", "TP"], "rec": "מזון Mobility."},
    "רועה בלגי (מלינואה)": {"genetics": "רגישות נוירולוגית ומפרקים.", "risk_markers": ["CREA", "WBC"], "rec": "חלבון איכותי."},
    "פיטבול/אמסטף": {"genetics": "אלרגיות עור ובעיות בלוטת התריס.", "risk_markers": ["EOS", "CHOL"], "rec": "מזון היפו-אלרגני."},
    "רועה אוסטרלי": {"genetics": "רגישות MDR1 ובעיות עיניים.", "risk_markers": ["ALT", "ALKP"], "rec": "נוגדי חמצון."}
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/uL", "cause": "זיהום או דלקת."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כליות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד או עצם."},
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", "cause": "תזונה או בעיה מטבולית."},
    "TP": {"name": "חלבון כללי", "min": 5.2, "max": 8.2, "unit": "g/dL", "cause": "דלקת כרונית."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "unit": "g/dL", "cause": "תפקוד כבד או כליה."},
    "AMYL": {"name": "עמילאז", "min": 500, "max": 1500, "unit": "U/L", "cause": "בעיות לבלב."}
}

# --- 2. המוח הווטרינרי: מנוע הצלבות ודיאגנוזה ---
def run_expert_diagnosis(data, breed, weight, age):
    diag = []
    # הצלבת כליות ומשקל
    if data.get("CREA", 0) > 1.5 or data.get("BUN", 0) > 27:
        status = "חריפה" if data.get("CREA", 0) > 2.0 else "ראשונית"
        diag.append(f"🚨 **אבחנה כלייתית {status}:** ישנו עומס על הכליות. במשקל של {weight} ק\"ג, חשוב להקפיד על צריכת נוזלים ומזון Renal.")
    # הצלבת כבד וגנטיקה
    if data.get("ALT", 0) > 100 or data.get("ALKP", 0) > 150:
        diag.append(f"🚨 **ממצא כבדי:** חריגה באנזימי כבד. בגזע {breed}, ישנה רגישות מוגברת לממצאים אלו.")
    # הצלבת סוכר וגיל
    if data.get("GLU", 0) > 110 and age > 8:
        diag.append("🚨 **חשד מטבולי:** רמת סוכר גבוהה בגיל מבוגר מחייבת מעקב סוכרת.")
    
    if not diag:
        diag.append("✅ **סיכום מומחה:** לא נמצאו הצלבות מדאיגות. המצב יציב.")
    return diag

# --- 3. מנוע סריקה V32 ---
def extract_v32(image):
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
                        num = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num:
                            val = float(num.group(1))
                            if 0.1 <= val <= 2000 and val != 6789123:
                                line_nums.append(val)
                if line_nums:
                    results[eng_key] = line_nums[-1]
    return results

# --- 4. ממשק המשתמש המלא ---
st.set_page_config(page_title="Foodels Master Brain V32", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע הכלב:", list(breed_intelligence.keys()) + ["מעורב"])
dog_age = st.sidebar.number_input("גיל הכלב:", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🩺 מומחה הפיענוח של פודלס: {dog_name}")

if dog_breed in breed_intelligence:
    with st.expander(f"🧬 רקע גנטי: {dog_breed}", expanded=False):
        st.write(breed_intelligence[dog_breed]['genetics'])
        st.info(f"המלצה: {breed_intelligence[dog_breed]['rec']}")

uploaded_file = st.file_uploader("העלה טופס לסריקה וניתוח מומחה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_v32(img)
    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📊 מדדי מעבדה")
            issues_count = 0
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues_count += 1
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"תוצאה: {val} (טווח: {info['min']}-{info['max']})")
        
        with col2:
            st.subheader("🧠 אבחנת מומחה (הצלבות)")
            expert_summary = run_expert_diagnosis(data, dog_breed, dog_weight, dog_age)
            for line in expert_summary:
                st.write(line)
            
            score = max(0, 100 - (issues_count * 12))
            st.metric("ציון בריאות כללי", f"{score}%")
            st.progress(score / 100)

        wa_text = f"חוות דעת מומחה ל*{dog_name}* מפודלס:\n" + "\n".join(expert_summary)
        msg = urllib.parse.quote(wa_text + f"\nכתובתנו: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח אבחנה מלאה לווטסאפ</button></a>', unsafe_allow_html=True)
