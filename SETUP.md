## Setup Instructions  
  
1. **Clone the repository**  
    ```sh  
    git clone https://github.com/your-username/AzureOpenAI-ResearchPaperAnalyzer.git  
    cd AzureOpenAI-ResearchPaperAnalyzer  
    ```  
  
2. **Install and Configure a virtual python environment**  

**Option 1: VENV**

- *Create virtual directory*: From the project directory, run: `python -m venv .venv`
- *Activate the environment*: Run: `source .venv/bin/activate`
- *Install the dependencies*: Run: `pip install -r requirements.txt`

**Option 2: Conda**

- Download Miniconda from the [official website](https://docs.conda.io/en/latest/miniconda.html).  
- Follow the installation instructions for your operating system.  
- *Create Conda environment*: From the project directory, run: `conda create -n research-paper-analyzer python=3.11`
- *Activate the environment*: run:  `conda activate research-paper-analyzer`
- *Install Dependencies*: run: `pip install -r requirements.txt`

3. **Set up environment file**  
- Create a `.env` file in the root directory of the repository and add your Azure OpenAI API key and endpoint (and any others you might want):  
```sh
AZURE_OPENAI_API_KEY=your_api_key_here  
AZURE_OPENAI_ENDPOINT=https://<your_resource_name>.openai.azure.com  
```  


## IDE Setup Instructions for contributing code

If you plan on writing code and contributing to this repo, then install an IDE like VSCode.

1. **Download and Install Visual Studio Code**  
    - Download Visual Studio Code from the [official website](https://code.visualstudio.com/).  
    - Follow the installation instructions for your operating system.  
  
2. **Open the Project in Visual Studio Code**  
    - Open Visual Studio Code.  
    - Click on `File > Open Folder` and select the `AzureOpenAI-ResearchPaperAnalyzer` folder.
  
3. **Set Up a Conda Environment in Visual Studio Code**  
    - Open the Command Palette by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).  
    - Type `Python: Create Environment` and select it.  
    - Choose either `venv` or `Conda` as the environment type.  
    - Select `Python 3.x` (ensure it matches the version you have installed).
    - Make sure to tick the option to 'install dependencies' from the requirements file
    - [If conda] Name your environment (e.g., `research-paper-analyzer`).  
    - Visual Studio Code will create the environment and install the necessary dependencies.  
