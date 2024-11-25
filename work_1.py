import os
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate
)
from dotenv import load_dotenv

def classify_filenames(filenames: List[str], labels: List[str]) -> List[str]:
    # Load environment variables from .env file
    load_dotenv()

    # Fetch environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("BASE_URL")

    # Initialize the language model with the specified parameters
    llm = ChatOpenAI(
        model_name="gpt-4",
        openai_api_key=api_key,
        temperature=0,
        base_url=base_url
    )

    # Define the system prompt with instructions for the model
    system_prompt = """
You are an expert classifier.

Instructions:
- I will provide a FILENAME and a LIST of predefined categories.
- If the filename fits one of the predefined categories, return only the corresponding LABEL.
- If the filename does not fit any of the predefined categories, create a new, concise category, add it to the LIST, and return only the new LABEL.

Constraints:
- Your response should contain only the LABEL without any additional text or explanation.
- Do not include any prefixes like 'Label:' or 'Category:' in your response.
"""

    # Create the SystemMessagePromptTemplate with the system prompt
    system_msg_template = SystemMessagePromptTemplate.from_template(template=system_prompt)

    # Create the HumanMessagePromptTemplate for user input
    human_msg_template = HumanMessagePromptTemplate.from_template(
        template="FILENAME: {filename}\nLIST: {labels}"
    )

    # Create the ChatPromptTemplate combining system and human templates
    prompt_template = ChatPromptTemplate.from_messages(
        [system_msg_template, human_msg_template]
    )

    # Create the LLMChain with the language model and prompt
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=True
    )

    # List to store the classified labels
    classified_labels = []

    # Iterate over each filename to classify
    for filename in filenames:
        try:
            # Run the chain with the current filename and labels
            response = chain.run(
                filename=filename,
                labels=", ".join(labels)
            )

            # Print the filename and raw response from the model
            print(f"Filename: {filename}")
            print(f"Raw Response: {response}")

            # Process the response to extract the label
            label = response.strip()

            # Remove any prefixes like 'Label: ' if present
            if label.lower().startswith('label:'):
                label = label[len('label:'):].strip()

            # Add the label to the list of classified labels
            classified_labels.append(label)

            # Update labels if a new category was added
            if label not in labels:
                labels.append(label)
        except Exception as e:
            # Handle any exceptions and append 'Error' as the label
            print(f"Error processing filename {filename}: {e}")
            classified_labels.append("Error")

    return classified_labels

# Usage example
if __name__ == "__main__":
    # List of filenames to classify
    filenames = ["medical_records_2023.xlsx", "financial_report_Q1.pdf", "unknown_file.txt"]

    # Initial list of predefined labels
    labels = ["medical", "financial", "insurance plans"]

    # Call the classify_filenames function and get the classified labels
    classified_labels = classify_filenames(filenames, labels)

    # Print the final list of labels and the classification results
    print("Final labels:", labels)
    print("Classified labels:", classified_labels)
