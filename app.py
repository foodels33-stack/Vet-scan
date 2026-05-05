import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- 1. הגדרות ונתוני פודלס ---
SHOP_INFO = "פודלס - נחום שריג 33, שכונת רמות, באר שבע | 08-6655443"

hebrew_mapping = {
    "קריאטינין": "CREA", "אוריאה": "BUN", "גלוקוז": "GLU", "סוכר": "GLU",
    "ALT": "ALT", "ALKP": "ALKP", "לבנות": "WBC", "המוגלובין": "HGB",
    "אדומות": "RBC", "טסיות": "PLT", "אלבומין": "ALB", "כולסטרול": "CHOL"
}

blood_db_base = {
    "HGB": {"name": "המוגלובין", "min": 12.0, "max": 18.0, "sane_max": 25, "unit": "g/dL"},
    "WBC": {"name": "כדוריות לבנות", "min": 6.0, "max": 17.0, "sane_max": 100, "unit": "K/uL"},
    "CREA": {"name": "קריאטינין", "min": 0.5, "max": 1.5, "sane_max": 15, "unit": "mg/dL"},
    "BUN": {"name": "אוריאה", "min": 7, "max": 27, "sane_max": 200, "unit": "mg/dL"},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 100, "sane_max": 2000, "unit": "U/L"},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 20, "max": 150, "sane_max": 3000, "unit": "U/L"},
    "GLU": {"name": "גלוקוז", "min": 70, "max": 110, "sane_max": 600, "unit": "mg/dL"},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "sane_max": 1000, "unit": "mg/dL"}
}

# --- 2. מנוע סריקה עם אימות ביולוגי V33 ---
def extract_v33(image):
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
                            # אימות ביולוגי: האם המספר הגיוני למדד הזה?
                            sane_limit = blood_db_base.get(eng_key, {}).get('sane_max', 5000)
                            if 0.1 <= val <= sane_limit and val != 6789123:
                                potential_vals.append(val)
                if potential_vals:
                    # לוקח את הערך שהכי סביר שהוא התוצאה (לא הטווח)
                    results[eng_key] = potential_vals[0]
    return results

# --- 3. מוח מומחה (הצלבות) ---
def run_diagnosis(data, breed, weight):
    diag = []
    if data.get("CREA", 0) > 1.5 and data.get("BUN", 0) > 27:
        diag.append(f"🚨 **חשד לכשל כלייתי:** הצלבה בין קריאטינין לאוריאה. במשקל {weight} ק\"ג מומלץ מעבר למזון רפואי.")
    if data.get("ALT", 0) > 100 or data.get("ALKP", 0) > 150:
        diag.append(f"🚨 **עומס כבדי:** אנזימי כבד גבוהים. בגזע {breed} מומלץ לתמוך עם תוספי כבד וניקוי רעלים.")
    if not diag: diag.append("✅ **מצב יציב:** לא זוהו הצלבות חריגות בין מערכות הגוף.")
    return diag

# --- 4. UI ---
st.set_page_config(page_title="Foodels Clinical V33", layout="wide")
st.sidebar.title("🐾 Foodels Lab Pro")
st.sidebar.info(SHOP_INFO)

dog_name = st.sidebar.text_input("שם הכלב:", "בונו")
dog_breed = st.sidebar.selectbox("גזע:", ["שיצו", "רועה גרמני", "מלינואה", "מלטז", "מעורב"])
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

st.title(f"🩺 מומחה הפיענוח של פודלס: {dog_name}")

uploaded_file = st.file_uploader("העלה טופס לבדיקה אמינה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    data = extract_v33(img)
    if data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📊 תוצאות מאומתות")
            for m, val in data.items():
                if m in blood_db_base:
                    info = blood_db_base[m]
                    is_bad = val > info["max"] or val < info["min"]
                    st.write(f"{'🚨' if is_bad else '✅'} **{info['name']}**: {val} (טווח: {info['min']}-{info['max']})")
        
        with col2:
            st.subheader("🧠 ניתוח מומחה")
            summary = run_diagnosis(data, dog_breed, dog_weight)
            for line in summary: st.write(line)
            
        wa_text = f"אבחנת מומחה ל*{dog_name}* מפודלס:\n" + "\n".join(summary)
        msg = urllib.parse.quote(wa_text + f"\n{SHOP_INFO}")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">📲 שלח אבחנה אמינה לווטסאפ</button></a>', unsafe_allow_html=True)
