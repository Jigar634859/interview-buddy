# Interview Insights RAG Chatbot

This project is an advanced tool for job seekers that scrapes interview experiences, provides a conversational Q&A interface using a RAG (Retrieval-Augmented Generation) chatbot, and generates a professional PDF summary of the findings.

The application is a self-contained Streamlit app that handles both the web scraping and the user-facing AI components.

## Architecture Overview

The project is a monolithic Streamlit application that performs two main functions:

1.  **Live Web Scraping:** A robust web scraper built with Python and Selenium is integrated directly into the app. When a user provides a company and role, the scraper launches a headless browser, navigates to `naukri.com/code360`, applies the necessary filters, and scrapes the interview experiences in real-time.

2.  **Frontend & AI:** The user-friendly web interface is built with Streamlit. After the scraping is complete, the app processes the text and loads it into a FAISS vector store. A conversational chatbot, powered by Google Gemini and LangChain, allows users to ask questions about the interview process. Finally, the app can generate a detailed PDF report summarizing the key insights.

---

## Key Technologies Used

-   **Frontend:** Streamlit
-   **Web Scraping:** Selenium
-   **AI & Language Models:**
    -   LangChain (for RAG pipeline orchestration)
    -   Google Gemini (as the core language model)
    -   FAISS (for efficient vector storage and similarity search)
-   **PDF Generation:** ReportLab
-   **Data Handling:** Pandas

---

## Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

-   Python 3.10+
-   Git
-   A Google API Key with the Gemini API enabled

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
```

### 2. Set Up the Streamlit App

1.  **Create a Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a Secrets File:**
    -   Create a new folder in the root directory named `.streamlit`.
    -   Inside that folder, create a new file named `secrets.toml`.
    -   Add your Google API key to this file:
        ```toml
        # .streamlit/secrets.toml
        GOOGLE_API_KEY = "your_google_api_key_here"
        ```

---

## How to Run the Application

1.  **Activate your virtual environment:**
    ```bash
    source venv/bin/activate
    ```

2.  **Run the Streamlit app:**
    ```bash
    streamlit run your_app_name.py
    ```
    The application will open in your web browser.

3.  **Using the App:**
    -   Enter a company and role into the input fields.
    -   Click "Load & Build Chatbot". This will trigger the integrated Selenium scraper.
    -   Once the data is fetched and processed, you can interact with the chatbot.
    -   Click "Generate PDF from Interviews" to get a downloadable summary report.

---

## Project Structure

```
.
├── .streamlit/
│   └── secrets.toml      # Stores API keys for local development
├── your_app_name.py      # The main Streamlit application script
├── code360.py            # The Python code for the Selenium scraper
├── data_preprocessor.py  # Functions for cleaning and structuring text
├── parser.py             # Functions to parse scraped data
├── pdfgen.py             # Logic for generating the PDF report
├── prompt.py             # Contains the prompt template for the LLM
├── requirements.txt      # Python dependencies for the Streamlit app
├── packages.txt          # System-level dependencies for cloud deployment
└── README.md             # This file
```
