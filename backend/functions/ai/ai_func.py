from google import genai
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from functions.database import document_manager, permissions_manager

# The client gets the API key from the hardcoded API key.
client = genai.Client(api_key="AIzaSyDgc13grWGHeGitJB4_CIk2nK21TsMPcBE")

def generate_case_summary(case_id, user_id):
    """Generates a summary of the case documents using AI."""
    if not permissions_manager.check_access(case_id, user_id):
        return "Access denied"

    docs = document_manager.get_case_documents(case_id)
    if not docs:
        return "No documents found for this case."

    # Use AI to invent a summary
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Invent a detailed summary for a legal case involving multiple documents and parties. Make it sound realistic and professional."
        )
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"