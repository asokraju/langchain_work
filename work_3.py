import os
import pandas as pd
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)
from dotenv import load_dotenv
import logging
from langchain.globals import set_verbose, set_debug
set_verbose(False)
# Set the logging level to WARNING to suppress INFO-level logs
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

def classify_filenames(
    filenames: List[str],
    labels_dict: Dict[str, str],
    default_label: str = "Others"
) -> List[str]:
    """
    Classifies filenames into labels based on their names.

    Args:
        filenames (List[str]): List of filenames to classify.
        labels_dict (Dict[str, str]): Dictionary with labels as keys and descriptions as values.
        default_label (str, optional): Default label for unmatched filenames. Defaults to "Others".

    Returns:
        List[str]: List of labels assigned to each filename.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Fetch environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("BASE_URL")

    # Initialize the language model with the specified parameters
    llm = ChatOpenAI(
        model_name="gpt-4-32k-0613",
        openai_api_key=api_key,
        temperature=0,
        base_url=base_url
    )

    # Prepare the labels and descriptions for the prompt
    labels = list(labels_dict.keys())
    descriptions = [f"{label}: {description}" for label, description in labels_dict.items()]
    labels_with_descriptions = "\n".join(descriptions)

    # Define the system prompt with instructions for the model
    system_prompt = f"""
You are an expert classifier working with a Medical Insurance company.

Instructions:
- I will provide a FILENAME and a LIST of predefined categories with their DESCRIPTIONS.
- Assign the FILENAME to the most appropriate LABEL from the LIST.
- Use the DESCRIPTIONS to make the best decision.
- If the FILENAME does not clearly fit any LABEL, assign it to the default category '{default_label}'.
- Only choose '{default_label}' if the FILENAME does not fit any other category.

Constraints:
- Your response should contain only the LABEL without any additional text or explanation.
- Do not create new labels.
- Do not include any prefixes like 'Label:' or 'Category:' in your response.

LIST of LABELS and DESCRIPTIONS:
{labels_with_descriptions}
"""

    # Create the SystemMessagePromptTemplate with the system prompt
    system_msg_template = SystemMessagePromptTemplate.from_template(template=system_prompt)

    # Create the HumanMessagePromptTemplate for user input
    human_msg_template = HumanMessagePromptTemplate.from_template(
        template="FILENAME: {filename}"
    )

    # Create the ChatPromptTemplate combining system and human templates
    prompt_template = ChatPromptTemplate.from_messages(
        [system_msg_template, human_msg_template]
    )

    # Create the LLMChain with the language model and prompt
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=False
    )

    # List to store the classified labels
    classified_labels = []

    # Iterate over each filename to classify
    for filename in filenames:
        try:
            # Run the chain with the current filename
            response = chain.run(
                filename=filename
            )

            # Process the response to extract the label
            label = response.strip()

            # Remove any prefixes like 'Label: ' if present
            if label.lower().startswith('label:'):
                label = label[len('label:'):].strip()

            # If the label is not in the predefined labels, assign default_label
            if label not in labels:
                label = default_label

            # Add the label to the list of classified labels
            classified_labels.append(label)

        except Exception as e:
            # Handle any exceptions and append 'Error' as the label
            print(f"Error processing filename {filename}: {e}")
            classified_labels.append("Error")

    return classified_labels

# Additional code to work with pandas DataFrame
if __name__ == "__main__":
    # Define the bins dictionary with labels and descriptions
    bins = {
        "Financial": "Documents directly related to the company's internal finances, including financial transactions and internal financial reports.",
        "LegalCompliance": "Documents related to legal matters, legislation, and compliance with regulations, including privacy policies, grievance procedures, investigations, non-compliance reports, and other regulatory affairs within the insurance industry.",
        "AdminHR": "Documents pertaining to administrative tasks and human resource management, including employee records, HR policies, staff insurance plans, payroll, personal information updates, and other internal administrative matters. This also encompasses general business activities, branding guidelines, education and research, government programs, public safety measures, entertainment activities, shopping information, travel policies, directory services, and documents related to natural resources.",
        "TechCommCustomerService": "Documents related to technological systems, system infrastructure, database management, website updates, and system management. This includes customer service interactions, support tickets, service policies, postal and communication activities, translation services, and documents that encountered errors during processing or require verification.",
        "InsurancePoliciesBenefits": "Documents related to insurance policies and benefits, including coverage details, benefit summaries, policy applications, endorsements, claims processing, provider payments, and provider registry information. This encompasses all documentation essential for managing insurance policies and benefits offered to clients.",
        "HealthcareMedical": "Documents concerning medical and healthcare information, including medical insurance claims, medical reports, healthcare policies, health programs, wellness initiatives, and healthcare guidance. This also includes mental health documents such as assessments, therapy sessions, crisis intervention, psychological evaluations, quality management programs, and clinical coding relevant to healthcare services.",
        "Others": "Documents that do not fit into any of the above categories."
    }

    # Create a sample DataFrame with a 'file names' column
    df = pd.DataFrame({
        'file names': [
            "financial_statement_Q3.pdf",
            "employee_handbook.docx",
            "system_error_log.txt",
            "patient_medical_report_2023.xlsx",
            "insurance_policy_updates.pdf",
            "legal_compliance_audit.doc",
            "random_notes_about_events.txt",
            "customer_service_feedback.csv",
            "company_brand_guidelines.pptx",
            "unknown_document.xyz"
        ]
    })

    # Extract the filenames from the DataFrame
    filenames = df['file names'].tolist()

    # Classify the filenames using the classify_filenames function
    classified_labels = classify_filenames(filenames, bins, default_label="Others")

    # Add the classified labels as a new column in the DataFrame
    df['LLM_label'] = classified_labels

    # Print the updated DataFrame
    print(df)
