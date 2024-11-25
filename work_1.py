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

    # Set environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("BASE_URL")

    # Initialize the language model
    llm = ChatOpenAI(
        model_name="gpt-4-32k-0613",
        openai_api_key=api_key,
        temperature=0,
        base_url=base_url
    )

    # Define the system prompt
    system_prompt = """
    You are an expert classifier. I am providing a FILENAME and a LIST.
    1. If the filename fits one of the predefined categories in the LIST, return the corresponding LABEL.
    2. If the filename does not fit any of the predefined categories, create a new, concise category and add it to the LIST.
    Then, return the new category as the LABEL.
    """

    # Create the SystemMessagePromptTemplate
    system_msg_template = SystemMessagePromptTemplate.from_template(template=system_prompt)

    # Create the HumanMessagePromptTemplate
    human_msg_template = HumanMessagePromptTemplate.from_template(template="FILENAME: {filename}\nLIST: {labels}")

    # Create the ChatPromptTemplate
    prompt_template = ChatPromptTemplate.from_messages(
        [system_msg_template, human_msg_template]
    )

    # Create the chain
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        verbose=True
    )

    # Store the results
    classified_labels = []

    # Classify each filename
    for filename in filenames:
        try:
            response = chain.run(
                filename=filename,
                labels=", ".join(labels)
            )
            print(f"Filename: {filename}")
            print(f"Label: {response}")
            label = response.strip()
            classified_labels.append(label)
            # Update labels if a new category was added
            if label not in labels:
                labels.append(label)
        except Exception as e:
            print(f"Error processing filename {filename}: {e}")
            classified_labels.append("Error")

    return classified_labels

# Usage example
if __name__ == "__main__":
    filenames = ["medical_records_2023.xlsx", "financial_report_Q1.pdf", "unknown_file.txt"]
    labels = ["medical", "financial", "insurance plans"]
    classified_labels = classify_filenames(filenames, labels)
    print("Final labels:", labels)
    print("Classified labels:", classified_labels)
