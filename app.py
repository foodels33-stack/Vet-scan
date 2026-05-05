import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. הגדרות ונתוני בסיס ---
SHOP_INFO = "פודלס - נחום שריג 33, באר שבע | 08-6655443"

hebrew_mapping = {
    "המוגלובין": "HGB", "אדומות": "RBC", "לבנות": "WBC",
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU",
    "אלבומין": "ALB", "ALKP": "ALKP", "ALT": "ALT", "טסיות": "PLT"
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "unit": "g/dL", "cause": "אנמיה או התייבשות."},
    "RBC": {"name": "כדוריות אדומות", "min": 5.5, "max": 8.5, "unit": "M/uL", "cause": "דימום או מחלת מח עצם."},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "unit": "K/uL", "cause": "זיהום או דלקת."},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "unit": "mg/dL", "cause": "עומס כליות."},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "unit": "mg/dL", "cause": "תפקוד כליות ירוד."},
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "unit": "mg/dL", "cause": "סוכרת או סטרס."},
    "ALB": {"name": "אלבומין", "min": 2.5, "max": 4.0, "unit": "g/dL", "cause": "בעיות כבד או כליה."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "unit": "U/L", "cause": "פגיעה בתאי כבד."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "unit": "U/L", "cause": "בעיות כבד או עצם."},
    "PLT": {"name": "טסיות", "min": 200, "max": 500, "unit": "K/uL", "cause": "בעיות קרישה."}
}

# --- 2. מנוע סריקה "רדיוס-פרו" V29 ---
def extract_data_v29(image):
    d = pytesseract.image_to_data(image, config=r'--oem 3 --psm 6 -l heb+eng', output_type=pytesseract.Output.DICT)
    results = {}
    for i in range(len(d['text'])):
        word = d['text'][i].strip().upper()
        for key_word, eng_key in hebrew_mapping.items():
            if key_word in word or eng_key in word:
                curr_y = d['top'][i]
                line_nums = []
                # אוסף את כל המספרים בשורה ברדיוס מוגדל
                for j in range(len(d['text'])):
                    if abs(d['top'][j] - curr_y) < 40:
                        num_match = re.search(r"(\d+\.?\d*)", d['text'][j])
                        if num_match:
                            val = float(num_match.group(1))
                            # סינון: מתעלם מהתאריך, מספרי טלפון וערכים לא הגיוניים
                            if 0.1 <= val <= 1000 and val != 6789123:
                                line_nums.append(val)
                if line_nums:
                    # לוגיקה חכמה: בדוגמה הצפופה, התוצאה האמיתית היא המספר האחרון בשורה
                    results[eng_key] = line_nums[-1]
    return results

# --- 3. UI ---
st.set_page_config(page_title="Foodels AI V29", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", ["שיצו", "מלטז", "רועה גרמני", "פיטבול", "מלינואה", "מעורב"])

uploaded_file = st.file_uploader("העלה את דף הבדיקה לסריקה סופית", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_data_v29(img)
    if data:
        st.subheader(f"🚀 פיענוח מלא עבור {dog_name}")
        issues = 0
        wa_text = f"סיכום בדיקה ל*{dog_name}* מפודלס:\n"
        col1, col2 = st.columns([2, 1])
        with col1:
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    if is_bad: issues += 1
                    with st.expander(f"{info['name']}: {val} {'🚨' if is_bad else '✅'}", expanded=is_bad):
                        st.write(f"תוצאה: {val} (טווח: {info['min']}-{info['max']})")
                        if is_bad: st.error(f"סיבה: {info['cause']}")
                        wa_text += f"{'📍' if is_bad else '✅'} {info['name']}: {val}\n"
        with col2:
            score = max(0, 100 - (issues * 12))
            st.metric("Health Score", f"{score}%")
            st.progress(score / 100)
        
        msg = urllib.parse.quote(wa_text + f"\n{SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח לווטסאפ</button></a>', unsafe_allow_html=True)
