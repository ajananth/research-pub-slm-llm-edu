# AzureOpenAI-ResearchPaperAnalyzer  
  
## Overview  
  
The **AzureOpenAI-ResearchPaperAnalyzer** project is designed to facilitate the analysis of research papers using the powerful capabilities of Azure OpenAI. The primary objective of this project is to automate the extraction and categorization of key insights from research papers written in markdown format. By leveraging Azure OpenAI's advanced natural language processing abilities, the script can:  
  
- Process markdown files of research papers.  
- Extract key insights and bullet points from the text.  
- Categorize the extracted information according to different research fields, funding sources, and affiliations.  
- Generate a summary of the paper's content and structure.  
- Format and save the results into a CSV file for easy analysis and reporting.  
  
This tool aims to save researchers significant time and effort by automating the tedious process of reading and summarizing lengthy research papers, allowing them to focus more on the critical aspects of their work. 

## The Python Notebook
The code you are working with is avaiable in [Analyze Research Papers Notebook](./analyzepapers.ipynb). Use this to help you get started. Copy the Markdown Files you just converted into the same directory as this notebook.

## Step-by-Step Walkthrough  
  
1. **Import necessary libraries**  
    ```python  
    from openai import AzureOpenAI  
    import os  
    from dotenv import load_dotenv  
    from IPython.display import Markdown, display, Image  
    import glob  
    ```  
    - `openai`: Used for interacting with Azure OpenAI.  
    - `os`: Used for accessing environment variables.  
    - `dotenv`: Used for loading environment variables from a `.env` file.  
    - `IPython.display`: Used for displaying markdown and images in Jupyter Notebooks.  
    - `glob`: Used for file pattern matching.  
  
2. **Load environment variables**  
    ```python  
    load_dotenv()  
    ```  
    - This loads the environment variables from the `.env` file into the script.  
  
3. **Set up deployment name and API client**  
    ```python  
    deployment_name = "gpt-4o-mini"  
    api_key = os.environ["AZURE_OPENAI_API_KEY"]  
    azure_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']  
    api_version = "2024-02-15-preview"  
  
    client = AzureOpenAI(  
        api_key=api_key,  
        azure_endpoint=azure_endpoint,  
        api_version=api_version  
    )  
    ```  
    - `deployment_name`: Name of the OpenAI deployment.  
    - `api_key`: API key loaded from the environment variable.  
    - `azure_endpoint`: Endpoint for the Azure OpenAI service.  
    - `api_version`: Version of the API being used.  
    - `client`: Instance of the AzureOpenAI client.  
  
4. **Load markdown files and limit to first 5**  
    ```python  
    article_files = glob.glob("*.md")  
    article_files = article_files[:5]  
    ```  
    - `article_files`: List of markdown files in the current directory.  
    - Limits the list to the first 5 markdown files.  
  
5. **Define function to split text into smaller parts**  
    ```python  
    def split_text(text, limit):  
        text_parts = []  
        current_part = ""  
        current_length = 0  
        for sentence in text.split("."):  
            if current_length + len(sentence) < limit:  
                current_part += sentence + "."  
                current_length += len(sentence)  
            else:  
                text_parts.append(current_part)  
                current_part = sentence + "."  
                current_length = len(sentence)  
        text_parts.append(current_part)  
        return text_parts  
    ```  
    - `split_text`: Splits a large text into smaller parts based on a character limit.  
    - `text`: The input text to be split.  
    - `limit`: The maximum number of characters for each part.  
  
6. **Process each markdown file and generate notes**  
    ```python  
    first_system_message = {"role": "system", "content": "You are an AI assistant that helps with creating bullet points of long research papers. ..."}  
      
    for article_file in article_files:  
        with open(article_file, 'r', encoding="utf-8") as file:  
            article = file.read()  
            chunk_size = 4000  
            article_length = len(article)  
            chunks = article_length // chunk_size  
            text_parts = split_text(article, chunk_size)  
            notes_file = article_file.replace(".md", "_notes.md")  
            with open(notes_file, 'w', encoding='utf-8') as file:  
                file.write("# Notes\n\n")  
                for i, text_part in enumerate(text_parts):  
                    completion = client.chat.completions.create(  
                        model=deployment_name,  
                        messages=[first_system_message, {"role": "user", "content": text_part}]  
                    )  
                    response = completion.choices[0].message.content  
                    file.write(f"## Part {i+1}\n\n")  
                    file.write(f"{response}\n\n")  
    ```  
    - `first_system_message`: Initial system prompt to guide the AI's response.  
    - Opens each markdown file, reads its content, and splits it into smaller parts.  
    - For each part, it generates notes using the Azure OpenAI client and writes the notes to a new markdown file.  
  
7. **Run system prompts to get final output**  
    ```python  
    article_notes = glob.glob("*_notes.md")  
    article_notes = article_notes[:2]  
  
    field_of_research_code_system_prompt = {"role": "system", "content": """You are an assistant that reviews research papers and determines their field of research. ..."""}  
    funding_sources_system_prompt = {"role": "system", "content": """You are an AI assistant that reviews research paper notes and detects information on funding. ..."""}  
    affiliations_system_prompt = {"role": "system", "content": """You are an AI assistant that reviews research paper notes and detects affiliations to the local University. ..."""}  
    csv_friendly_format_system_prompt = {"role": "system", "content": """You are an AI assistant that reviews research paper notes and formats the information into a CSV formatted data. ..."""}  
  
    with open("results.csv", 'w', encoding='utf-8') as file:  
        file.write("Article, Field of Research Code, Funding Sources, Affiliations\n")  
  
    for article_note in article_notes:  
        with open(article_note, 'r', encoding="utf-8") as file:  
            article = file.read()  
            completion = client.chat.completions.create(  
                model=deployment_name,  
                messages=[field_of_research_code_system_prompt, {"role": "user", "content": article}]  
            )  
            fieldOfResearchResult = completion.choices[0].message.content  
  
            completion = client.chat.completions.create(  
                model=deployment_name,  
                messages=[funding_sources_system_prompt, {"role": "user", "content": article}]  
            )  
            fundingSourcesResult = completion.choices[0].message.content  
  
            completion = client.chat.completions.create(  
                model=deployment_name,  
                messages=[affiliations_system_prompt, {"role": "user", "content": article}]  
            )  
            affiliationsResult = completion.choices[0].message.content  
  
            collatedResults = f"{fieldOfResearchResult}, {fundingSourcesResult}, {affiliationsResult}"  
            completion = client.chat.completions.create(  
                model=deployment_name,  
                messages=[csv_friendly_format_system_prompt, {"role": "user", "content": collatedResults}]  
            )  
            csv_friendly_format = completion.choices[0].message.content  
  
            with open("results.csv", 'a', encoding='utf-8') as file:  
                file.write(f"{csv_friendly_format}\n")  
    ```  
    - Collects and processes the notes generated for each article.  
    - Uses different system prompts to extract specific information (field of research, funding sources, affiliations).  
    - Formats the extracted information into a CSV-friendly format and writes it to `results.csv`.  
  
## Important Notes:  
- Ensure the hardcoded API key is removed from the script before committing to the repository.  
- Make sure to update the `.env` file with your own Azure OpenAI credentials.  
- Customize the system prompts as needed to better suit the research papers you are analyzing.  