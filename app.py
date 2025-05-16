import streamlit as st
import requests
import json
import ast
import textwrap

# ------------------- Config -------------------
HF_API_URL = "https://api-inference.huggingface.co/models/YOUR_USERNAME/YOUR_MODEL"
HF_API_TOKEN = "YOUR_HUGGINGFACE_TOKEN"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

CHOICES = {"Almost Never": 0.0, "Sometimes": 0.5, "Often": 1.0}

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

def run_student_code(code, test_cases):
    namespace = {}
    try:
        exec(code, namespace)
        func = [v for k, v in namespace.items() if callable(v)][0]
        for inp, expected in test_cases:
            result = func(*inp)
            if result != expected:
                return False, (inp, result, expected)
        return True, None
    except Exception as e:
        return False, str(e)

def generate_feedback(metacog_vector, problem, student_code, expected_code):
    payload = {
        "inputs": f"<METACOG>{json.dumps(metacog_vector)}</METACOG> "
                  f"<PROBLEM>{problem}</PROBLEM> "
                  f"<STUDENTCODE>{student_code}</STUDENTCODE> "
                  f"<EXPECTEDCODE>{expected_code}</EXPECTEDCODE>"
    }
    response = requests.post(HF_API_URL, headers=HEADERS, json=payload)
    return response.json()[0]['generated_text'] if isinstance(response.json(), list) else response.json()

# ------------------- UI -------------------
st.title("🧠 Metacognitive Feedback Tutor")

# 1. Questionnaire
st.header("Step 1: Metacognitive Questionnaire")
with st.form("questionnaire_form"):
    metacog_vector = collect_metacognitive_vector()
    submitted = st.form_submit_button("Submit Questionnaire")

# 2. Problem
if submitted:
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

    # 3. Code Input
    st.header("Step 3: Write Your Solution")
    student_code = st.text_area("✍️ Write your function below:", height=250, key="studentcode")
    st.markdown("```python\n" + student_code + "\n```")
    expected_code = st.text_area("✅ (Optional) Reference implementation:", height=200)

    # 4. Test Cases Input
    st.subheader("📥 Test Cases")
    default_tests = "[(([2, 5, 3, 1],), 2), (([3, 4, 2, 5, 1],), 2)]"
    test_cases_input = st.text_area("Enter test cases:", value=default_tests)
    try:
        test_cases = ast.literal_eval(test_cases_input)
    except:
        st.error("❌ Test cases must be a list of tuples.")
        test_cases = []

    # 5. Action Buttons
    col1, col2 = st.columns(2)
    run_check = col1.button("Run & Submit")
    ask_help = col2.button("Ask for Feedback")

    # 6. Result
    if run_check or ask_help:
        if not student_code.strip():
            st.warning("⚠️ Please enter your code.")
        elif not test_cases:
            st.warning("⚠️ Please provide valid test cases.")
        else:
            passed, info = run_student_code(student_code, test_cases)
            if not passed or ask_help:
                st.info("💬 Generating feedback...")
                feedback = generate_feedback(metacog_vector, problem, student_code, expected_code)
                st.subheader("📘 Tutor Feedback")
                st.markdown(f"```markdown\n{textwrap.fill(feedback, 90)}\n```")
            else:
                st.success("🎉 All test cases passed! Great job!")

