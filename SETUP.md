## Setup Instructions  
  
1. **Clone the repository**  
    ```sh  
    git clone https://github.com/your-username/AzureOpenAI-ResearchPaperAnalyzer.git  
    cd AzureOpenAI-ResearchPaperAnalyzer  
    ```  
  
2. **Install Miniconda**  
    - Download Miniconda from the [official website](https://docs.conda.io/en/latest/miniconda.html).  
    - Follow the installation instructions for your operating system.  
  
3. **Set Up a Conda Environment**  
    - Open a terminal and navigate to the project directory.  
    - Create a new conda environment:  
        ```sh  
        conda create -n research-paper-analyzer python=3.8  
        conda activate research-paper-analyzer  
        ```  
    - Install the required libraries:  
        ```sh  
        pip install openai ipython python-dotenv jupyter  
        ```  
  
4. **Set up environment variables**  
    - Create a `.env` file in the root directory of the repository and add your Azure OpenAI API key and endpoint:  
        ```sh  
        AZURE_OPENAI_API_KEY=your_api_key_here  
        AZURE_OPENAI_ENDPOINT=https://<your_resource_name>.openai.azure.com  
        ```  
  
## Visual Studio Code Setup Instructions  
  
1. **Download and Install Visual Studio Code**  
    - Download Visual Studio Code from the [official website](https://code.visualstudio.com/).  
    - Follow the installation instructions for your operating system.  
  
2. **Open the Project in Visual Studio Code**  
    - Open Visual Studio Code.  
    - Click on `File > Open Folder` and select the `AzureOpenAI-ResearchPaperAnalyzer` folder.  
  
3. **Set Up a Conda Environment in Visual Studio Code**  
    - Open the Command Palette by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).  
    - Type `Python: Create Environment` and select it.  
    - Choose `Conda` as the environment type.  
    - Select `Python 3.x` (ensure it matches the version you have installed).  
    - Name your environment (e.g., `research-paper-analyzer`).  
    - Visual Studio Code will create the environment and install the necessary dependencies.  
  
4. **Activate the Conda Environment**  
    - Open the Command Palette again by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).  
    - Type `Python: Select Interpreter` and select it.  
    - Choose the interpreter that matches the environment you just created (e.g., `research-paper-analyzer`).  
  
5. **Install Required Packages in the Conda Environment**  
    - Open a new terminal in Visual Studio Code by clicking on `Terminal > New Terminal`.  
    - Ensure the terminal is using the conda environment you created. If not, activate it by running:  
        ```sh  
        conda activate research-paper-analyzer  
        ```  
    - Install the required packages:  
        ```sh  
        pip install openai ipython python-dotenv jupyter  
        ```  
  
6. **Install Jupyter Notebook Extensions in Visual Studio Code**  
    - Open the Command Palette by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).  
    - Type `Extensions: Install Extensions` and select it.  
    - In the Extensions view, search for `Jupyter` and install the official Jupyter extension for Visual Studio Code.  
  
7. **Run Jupyter Notebook**  
    - Open the Command Palette by pressing `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).  
    - Type `Jupyter: Create New Blank Notebook` and select it.  
    - Save the new notebook with a name (e.g., `analyze_papers.ipynb`).  
    - Open the `analyze_papers.ipynb` notebook file in the Jupyter interface within Visual Studio Code.  
