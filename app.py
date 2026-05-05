import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. ליבת הנתונים: פודלס באר שבע ---
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

# --- 2. מנוע המומחה: הצלבות נתונים ודיאגנוזה ---
def generate_expert_diagnosis(data, breed):
    diagnosis = []
    # הצלבת כליות
    if data.get("CREA", 0) > 1.5 and data.get("BUN", 0) > 27:
        diagnosis.append("🚨 **עומס כלייתי משולב:** חריגה בשני מדדי הכליות מעידה על פגיעה בתפקוד הניקוז. יש לשקול מזון Renal.")
    # הצלבת כבד
    if data.get("ALT", 0) > 100 or data.get("ALKP", 0) > 150:
        diagnosis.append("🚨 **ממצא כבדי:** חריגה באנזימי כבד. בשילוב עם גנטיקה של " + breed + ", מומלץ מזון תומך כבד.")
    # הצלבת דלקת
    if data.get("WBC", 0) > 17 and data.get("TP", 0) > 8.2:
        diagnosis.append("🚨 **דלקת כרונית:** שילוב של לבנות וחלבון גבוה מעיד על תהליך דלקתי מתמשך.")
    
    if not diagnosis:
        diagnosis.append("✅ **סיכום כללי:** המדדים העיקריים מאוזנים. מומלץ להמשיך בתזונה הנוכחית.")
    return diagnosis

# --- 3. מנוע סריקה הוליסטי ---
def extract_data_v31(image):
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
                    results[eng_key] = line_nums[-1] # התוצאה הסופית
    return results

# --- 4. ממשק המערכת ---
st.set_page_config(page_title="Foodels Omega Brain V31", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", list(breed_intelligence.keys()) + ["מעורב"])
dog_age = st.sidebar.number_input("גיל:", 0.1, 25.0, 5.0)

st.title(f"🩺 מומחה הפיענוח של פודלס: {dog_name}")

uploaded_file = st.file_uploader("העלה טופס לבדיקה וניתוח מומחה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v31(img)
    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📊 מדדי מעבדה")
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"תוצאה: {val} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"סיבה: {info['cause']}")

        with col2:
            st.subheader("🧠 דיאגנוזה והצלבות")
            expert_notes = generate_expert_diagnosis(data, dog_breed)
            for note in expert_notes:
                st.write(note)
            
            score = max(0, 100 - (len([v for k,v in data.items() if v > blood_db_base.get(k,{}).get('max',999)]) * 12))
            st.metric("Health Score", f"{score}%")

        wa_summary = f"סיכום מומחה ל*{dog_name}* מפודלס:\n" + "\n".join(expert_notes)
        msg = urllib.parse.quote(wa_summary + f"\nבואו אלינו להתאמת תזונה: {SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח חוות דעת מומחה ללקוח</button></a>', unsafe_allow_html=True)
