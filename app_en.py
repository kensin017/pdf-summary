import streamlit as st
import fitz  # PyMuPDF
import openai
from openai import OpenAI
import time

# ✅ GPT 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ 페이지 설정
st.set_page_config(
    page_title="AI PDF Summarizer",
    page_icon="📄",
    layout="wide"
)

# ✅ 상단 UI
st.title("📄 AI PDF Summarizer")
st.write("Upload a PDF file and get a structured summary powered by GPT.")
st.caption("⚠️ Uploaded files are not stored. They're used only for summarization.")

# ✅ PDF 텍스트 추출
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ✅ 텍스트 나누기
def split_text_by_length(text, max_length=1000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# ✅ GPT 요약 (재시도 포함)
def summarize_text_with_retry(prompt, retries=5, wait_sec=5):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # 또는 "gpt-4o" (API 한도에 따라)
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            st.warning(f"Rate limit hit. Retrying in {wait_sec} seconds... ({attempt+1}/{retries})")
            time.sleep(wait_sec)
    return "Failed due to rate limit."

# ✅ 전체 요약 파이프라인
def summarize_large_text(text):
    chunks = split_text_by_length(text)
    partial_summaries = []

    for i, chunk in enumerate(chunks):
        st.info(f"Summarizing part {i+1} of {len(chunks)}...")
        prompt = f"""
        Summarize the following text. Extract key points and present them clearly.

        Document:
        {chunk}

        Format:
        - Summary:
        - Key Points:
        - Questions to Consider:
        """
        summary = summarize_text_with_retry(prompt)
        partial_summaries.append(summary)

    # ✅ 개별 요약 출력
    st.markdown("### 🔹 Partial Summaries")
    for i, s in enumerate(partial_summaries):
        st.markdown(f"#### 📄 Part {i+1}")
        st.text_area(label=f"Summary Part {i+1}", value=s, height=250, key=f"part_{i}")

    # ✅ 전체 요약 시도
    st.markdown("### 🔹 Final Combined Summary")
    final_prompt = f"""
    Below are partial summaries from a multi-page document.  
    Please combine them into a single, well-structured summary.

    Summaries:
    {'\n\n'.join(partial_summaries)}

    Format:
    - Full Summary:
    - Key Highlights:
    - Questions to Consider:
    """
    final_summary = summarize_text_with_retry(final_prompt)

    if "Failed" in final_summary:
        st.warning("Final summary failed. You can use the partial summaries above.")
    else:
        st.success("Final summary complete!")
        st.text_area("📋 Full Summary", final_summary, height=400)
        st.download_button(
            label="📥 Download Summary",
            data=final_summary,
            file_name="summary.txt",
            mime="text/plain"
        )

    return final_summary

# ✅ 파일 업로드 UI
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Processing PDF..."):
        extracted_text = extract_text_from_pdf(uploaded_file)
        summarize_large_text(extracted_text)
