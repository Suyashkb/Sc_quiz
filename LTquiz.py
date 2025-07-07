import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Helpers ---

@st.cache_resource
def get_gsheet():
    """Connect to Google Sheets using Streamlit secrets."""
    creds = Credentials.from_service_account_info(
        st.secrets["google_sheets"], scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(st.secrets["sheet_id"]).sheet1

# Set up the Streamlit page
st.set_page_config(page_title="Self-Compassion Test", layout="centered")

# Get the Google Sheet connection
sheet = get_gsheet()

# --- Questionnaire Setup ---
questions = [
    "Q1. I try to be loving towards myself when I’m feeling emotional pain.",
    "Q2. When I’m going through a very hard time, I give myself the caring and tenderness I need.",
    "Q3. I’m kind to myself when I’m experiencing suffering.",
    "Q4. I’m tolerant of my own flaws and inadequacies.",
    "Q5. I try to be understanding and patient towards those aspects of my personality I don't like.",
    "Q6. I’m disapproving and judgmental about my own flaws and inadequacies.",
    "Q7. When times are really difficult, I tend to be tough on myself.",
    "Q8. I’m intolerant and impatient towards those aspects of my personality I don't like.",
    "Q9. When I see aspects of myself that I don’t like, I get down on myself.",
    "Q10. I can be a bit cold-hearted towards myself when I'm experiencing suffering.",
    "Q11. When things are going badly for me, I see the difficulties as part of life that everyone goes through.",
    "Q12. When I'm down, I remind myself that there are lots of other people in the world feeling like I am.",
    "Q13. When I'm down, I remind myself that there are lots of other people in the world feeling like I am.",
    "Q14. I try to see my failings as part of the human condition.",
    "Q15. When I think about my inadequacies, it tends to make me feel more separate and cut off from the rest of the world.",
    "Q16. When I’m feeling down, I tend to feel like most other people are probably happier than I am.",
    "Q17. When I’m really struggling, I tend to feel like other people must be having an easier time of it.",
    "Q18. When I fail at something that's important to me, I tend to feel alone in my failure.",
    "Q19. When something upsets me I try to keep my emotions in balance.",
    "Q20. When something painful happens I try to take a balanced view of the situation.",
    "Q21. When I fail at something important to me I try to keep things in perspective.",
    "Q22. When I'm feeling down I try to approach my feelings with curiosity and openness.",
    "Q23. When I’m feeling down I tend to obsess and fixate on everything that’s wrong.",
    "Q24. When I fail at something important to me I become consumed by feelings of inadequacy.",
    "Q25. When something upsets me I get carried away with my feelings.",
    "Q26. When something painful happens I tend to blow the incident out of proportion."
]

# Likert scale options and their scoring
likert_options = ["Never", "Rarely", "Sometimes", "Often", "Almost Always"]
likert_score = {
    "Never": 1, "Rarely": 2, "Sometimes": 3, "Often": 4, "Almost Always": 5
}

# Indices of questions that need to be reverse-scored (0-based)
# These correspond to Self-Judgment, Isolation, and Over-Identification items.
reverse_score_indices = set(list(range(5, 10)) + list(range(14, 18)) + list(range(22, 26)))

# Define the three main sections and their corresponding question indices (0-based)
section_indices = {
    "Section 1": list(range(0, 10)),  # Self-Kindness vs. Self-Judgment
    "Section 2": list(range(10, 18)), # Common Humanity vs. Isolation
    "Section 3": list(range(18, 26))  # Mindfulness vs. Over-Identification
}

# --- Streamlit Pages ---

# Initialize page state
if 'page' not in st.session_state:
    st.session_state.page = 1

# Page 1: Welcome and User Info
if st.session_state.page == 1:
    st.title("Welcome to the Self-Compassion Test")
    st.write("This questionnaire measures the different ways you might act towards yourself in difficult times. Please read each statement carefully and select the option that best describes you.")
    
    with st.form("user_info_form"):
        name = st.text_input("Enter your name")
        university = st.text_input("Enter your School/University")
        submitted_info = st.form_submit_button("Start Questionnaire")
        
        if submitted_info:
            if name and university:
                st.session_state.name = name
                st.session_state.university = university
                st.session_state.page = 2
                st.rerun()
            else:
                st.warning("Please fill in all fields before starting.")

# Page 2: Questionnaire
elif st.session_state.page == 2:
    st.title("Self-Compassion Questionnaire")
    responses = {}
    with st.form("questionnaire_form"):
        for idx, q in enumerate(questions):
            responses[f"Q{idx+1}"] = st.radio(q, likert_options, key=f"q{idx}", index=None, horizontal=True)
        submitted = st.form_submit_button("Submit & See Your Results")

        if submitted:
            if any(val is None for val in responses.values()):
                st.warning("Please answer all questions before submitting.")
            else:
                # --- SCORING LOGIC ---
                
                # 1. Convert all text responses to scores, reversing the negative ones.
                processed_scores = []
                for idx, response_text in enumerate(responses.values()):
                    score = likert_score[response_text]
                    if idx in reverse_score_indices:
                        # Reverse the score (1->5, 2->4, 3->3, 4->2, 5->1)
                        processed_scores.append(6 - score)
                    else:
                        processed_scores.append(score)

                # 2. Calculate the combined average for each of the three sections.
                section_results = {}
                for section_name, indices in section_indices.items():
                    # Get all the processed scores for this section
                    section_scores = [processed_scores[i] for i in indices]
                    avg_score = sum(section_scores) / len(section_scores)
                    
                    # 3. Determine level and color based on the combined average
                    level, color = "", ""
                    if avg_score < 2:
                        level, color = "Very Low", "Yellow"
                    elif avg_score < 3:
                        level, color = "Low", "Blue"
                    elif avg_score < 4:
                        level, color = "Medium", "Pink"
                    elif avg_score < 4.5:
                        level, color = "High", "Green"
                    else:
                        level, color = "Very High", "Orange"

                    section_results[section_name] = {
                        "average": round(avg_score, 2),
                        "level": level,
                        "color": color
                    }

                # Save raw text responses to Google Sheet
                try:
                    sheet.append_row([st.session_state.name, st.session_state.university] + list(responses.values()))
                except Exception as e:
                    st.error(f"Could not save data to Google Sheet. Error: {e}")

                st.session_state.section_results = section_results
                st.session_state.page = 3
                st.rerun()

# Page 3: Results Display
elif st.session_state.page == 3:
    st.balloons()
    st.title("Thank You for Completing the Test!")
    st.header("Your Self-Compassion Profile")
    st.write("Below are your scores for the three core components of self-compassion. A higher score indicates a greater tendency towards being self-compassionate in that area.")

    color_map = {
        "Yellow": "#FFE35A", 
        "Blue": "#96C9DC",
        "Pink": "#FCD3DE",
        "Green": "#C8EDC7",
        "Orange": "#FFA845"
    }

    results = st.session_state.section_results
    
    for section_name, details in results.items():
        st.markdown(
            f"""
            <div style='background-color:{color_map[details["color"]]};
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        margin-bottom: 20px;'>
                <h3 style='margin:0; color:#333; font-weight:bold;'>{section_name}</h3>
                <p style='margin:10px 0 0 0; color:#333; font-size:2em; font-weight:bold;'>{details["average"]}</p>
                <p style='margin:0; color:#555;'>Level: {details["level"]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("Take the Test Again"):
        # Clear specific session state keys to reset the quiz
        keys_to_clear = ['page', 'name', 'university', 'section_results']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()