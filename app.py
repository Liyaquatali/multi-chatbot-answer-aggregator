import streamlit as st
import ollama
import re

st.set_page_config(page_title="AI Multi-Model Intelligence Lab", layout="wide")

# ---------------- CSS ----------------

st.markdown("""
<style>

body {
    background-color: #0f172a;
}

.model-card {
    background-color: #1e293b;
    padding: 18px;
    border-radius: 12px;
    height: 350px;
    overflow-y: auto;
}

.consensus-box {
    background-color: #1e293b;
    padding: 20px;
    border-radius: 12px;
}

.user-bubble {
    background-color:#1e293b;
    padding:12px;
    border-radius:10px;
    max-width:60%;
    margin-left:auto;
    text-align:right;
}

</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- SECURITY FUNCTION ----------------

def mask_sensitive_data(text):
    """
    Masks possible debit/credit card numbers.
    Example:
    1124 8811 1710 0018 -> xxxx xxxx xxxx 0018
    """

    pattern = r'\b(?:\d[ -]*?){13,16}\b'

    def replacer(match):
        raw = re.sub(r'\D', '', match.group())

        if 13 <= len(raw) <= 16:
            return "xxxx xxxx xxxx " + raw[-4:]

        return match.group()

    return re.sub(pattern, replacer, text)

# ---------------- CONSENSUS SPLITTER ----------------

def split_consensus(text):

    sections = {
        "summary": "",
        "similarities": "",
        "differences": "",
        "strengths": ""
    }

    try:
        summary_part = text.split("Similarities:")[0]
        sections["summary"] = summary_part.replace("Combined Summary:", "").strip()

        rest = text.split("Similarities:")[1]

        similarities = rest.split("Differences:")[0]
        sections["similarities"] = similarities.strip()

        rest2 = rest.split("Differences:")[1]

        differences = rest2.split("Unique Strengths:")[0]
        sections["differences"] = differences.strip()

        strengths = rest2.split("Unique Strengths:")[1]
        sections["strengths"] = strengths.strip()

    except:
        sections["summary"] = text

    return sections

# ---------------- SIDEBAR ----------------

st.sidebar.title("Chat History")

if len(st.session_state.chat_history) == 0:
    st.sidebar.caption("No conversations yet")

for i, chat in enumerate(st.session_state.chat_history):
    if st.sidebar.button(chat["prompt"][:40], key=f"history_{i}"):
        st.session_state.selected_chat = i

# ---------------- TITLE ----------------

st.title("AI Multi-Model Intelligence Lab")
st.caption("Compare responses from multiple AI models with consensus synthesis")

# ---------------- DISPLAY CHAT ----------------

for idx, chat in enumerate(st.session_state.chat_history):

    # USER MESSAGE

    with st.chat_message("user"):
        st.markdown(
            f"<div class='user-bubble'>{chat['prompt']}</div>",
            unsafe_allow_html=True
        )

    # AI MESSAGE

    with st.chat_message("assistant"):

        consensus = chat["consensus"]
        sections = split_consensus(consensus)

        st.markdown("### Consensus Intelligence Analysis")

        st.markdown(
            f"""
            <div class='consensus-box'>
            <b>Combined Summary</b><br><br>
            {sections["summary"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        toggle_key = f"thinking_{idx}"

        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = False

        if st.button("🧠 Thinking", key=f"btn_{idx}"):
            st.session_state[toggle_key] = not st.session_state[toggle_key]

        if st.session_state[toggle_key]:

            st.markdown("---")

            st.markdown("### Similarities")
            st.write(sections["similarities"])

            st.markdown("### Differences")
            st.write(sections["differences"])

            st.markdown("### Unique Strengths")
            st.write(sections["strengths"])

            st.markdown("---")
            st.markdown("### Model Responses")

            responses = chat["responses"]

            cols = st.columns(len(responses))

            for col, model in zip(cols, responses):

                with col:
                    st.markdown(f"**{model.upper()}**")

                    st.markdown(
                        f"<div class='model-card'>{responses[model]}</div>",
                        unsafe_allow_html=True
                    )

# ---------------- CHAT INPUT ----------------

prompt = st.chat_input("Ask anything...")

if prompt:

    # SECURITY MASKING
    safe_prompt = mask_sensitive_data(prompt)

    if prompt != safe_prompt:
        st.warning("Sensitive information detected and masked before AI processing.")

    responses = {}

    with st.spinner("Generating responses..."):

        responses["mistral"] = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": safe_prompt}]
        )["message"]["content"]

        responses["llama3"] = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": safe_prompt}]
        )["message"]["content"]

        responses["phi3"] = ollama.chat(
            model="phi3",
            messages=[{"role": "user", "content": safe_prompt}]
        )["message"]["content"]

        synthesis_prompt = f"""
User Question:
{safe_prompt}

Model Responses:
{responses}

Return exactly in this format:

Combined Summary:
Similarities:
Differences:
Unique Strengths:
"""

        consensus = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": synthesis_prompt}]
        )["message"]["content"]

        st.session_state.chat_history.append({
            "prompt": prompt,
            "responses": responses,
            "consensus": consensus
        })

    st.rerun()