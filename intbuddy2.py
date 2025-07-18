import streamlit as st
import asyncio
import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from data_preprocessor import clean_and_structure, json_to_documents
from parser import structure_df
from prompt import get_prompt
from pdfgen import build_pdf
# Correctly import the new generator function
from code360 import main_generator as fetch_interview_data

os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]


# --- Main Application Logic ---

# Ensure event loop exists for async operations
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Cached function to get the LLM (this is correct)
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )

# Cached function to get the embedding model (this is correct)
@st.cache_resource
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# --- Streamlit Page UI ---

st.title("🔍 RAG Q&A Chatbot for Interview Insights")

# User inputs
company = st.text_input("Enter Company Name", "Microsoft")
role = st.text_input("Enter Role", "SDE-1")
pages = st.number_input("Number of Pages to Scrape", min_value=1, max_value=10, value=1)

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

# --- CHANGE: This is the completely new logic for the button ---
if st.button("Load & Build Chatbot"):
    # Placeholders for dynamic progress text
    info_placeholder = st.empty()
    progress_placeholder = st.empty()
    df = None

    with st.spinner("Initializing scraper..."):
        # Call the generator function
        scraper_generator = fetch_interview_data(company, role, pages)

        # Iterate through the yielded updates from the scraper
        for result in scraper_generator:
            if result.get('status') == 'info':
                info_placeholder.info(result['message'])
            elif result.get('status') == 'progress':
                # Update the progress text, e.g., "Scraped 4/10"
                progress_placeholder.text(f"Scraped {result['current']}/{result['total']}")
            elif result.get('status') == 'complete':
                # The final result is the DataFrame
                df = result['data']
                break # Exit loop once data is complete

    # --- Process the data after scraping is finished ---
    if df is not None and not df.empty:
        # Clear the progress text and show a final message
        progress_placeholder.empty()
        info_placeholder.info(f"Scraping complete. Processing {len(df)} experiences...")

        with st.spinner("Embedding data and building chatbot..."):
            # This logic was previously in the cached function
            raw_text = df['description'].str.cat(sep=' ')
            structured = clean_and_structure(raw_text)
            chunks = json_to_documents(structured)
            docs = [Document(page_content=chunk) for chunk in chunks]
            embeddings = get_embeddings()
            vs = FAISS.from_documents(docs, embeddings)

            # Store results in session state
            st.session_state.df = df
            st.session_state.company = company
            st.session_state.role = role
            custom_prompt = get_prompt()
            st.session_state.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=get_llm(),
                retriever=vs.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": custom_prompt}
            )
        st.success(f"Chatbot ready with {len(df)} interview experiences ✅")
        st.balloons()
        # Clear the info message for a clean UI
        info_placeholder.empty()

    elif df is not None and df.empty:
        st.warning("Scraping finished, but no interview data was found for the given criteria.")
    else:
        st.error("Scraping failed to start or complete. Please check your inputs or the scraper function.")


# --- Chat Interface and PDF Generation (These sections remain unchanged) ---

if st.session_state.qa_chain:
    # Display previous messages
    for user_q, bot_a in st.session_state.chat_history:
        st.chat_message("user").write(user_q)
        st.chat_message("assistant").write(bot_a)

    if prompt := st.chat_input("Ask a question"):
        if prompt.lower().strip() in ["exit", "quit", "bye"]:
            st.success("🧹 Ending session. Cache and chat history cleared.")
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()

        st.chat_message("user").write(prompt)
        with st.spinner("Thinking..."):
            result = st.session_state.qa_chain({
                "question": prompt,
                "chat_history": st.session_state.chat_history
            })
            answer = result["answer"]
            st.session_state.chat_history.append((prompt, answer))
            st.chat_message("assistant").write(answer)

    st.markdown("---")
    if st.button("📄 Generate PDF from Interviews"):
        if "df" in st.session_state and st.session_state.df is not None:
            with st.spinner("Generating PDF with summaries..."):
                final_struct = structure_df(st.session_state.df)
                llm = get_llm()
                pdf_bytes = build_pdf(
                    final_struct,
                    llm,
                    st.session_state.company,
                    st.session_state.role
                )
                st.success("PDF generated successfully! 📄")
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name="interview_summary.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Please load and build the chatbot first.")