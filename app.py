import streamlit as st
import requests
import json
import pandas as pd
import textwrap

# ------------------- Config -------------------
HF_API_URL = "https://api-inference.huggingface.co/models/YOUR_USERNAME/YOUR_MODEL"
HF_API_TOKEN = "YOUR_HUGGINGFACE_TOKEN"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

CHOICES = {"Almost Never": 1, "Sometimes": 2, "Often": 3}

QUESTIONS = [
    "I read the question entirely before I start the solving process.",
    "I identify and highlight the key requirements, inputs, outputs, and constraints.",
    "I rephrase/summarize the question in my own words and identify the main points.",
    "I create specific input examples and manually work through them before coding.",
    "I break down the problem into smaller, achievable sub-goals.",
    "I estimate the algorithm by recognizing patterns like repetition or conditionals.",
    "I sketch out the algorithm or plan the solution before coding.",
    "I revise and execute the designed algorithm systematically.",
    "I monitor the implementation to stay on track.",
    "I pay attention to avoid negligent mistakes during implementation.",
    "I verify intermediate results during problem solving.",
    "I monitor the ongoing program implementation process.",
    "I check if the algorithm fits the data constraints.",
    "I confirm the final implementation is correct.",
    "I refer to the problem statement to verify solution coverage.",
    "I reflect on similar problems and evaluate efficiency/accuracy."
]

# ------------------- Helpers -------------------
def collect_metacognitive_vector():
    vector = []
    for i, q in enumerate(QUESTIONS, 1):
        choice = st.selectbox(f"Q{i}. {q}", list(CHOICES.keys()), key=f"q{i}")
        vector.append(CHOICES[choice])
    return vector

def generate_feedback(metacog_vector, problem, student_code, expected_code):
    payload = {
        "inputs": f"<PROBLEM>{problem}</PROBLEM> "
                  f"<STUDENTCODE>{student_code}</STUDENTCODE> "
                  f"<EXPECTEDCODE>{expected_code}</EXPECTEDCODE>"
                  f"<METACOG>{json.dumps(metacog_vector)}</METACOG>"
    }
    response = requests.post(HF_API_URL, headers=HEADERS, json=payload)
    try:
        result = response.json()
        if isinstance(result, list):
            return result[0]['generated_text']
        return result
    except Exception as e:
        return f"⚠️ Error generating feedback: {e}"

# ------------------- UI -------------------
st.title("🧠 Metacognitive Feedback Tutor")

# Step 1: Questionnaire
st.header("Step 1: Metacognitive Questionnaire")
with st.form("questionnaire_form"):
    metacog_vector_input = collect_metacognitive_vector()
    submitted = st.form_submit_button("Submit Questionnaire")

if submitted:
    st.session_state["metacog_vector"] = metacog_vector_input
    st.session_state["submitted_questionnaire"] = True

# Step 2: Problem + Step 3: Code
if st.session_state.get("submitted_questionnaire", False):

    # Safe retrieval of vector
    metacog_vector = st.session_state.get("metacog_vector", [])

    with st.expander("📊 View Your Metacognitive Vector"):
        vector_df = pd.DataFrame({
            'Question': [f"Q{i+1}" for i in range(16)],
            'Response Score': metacog_vector
        })
        st.dataframe(vector_df, use_container_width=True)
        st.markdown("### Your Metacognitive Vector")

    st.success("✅ Questionnaire submitted. Now attempt the problem.")
    st.header("Step 2: Problem - Emma’s Workshop")
    problem = (
        "Emma has a small workshop where she organizes items on shelves. Each item has a unique weight. "
        "To balance the shelves and make the system efficient, she wants to arrange the items in ascending order of weight. "
        "However, she can only swap the positions of two items at a time. Your task is to return the minimum number of swaps "
        "required to sort the array of item weights.\n\n"
        "Function Signature:\n"
        "def rearrangeWorkshop(items: List[int]) -> int\n\n"
        "Example:\n"
        "Input: [2, 5, 3, 1] → Output: 2\n"
        "Explanation: One way is swap 5 with 1 → [2, 1, 3, 5], then 2 with 1 → [1, 2, 3, 5].\n\n"
        "Input: [3, 4, 2, 5, 1] → Output: 2"
    )
    st.markdown(f"```markdown\n{problem}\n```")

    st.header("Step 3: Write Your Solution")
    student_code = st.text_area("✍️ Write your function below:", height=250, key="studentcode")

    # Button to submit code
    if st.button("🚀 Submit Code"):
        if not student_code.strip():
            st.warning("⚠️ Please enter your code.")
        else:
            st.session_state["student_code"] = student_code
            st.session_state["problem"] = problem

            st.info("💬 Generating feedback based on your solution and questionnaire...")

            expected_code = """def getswaps(d):
    swap = 0
    for x in d.keys():
        y = d[x]
        while x != y:
            swap += 1
            d[x] = d[y]
            d[y] = y
            y = d[x]
    return swap

def rearrangeWorkshop(arr):
    arrs = sorted(arr)
    d1 = {}
    d2 = {}
    for i in range(len(arr)):
        d1[arr[i]] = arrs[i]
        d2[arr[i]] = arrs[len(arr) - 1 - i]
    return min(getswaps(d1), getswaps(d2))"""

            feedback = generate_feedback(
                st.session_state["metacog_vector"],
                st.session_state["problem"],
                student_code,
                expected_code
            )

            st.session_state["feedback"] = feedback

    # Display feedback if available
    if "feedback" in st.session_state:
        st.subheader("📘 Tutor Feedback")
        st.markdown(f"```markdown\n{textwrap.fill(str(st.session_state['feedback']), 90)}\n```")