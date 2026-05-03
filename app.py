import streamlit as st
import pytesseract
from PIL import Image
import re

# הגדרת בסיס הנתונים עם כל הפיצ'רים (אלרגיה, דלקת, כליות, כבד)
blood_db = {
    "CREA": {"name": "קריאטינין (כליות)", "min": 0.5, "max": 1.8, "unit": "mg/dL", "cat": "Kidney", 
             "rec": "חשד לעומס כלייתי. מומלץ מזון רפואי Renal ותוספי תמיכה בכליות."},
    "EOS": {"name": "אאוזינופילים (אלרגיה)", "min": 0.1, "max": 1.2, "unit": "x10³/µL", "cat": "Allergy", 
            "rec": "מדד אלרגיה גבוה. מומלץ לעבור למזון היפו-אלרגני (חלבון מפורק או דג) למשך 8 שבועות."},
    "WBC": {"name": "כדוריות דם לבנות (דלקת)", "min": 5.0, "max": 16.7, "unit": "x10³/µL", "cat": "Inflammation", 
            "rec": "סימני דלקת או זיהום. מומלץ להוסיף אומגה 3 ונוגדי חמצון לחיזוק מערכת החיסון."},
    "ALT": {"name": "אנזימי כבד (ALT)", "min": 10, "max": 125, "unit": "U/L", "cat": "Liver", 
            "rec": "עומס על הכבד. מומלץ תזונה קלה לעיכול ותוספי ניקוי רעלים (סילמרין)."}
}

def extract_from_image(image):
    # המרת תמונה לטקסט
    text = pytesseract.image_to_string(image)
    results = {}
    for marker in blood_db.keys():
        # מחפש את המדד ואת המספר שאחריו
        pattern = rf"{marker}\s*[:\-]?\s*(\d+\.?\d*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[marker] = float(match.group(1))
    return results

def get_analysis(current_data, past_data, breed):
    # פיצ'ר התאמת גזע
    if breed == "Greyhound":
        blood_db["CREA"]["max"] = 2.1
        
    report = []
    for marker, val in current_data.items():
        db = blood_db[marker]
        past_val = past_data.get(marker)
        status = "תקין ✅"
        advice = ""
        
        # זיהוי חריגה
        if val > db["max"]:
            status = "גבוה 🚨"
            advice = f"**המלצה:** {db['rec']}"
        
        # פיצ'ר ניתוח מגמות
        if past_val:
            change = ((val - past_val) / past_val) * 100
            if change > 15:
                advice += f" | 📈 **התרעת מגמה:** עלייה של {change:.1f}% מהבדיקה הקודמת."

        report.append({"name": db["name"], "val": val, "unit": db["unit"], "status": status, "advice": advice})
    return report

# ממשק המשתמש (UI)
st.set_page_config(page_title="Vet-Scan Foodels", page_icon="🐾")
st.title("🐾 Vet-Scan: מפענח הבריאות של פודלס")
st.write("סרוק את בדיקות הדם של הכלב וקבל פיענוח והמלצות תזונה מיידיות.")

# בחירת גזע (פיצ'ר קריטי)
breed = st.selectbox("בחר גזע הכלב:", ["מעורב/אחר", "Greyhound", "Poodle", "Labrador"])

# העלאת צילום
uploaded_file = st.file_uploader("צלם או העלה את טופס הבדיקה", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="הטופס שנסרק", use_container_width=True)
    
    with st.spinner("מנתח נתונים רפואיים..."):
        scanned_results = extract_from_image(img)
        
    if scanned_results:
        st.success(f"זיהיתי {len(scanned_results)} מדדים!")
        
        # הזנת נתוני עבר לניתוח מגמות
        st.write("---")
        st.write("### ניתוח מגמות (אופציונלי)")
        p_crea = st.number_input("ערך קריאטינין בבדיקה קודמת (אם יש):", value=0.0)
        
        if st.button("הפק דווח סופי"):
            past_dict = {"CREA": p_crea} if p_crea > 0 else {}
            final_report = get_analysis(scanned_results, past_dict, breed)
            
            for r in final_report:
                st.markdown(f"#### {r['name']}: {r['val']} {r['unit']} ({r['status']})")
                if r['advice']:
                    st.info(r['advice'])
                st.divider()
    else:
        st.error("לא הצלחתי לזהות מדדים. וודא שהצילום ברור וכולל את קיצורי המדדים (CREA, EOS וכד').")

st.sidebar.write("---")
st.sidebar.write("**פודלס באר שבע**")
st.sidebar.write("נחום שריג 33, רמות")