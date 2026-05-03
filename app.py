import streamlit as st
import pytesseract
from PIL import Image
import re

# הגדרת המדדים - הוספתי עוד וריאציות לשמות כדי להקל על הזיהוי
blood_db = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "rec": "חשד לעומס כלייתי. מומלץ מזון רפואי Renal."},
    "EOS": {"name": "אאוזינופילים (אלרגיה)", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "rec": "מדד אלרגיה גבוה. מומלץ מזון היפו-אלרגני."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "rec": "עומס על הכבד. מומלץ תזונה קלה לעיכול."},
    "WBC": {"name": "כדוריות דם לבנות", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "rec": "סימני דלקת. מומלץ חיזוק חיסוני."}
}

def extract_from_image(image):
    # שיפור: הוספת הגדרות למנוע ה-OCR לשיפור דיוק במספרים
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)
    
    results = {}
    # ניקוי טקסט בסיסי כדי להקל על החיפוש
    clean_text = text.replace('(', ' ').replace(')', ' ').replace('|', ' ')
    
    for marker in blood_db.keys():
        # ביטוי רגולרי גמיש יותר: מחפש את שם המדד, ואז כל תו שאינו מספר, ואז את המספר
        pattern = rf"{marker}.*?(\d+\.?\d*)"
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            results[marker] = float(match.group(1))
    
    return results, text # מחזירים גם את הטקסט הגולמי לצורך בדיקה

# ממשק המשתמש
st.set_page_config(page_title="Vet-Scan Foodels V2", page_icon="🐾")
st.title("🐾 Vet-Scan V2: מפענח הבריאות")

breed = st.selectbox("גזע הכלב:", ["מעורב", "Greyhound", "Poodle"])
uploaded_file = st.file_uploader("העלה את טופס הבדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="התמונה שהועלתה", use_container_width=True)
    
    with st.spinner("מנתח..."):
        scanned_results, raw_text = extract_from_image(img)
    
    # כפתור סודי לראות מה המערכת קראה (לצורך תיקון תקלות)
    with st.expander("ראה טקסט שנסרק (לביקורת טכנית)"):
        st.code(raw_text)
        
    if scanned_results:
        st.success(f"זיהיתי {len(scanned_results)} מדדים!")
        for marker, val in scanned_results.items():
            db = blood_db[marker]
            status = "תקין ✅" if val <= db["max"] else "גבוה 🚨"
            st.write(f"**{db['name']}**: {val} {db['unit']} ({status})")
            if val > db["max"]:
                st.warning(db["rec"])
    else:
        st.error("לא הצלחתי לזהות מדדים. נסה לוודא שהטקסט בתמונה ברור מאוד.")
