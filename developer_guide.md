# UniChat Application User Guide

## 1. Introduction
UniChat is an intelligent assistant application that utilizes various large language models (LLMs) and knowledge base documents to provide users with accurate and useful answers. This guide will help you understand how to install, configure, and use the application.

## 2. Installation

### 2.1 Prerequisites
- **Python and Dependencies**: Ensure that Python is installed on your system. You also need to have `PyInstaller` installed. If not, you can install it using `pip install pyinstaller`.
- **Ollama (Optional)**: If you plan to use the Ollama LLM provider, make sure Ollama is installed and running on your local machine.

### 2.2 Building the Installation Package
To build the installation package, follow these steps:
1. Open a command prompt or terminal and navigate to the project directory.
2. Run the `buildexe.bat` script. This script will perform the following tasks:
    - Check if `PyInstaller` is installed.
    - Generate a version file based on the `metadata.yml` file.
    - Use `PyInstaller` to build the application into a single directory named `dist\unichat`.
    - Copy necessary configuration files, frontend files, resources, and local documents to the `dist\unichat` directory.
    - Reset the dynamic configuration file to its factory defaults.

```batch
@echo off
@chcp 65001
REM Set the script path
@set script=../unichat/backend/http_server.py

@setlocal enabledelayedexpansion

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo PyInstaller is not installed. Please install it firstly.
    exit /b 1
)

@cls

REM Check if the script file exists
if not exist %script% (
    echo Script file %script% not found.
    exit /b 1
)

REM Build all
if "%1%"=="all" (
  rd /S /Q dist
  rd /S /Q build
)

pyivf-make_version --source-format yaml --metadata-source metadata.yml --outfile version_info.txt

set cenv_root="d:\programdata\anaconda3\envs\condaenv-unichat"

REM Launch pyinstaller
pyinstaller --onedir ^
            --specpath spec ^
            --name UniChat ^
            --noconfirm ^
            --add-binary "%cenv_root%\Scripts\pandoc.exe:bin" ^
            --collect-submodules pydantic ^
            --collect-submodules langchain.chains ^
            --exclude-module pyinstaller ^
            --exclude-module pillow ^
            --icon %CD%\resources\icon3.ico ^
            --version-file %CD%\version_info.txt ^
            %script%

cd %CD%
if exist "dist\unichat\backend" (
  rd /S /Q dist\unichat\backend
)
mkdir dist\unichat\backend
rem if exist "backend\.env" (
rem   copy %CD%\backend\.env %CD%\dist\unichat\backend
rem )
copy %CD%\backend\sta_config.toml %CD%\dist\unichat\backend
copy %CD%\backend\dyn_config.toml %CD%\dist\unichat\backend
copy %CD%\backend\factory.toml %CD%\dist\unichat\backend
python reset_config.py --dynamic-config %CD%\dist\unichat\backend\dyn_config.toml ^
                       --factory-config %CD%\dist\unichat\backend\factory.toml

if exist "dist\unichat\frontend" (
  rd /S /Q dist\unichat\frontend
)
mkdir dist\unichat\frontend && copy frontend\* dist\unichat\frontend

if exist "dist\unichat\resources" (
  rd /S /Q dist\unichat\resources
)
mkdir dist\unichat\resources && copy resources\* dist\unichat\resources

if exist "dist\unichat\local_docs" (
  rd /S /Q dist\unichat\local_docs
)
mkdir dist\unichat\local_docs && copy docs\QA.md dist\unichat\local_docs

copy %CD%\README.md %CD%\dist\unichat
copy %CD%\LICENSE %CD%\dist\unichat
copy %CD%\metadata.yml %CD%\dist\unichat
```

### 2.3 Installing the Application
After the build process is complete, you can distribute the `dist\unichat` directory to other users. The users can simply run the `UniChat.exe` file inside the `dist\unichat` directory to start the application.

## 3. Configuration

### 3.1 Environment Variables
The application uses an `.env` file to store environment variables such as API keys and base URLs for different LLM providers. You can configure the following providers:
- **OpenAI**
- **Moonshot**
- **Baichuan**
- **ZhipuAI**
- **DeepSeek**
- **DashScope**
- **Ollama**

Here is an example of the `.env` file:
```plaintext
OPENAI_API_KEY=
MOONSHOT_API_KEY="sk-l6Wg4HFd..."
BAICHUAN_API_KEY="sk-68b0..."
ZHIPUAI_API_KEY="f881c528..."
DEEPSEEK_API_KEY="sk-0b06..."
DASHSCOPE_API_KEY="sk-79f1b2aa..."
```

### 3.2 Configuration Files
The application also uses TOML configuration files:
- **`sta_config.toml`**: Contains static configuration parameters.
- **`dyn_config.toml`**: Contains dynamic configuration parameters that can be modified during runtime.
- **`factory.toml`**: Contains factory default configuration values.

You can modify these files to change the application's behavior, such as selecting a different LLM provider or model, or specifying a different set of knowledge base documents.

### 3.3 Model Selection
You can select the LLM provider and model through the application's configuration interface. The available models depend on the selected provider. If a model is not locally available, the application will prompt you to download it using `Ollama pull <model_name>`.

## 4. Using the Application

### 4.1 Starting the Application
Double-click the `UniChat.exe` file in the `dist\unichat` directory to start the application. A custom console window will appear, and the application will start the HTTP server in the background. You can access the chat interface by opening the following URL in your web browser:
```plaintext
http://localhost:63342/unichat/frontend/index.html
```

### 4.2 Chatting with the Assistant
1. Enter your question in the input field at the bottom of the chat window.
2. Click the "发送" (Send) button to send your question to the assistant.
3. The assistant will process your question and display the answer in the chat window.

### 4.3 Updating Models
You can fetch and update deployed models through the application's API. To do this, send a GET/POST request to the `/api/models` endpoint with the following parameters:
- **`llm_providers`**: A list of LLM model providers.
- **`llm_models`**: A list of LLM models published by specific provider.
- **`emb_providers`**: A list of Embedding model providers.
- **`emb_models`**: A list of Embedding models published by specific provider.

### 4.4 Uploading Documents
You can upload your own knowledge base documents through the application's API. To do this, send a POST request to the `/api/upload-documents` endpoint with the following parameters:
- **`documents`**: A list of files to upload.
- **`system_prompt`**: A system prompt for the assistant.
- **`document_list`**: A comma-separated list of document names.

### 4.5 Updating Documents
You can upload your own knowledge base documents through the application's API. To do this, send a POST request to the `/api/upload-documents` endpoint with the following parameters:
- **`system_prompt`**: A system prompt for the assistant, pointing to the same as $4.3.
- **`document_list`**: A comma-separated list of document names.

### 4.6 Querying Suspensive Config Changes
You can query whether there are suspensive config changes through the application's API. To do this, send a GET request to the `/api/config-suspense` endpoint with the following parameters:
- **`documents`**: A list of files to upload.
- **`system_prompt`**: A system prompt for the assistant.
- **`document_list`**: A comma-separated list of document names.

### 4.7 Applying Config Changes
You can launch config changes deployment procedure through the application's API. To do this, send a POST request to the `/api/config-apply` endpoint without any following.
 
### 4.8 File Format Conversion
You can convert file format through the application's API. To do this, send a POST request to the `/api/file-format` endpoint without any following.
- **`data_blob`**: The blob of the file to be converted.
- **`ext_name`**: Extension name of target file.

Here is an example of how to use the API in JavaScript:
```javascript
function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;

    appendMessage('user', userInput);

    fetch(`${BASE_URL}/ask`, { // Use BASE_URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userInput }),
    })
    .catch(error => {
        console.error('Error during fetch:', error);
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(errorText => {
                throw new Error(`Server error: ${errorText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        appendMessage('assistant', data.answer);
    })
    .catch(error => {
        if (error instanceof TypeError) {
            console.error('Network error:', error);
            appendMessage('assistant', '网络错误，请检查您的网络连接。');
        } else {
            console.error('Server error:', error);
            appendMessage('assistant', '抱歉，服务器处理您的请求时出现错误。');
        }
    });

    document.getElementById('user-input').value = '';
    document.getElementById('user-input').focus();
}
```

## 5. Troubleshooting

### 5.1 Model Not Found
If you encounter an error indicating that a model is not locally found, you can download the model using `Ollama pull <model_name>` in your terminal.

### 5.2 Network Error
If you experience a network error, check your network connection and make sure that the API keys and base URLs in the `.env` file are correct.

### 5.3 Server Error
If you receive a server error, check the application's log file (`run.log` in the application root directory) for more details. You can also try restarting the application.

## 6. Conclusion
This user guide provides a comprehensive overview of how to install, configure, and use the UniChat application. If you have any further questions or encounter any issues, please refer to the application's documentation or contact the support team.