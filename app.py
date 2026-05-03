import streamlit as st
import pytesseract
from PIL import Image
import re
import urllib.parse

# מאגר אינטליגנציה לגזעים קטנים וגדולים - מבוסס מחקר וטרינרי
breed_data = {
    "שיצו": {"risks": "נטייה לבעיות בכבד, אלרגיות עור ובעיות בעיניים. דורש תזונה קלה לעיכול.", "focus": ["ALT", "EOS"]},
    "מלטז": {"risks": "רגישות גבוהה לאבנים בדרכי השתן ובעיות שיניים. דורש בקרה על מינרלים.", "focus": ["CREA", "BUN"]},
    "יורקשייר טרייר": {"risks": "נטייה לנפילות סוכר (היפוגליקמיה) ובעיות במערכת העיכול.", "focus": ["GLU", "AMYL"]},
    "מלטיפו": {"risks": "שילוב גנטי הרגיש לבעיות עיכול, אלרגיות מזון ובעיות ברכיים.", "focus": ["EOS", "AMYL"]},
    "בולדוג צרפתי": {"risks": "בעיות נשימה, נטייה להשמנה ואלרגיות עור חריפות. דורש חלבון איכותי.", "focus": ["WBC", "EOS", "CHOL"]},
    "פומרניאן": {"risks": "בעיות בלוטת התריס, קריסת קנה נשימה ובעיות עור.", "focus": ["CHOL", "WBC"]},
    "פקינז": {"risks": "בעיות לב ובעיות נשימה עקב מבנה הפנים. רגישות לחום.", "focus": ["ALT", "WBC"]},
    "צ'יוואווה": {"risks": "בעיות לב, שיניים ונפילות סוכר.", "focus": ["GLU", "ALT"]},
    "לברדור/גולדן": {"risks": "נטייה להשמנה, בעיות מפרקים וגידולים.", "focus": ["CHOL", "GLU", "WBC"]},
    "רועה גרמני": {"risks": "רגישות במערכת העיכול ובעיות מפרק ירך.", "focus": ["AMYL", "WBC"]}
}

blood_db = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", 
             "cause": "עומס כלייתי, התייבשות או בעיה בזרימת דם.", "rec": "מזון רפואי Renal."},
    "EOS": {"name": "אאוזינופילים (אלרגיה)", "min": 0.1, "max": 1.2, "unit": "x10³/µL", 
            "cause": "אלרגיה למזון/סביבה או טפילים.", "rec": "מזון היפו-אלרגני (Hypo)."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", 
            "cause": "פגיעה בתאי כבד או רעלים.", "rec": "מזון תומך כבד (Hepatic)."},
    "GLU": {"name": "סוכר (Glucose)", "min": 70, "max": 143, "unit": "mg/dL", 
            "cause": "סוכרת או סטרס חריף.", "rec": "מזון לניהול משקל/סוכרת."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", 
            "cause": "זיהום או דלקת.", "rec": "חיזוק חיסוני (אומגה 3)."},
    "CHOL": {"name": "כולסטרול", "min": 110, "max": 320, "unit": "mg/dL", 
             "cause": "תזונה עתירת שומן.", "rec": "מזון דל שומן (Low Fat)."},
    "AMYL": {"name": "עמילאז (לבלב)", "min": 500, "max": 1500, "unit": "U/L", 
             "cause": "דלקת בלבלב או קושי בעיכול.", "rec": "מזון Gastrointestinal."},
    "BUN": {"name": "אוריאה (Urea)", "min": 7, "max": 27, "unit": "mg/dL", 
            "cause": "תפקוד כלייתי ירוד או עודף חלבון.", "rec": "מזון מופחת חלבון."}
}

def extract_data(image):
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config)
    clean_text = re.sub(r'[^a-zA-Z0-9.\s:]', ' ', text)
    results = {}
    for marker in blood_db.keys():
        pattern = rf"{marker}.*?(\d+\.?\d*)"
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            results[marker] = float(match.group(1))
    return results

# ממשק משתמש
st.set_page_config(page_title="Foodels Vet-Scan Pro", layout="wide")

st.sidebar.header("🐾 פרופיל הכלב")
dog_name = st.sidebar.text_input("שם הכלב:", "באדי")
dog_breed = st.sidebar.selectbox("בחר גזע:", list(breed_data.keys()) + ["מעורב/אחר"])
dog_age = st.sidebar.number_input("גיל (שנים):", 0.1, 25.0, 5.0)
dog_weight = st.sidebar.number_input("משקל (ק\"ג):", 0.1, 100.0, 5.0)

st.title(f"🐾 דו\"ח פיענוח עבור {dog_name}")
st.write(f"**פודלס באר שבע** | גזע: {dog_breed} | משקל: {dog_weight} ק\"ג")

if dog_breed in breed_data:
    st.info(f"🧬 **מידע גנטי ל{dog_breed}:** {breed_data[dog_breed]['risks']}")

uploaded_file = st.file_uploader("העלה צילום בדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=300)
    
    with st.spinner("מנתח..."):
        data = extract_data(img)
    
    if data:
        st.success("הפיענוח הושלם!")
        whatsapp_msg = f"היי! זה סיכום בדיקת הדם של *{dog_name}* ({dog_breed}) מפודלס:\n\n"
        
        for m, val in data.items():
            info = blood_db[m]
            is_issue = val > info["max"] or val < info["min"]
            is_focus = dog_breed in breed_data and m in breed_data[dog_breed]["focus"]
            color = "red" if is_issue else "green"
            
            with st.expander(f"{info['name']}: {val} ({'🚨' if is_issue else '✅'})", expanded=is_issue):
                if is_focus: st.error(f"⚠️ מדד זה קריטי במיוחד לגזע {dog_breed}!")
                st.markdown(f"### תוצאה: :{color}[{val} {info['unit']}]")
                st.write(f"**טווח תקין:** {info['min']} - {info['max']}")
                if is_issue:
                    st.warning(f"🧐 **הסבר:** {info['cause']}\n\n🛒 **המלצה:** {info['rec']}")
                    whatsapp_msg += f"📍 *{info['name']}*: {val} (חריגה). המלצה: {info['rec']}\n"
                else:
                    whatsapp_msg += f"✅ *{info['name']}*: {val} (תקין)\n"

        encoded_msg = urllib.parse.quote(whatsapp_msg)
        st.markdown(f'<a href="https://wa.me/?text={encoded_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 20px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 18px; font-weight: bold;">📲 שלח סיכום אישי לווטסאפ</button></a>', unsafe_allow_html=True)
    else:
        st.error("לא נמצאו מדדים.")
