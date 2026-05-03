import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# --- מאגר הידע של פודלס: מדדים, טווחים, גורמים והמלצות ---
blood_db = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", 
             "cause": "עומס על הכליות, התייבשות או בעיה בזרימת הדם.",
             "rec": "מזון רפואי Renal (דל חלבון וזרחן)."},
    "EOS": {"name": "אאוזינופילים (אלרגיה)", "min": 0.1, "max": 1.2, "unit": "x10³/µL", 
            "cause": "תגובה אלרגית למזון, לסביבה או נוכחות טפילים.",
            "rec": "מזון היפו-אלרגני עם חלבון מפורק (Anallergenic/Hypo)."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", 
            "cause": "פגיעה בתאי כבד עקב רעלים, דלקת או תרופות.",
            "rec": "מזון Hepatic ותוספי ניקוי רעלים (סילמרין)."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", 
            "cause": "סוכרת, סטרס חריף או צריכת פחמימות עודפת.",
            "rec": "מזון לניהול משקל וסוכרת (Weight Management/Diabetic)."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", 
            "cause": "זיהום חיידקי, דלקת או תגובה חיסונית.",
            "rec": "חיזוק אומגה 3 ונוגדי חמצון במזון."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", 
             "cause": "תזונה עתירת שומן או חוסר איזון הורמונלי.",
             "rec": "מזון דל שומן (Low Fat/Gastro)."},
    "ALKP": {"name": "פוספטאזה בסיסית", "min": 23, "max": 212, "unit": "U/L", 
             "cause": "חסימת דרכי מרה או שימוש בסטרואידים.",
             "rec": "בדיקת וטרינר ומזון תומך כבד."},
    "BUN": {"name": "אוריאה (Urea)", "min": 7, "max": 27, "unit": "mg/dL", 
            "cause": "פירוק חלבון מוגבר או תפקוד כלייתי ירוד.",
            "rec": "הגברת שתייה ומעבר למזון מופחת חלבון."},
    "PLT": {"name": "טסיות דם", "min": 200, "max": 500, "unit": "K/µL", 
            "cause": "דימומים, מחלות קרציות או דלקת כרונית.",
            "rec": "תוספי ויטמין ותמיכה במערכת הדם."},
    "AMYL": {"name": "עמילאז (לבלב)", "min": 500, "max": 1500, "unit": "U/L", 
             "cause": "דלקת בלבלב או קושי בעיכול פחמימות.",
             "rec": "מזון Gastrointestinal קל לעיכול."}
}

def extract_data(image):
    # הגדרת מנוע OCR לדיוק מירבי
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    # ניקוי הטקסט
    clean_text = re.sub(r'[^a-zA-Z0-9.\s:]', ' ', text)
    results = {}
    for marker in blood_db.keys():
        pattern = rf"{marker}.*?(\d+\.?\d*)"
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            results[marker] = float(match.group(1))
    return results

# --- ממשק המשתמש (UI) ---
st.set_page_config(page_title="Poodles Vet-Scan Pro", layout="centered")

# סרגל צד - ניהול לקוח
st.sidebar.image("https://poodles.co.il/logo.png", width=150) # אם יש לינק ללוגו שלך
st.sidebar.header("📋 פרטי המטופל")
dog_name = st.sidebar.text_input("שם הכלב:", "באדי")
dog_breed = st.sidebar.text_input("גזע:", "מעורב")
dog_age = st.sidebar.number_input("גיל:", 0.0, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 15.0)

# כותרת ראשית
st.title(f"🐾 מפענח הבריאות של {dog_name}")
st.markdown(f"**חנות חיות פודלס | נחום שריג 33, באר שבע**")
st.divider()

# העלאת קובץ
uploaded_file = st.file_uploader("העלה צילום של טופס בדיקת הדם", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="הטופס שנסרק", use_container_width=True)
    
    with st.spinner("מנתח נתונים..."):
        data = extract_data(img)
    
    if data:
        st.success(f"נמצאו {len(data)} מדדים!")
        whatsapp_text = f"היי! זה סיכום בדיקת הדם של *{dog_name}* מפודלס:\n"
        whatsapp_text += f"גזע: {dog_breed} | משקל: {dog_weight}קג\n---\n"
        
        for m, val in data.items():
            info = blood_db[m]
            is_issue = val > info["max"] or val < info["min"]
            status = "🚨 חריגה" if is_issue else "✅ תקין"
            color = "red" if is_issue else "green"
            
            with st.expander(f"{info['name']}: {val} {info['unit']} ({status})", expanded=is_issue):
                st.markdown(f"### תוצאה: :{color}[{val} {info['unit']}]")
                st.write(f"**טווח תקין:** {info['min']} - {info['max']}")
                if is_issue:
                    st.info(f"🧐 **למה זה קורה?** {info['cause']}")
                    st.warning(f"💡 **המלצת פודלס:** {info['rec']}")
                    whatsapp_text += f"📍 *{info['name']}*: {val} (חריגה)\nהמלצה: {info['rec']}\n\n"
                else:
                    whatsapp_text += f"✅ *{info['name']}*: {val} (תקין)\n\n"
        
        # כפתור ווטסאפ
        whatsapp_text += "\nנשמח לעזור בהתאמת המזון בחנות!"
        encoded_msg = urllib.parse.quote(whatsapp_text)
        
        st.markdown(f"""
            <a href="https://wa.me/?text={encoded_msg}" target="_blank">
                <button style="background-color: #25D366; color: white; border: none; padding: 20px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 20px; font-weight: bold;">
                    📲 שלח סיכום לווטסאפ של הלקוח
                </button>
            </a>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ הכן להדפסה"):
            st.write("לחץ על Ctrl+P במקלדת כדי להדפיס את העמוד כדו''ח.")
            
    else:
        st.error("לא נמצאו מדדים. וודא שהצילום ברור ומכיל קיצורים כמו CREA, ALT וכו'.")

st.sidebar.markdown("---")
st.sidebar.write("📞 טלפון לחנות: 08-6655443")
