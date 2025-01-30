# FileConverter  
  
## Overview  
The **File Converter** project is designed to facilitate the conversion of various file types (e.g., PPTX, DOCX, PDF, JPG, JPEG, PNG) into markdown format. This tool leverages the `markitdown` library https://github.com/microsoft/markitdown to perform the conversions and saves the results in markdown files. The script automates the process of identifying supported file types in a directory, converting them, and saving the converted content as markdown files.  

## The Python Notebook
The code you are working with is avaiable in [Convert Files Notebook](./convertfiles.ipynb). Use this to help you get started. Save the PDFS you want to convert in the same directory as this notebook.

## Install Markitdown
```
 %pip install markitdown
```
## Step-by-Step Walkthrough  
  
1. **Import necessary libraries**  
    ```python  
    from markitdown import MarkItDown  
    from pathlib import Path  
    from openai import AzureOpenAI  
    import os  
    from dotenv import load_dotenv  
    from IPython.display import Markdown, display, Image  
    ```  
    - `markitdown`: Used for converting various file types to markdown.  
    - `pathlib`: Used for handling file paths.  
    - `openai`: Used for interacting with Azure OpenAI.  
    - `os`: Used for accessing environment variables.  
    - `dotenv`: Used for loading environment variables from a `.env` file.  
    - `IPython.display`: Used for displaying markdown and images in Jupyter Notebooks.  
  
2. **Load environment variables**  
    ```python  
    load_dotenv()  
    ```  
    - This loads the environment variables from the `.env` file into the script.  
  
3. **Initialize MarkItDown and set supported extensions**  
    ```python  
    md = MarkItDown()  
    supported_extensions = ('.pptx', '.docx', '.pdf', '.jpg', '.jpeg', '.png')  
    ```  
    - `md`: Instance of the MarkItDown class.  
    - `supported_extensions`: Tuple containing the file extensions supported for conversion.  
  
4. **Identify files to convert**  
    ```python  
    files_to_convert = [f for f in os.listdir('.') if f.lower().endswith(supported_extensions)]  
    ```  
    - `files_to_convert`: List of files in the current directory with supported extensions.  
  
5. **Convert files and save as markdown**  
    ```python  
    for file in files_to_convert:  
        print(f"\nConverting {file}...")  
        try:  
            md_file = os.path.splitext(file)[0] + '.md'  
            result = md.convert(file)  
            with open(md_file, 'w', encoding="utf-8") as f:  
                f.write(result.text_content)  
            print(f"Successfully converted {file} to {md_file}")  
        except Exception as e:  
            print(f"Error converting {file}: {str(e)}")  
    print("\nAll conversions completed!")  
    ```  
    - Loops through the list of files to convert.  
    - For each file, attempts to convert it to markdown using MarkItDown.  
    - Saves the converted content to a new markdown file.  
    - Prints the status of each conversion.  
  
## Important Notes:  
- Ensure the hardcoded API key is removed from the script before committing to the repository.  
- Make sure to update the `.env` file with your own Azure OpenAI credentials if you are using Azure OpenAI services.  
- Customize the supported extensions and conversion process as needed to better suit your requirements.  