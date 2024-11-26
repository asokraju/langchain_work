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

def classify_filenames(
    filenames: List[str],
    labels_dict: Dict[str, str],
    default_label: str = "other"
) -> List[str]:
    """
    Classifies filenames into labels based on their names and updates label descriptions.

    Args:
        filenames (List[str]): List of filenames to classify.
        labels_dict (Dict[str, str]): Dictionary with labels as keys and descriptions as values.
        default_label (str, optional): Default label for unmatched filenames. Defaults to "other".

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
You are an expert classifier.

Instructions:
- I will provide a FILENAME and a LIST of predefined categories with their DESCRIPTIONS.
- Assign the FILENAME to the most appropriate LABEL from the LIST.
- If the FILENAME does not clearly fit any LABEL, assign it to the default category '{default_label}'.

Constraints:
- Your response should contain only the LABEL without any additional text or explanation.
- Do not create new labels.
- Do not include any prefixes like 'Label:' or 'Category:' in your response.
- Use the DESCRIPTIONS to make a better decision.

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

            # Update the description of the label using the filename
            if label != default_label:
                old_description = labels_dict[label]
                # Use the model to generate an improved description
                new_description = update_label_description(llm, label, old_description, filename)
                labels_dict[label] = new_description

        except Exception as e:
            # Handle any exceptions and append 'Error' as the label
            print(f"Error processing filename {filename}: {e}")
            classified_labels.append("Error")

    return classified_labels

def update_label_description(llm, label, old_description, filename):
    """
    Updates the description of a label based on a new filename.

    Args:
        llm: The language model instance.
        label (str): The label to update.
        old_description (str): The current description of the label.
        filename (str): The filename that has been assigned to the label.

    Returns:
        str: The updated description of the label.
    """
    # Define the prompt to update the label description
    prompt = f"""
You are an assistant helping to update the description of a category.

Current LABEL: {label}
Current DESCRIPTION: {old_description}

A new FILENAME '{filename}' has been assigned to this LABEL.

Instructions:
- Update the DESCRIPTION to include relevant information implied by the FILENAME.
- Make the DESCRIPTION concise and informative.
- Do not mention the FILENAME directly.
- Ensure the DESCRIPTION accurately reflects all types of files assigned to this LABEL.

Constraints:
- Your response should be only the updated DESCRIPTION.
"""

    # Run the model to get the updated description
    response = llm.predict(prompt).strip()

    return response

# Additional code to work with pandas DataFrame
if __name__ == "__main__":
    # Create a sample DataFrame with a 'file names' column
    df = pd.DataFrame({
        'file names': [
            "medical_records_2023.xlsx",
            "financial_report_Q1.pdf",
            "insurance_plan_details.docx",
            "patient_diagnosis_notes.txt",
            "policy_premium_rates.csv",
            "employee_benefits_overview.pptx",
            "budget_overview.txt",
            "random_notes.pdf"
        ]
    })

    # Initial dictionary of labels and their descriptions
    labels_dict = {
        "medical": "Files related to medical records and health information.",
        "financial": "Documents pertaining to financial reports and budgets.",
        "insurance plans": "Information about insurance plans and policies."
    }

    # Extract the filenames from the DataFrame
    filenames = df['file names'].tolist()

    # Classify the filenames using the classify_filenames function
    classified_labels = classify_filenames(filenames, labels_dict, default_label="other")

    # Add the classified labels as a new column in the DataFrame
    df['LLM_label'] = classified_labels

    # Print the updated DataFrame
    print(df)

    # Print the updated labels and descriptions
    print("\nUpdated Labels and Descriptions:")
    for label, description in labels_dict.items():
        print(f"{label}: {description}")
