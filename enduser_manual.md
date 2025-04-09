# UniChat Application User Manual

## I. Introduction
UniChat is an intelligent assistant application that combines multiple large language models (LLMs) and knowledge base documents to provide users with accurate and useful answers. This manual will guide you through the installation, configuration, and usage of the application.

## II. Installation

### 2.1 Obtaining the Installation Package
UniChat is distributed as an installation package. After the package is built, a directory named `dist\unichat` will be generated. You can copy this directory to the device where you want to install the application.

### 2.2 Starting the Application
After copying the `dist\unichat` directory to the target device, simply double - click the `UniChat.exe` file in this directory to start the application. Once started, a custom console window will pop up, and the application will start an HTTP server in the background. You can access the chat interface by entering the following URL in your browser:
```plaintext
http://localhost:63342/unichat/frontend/index.html
```

## III. Configuration

### 3.1 Environment Variable Configuration
The `.env` file is used to store environment variables, such as API keys and base URLs for different large language model (LLM) providers. Here are some common LLM providers and their configuration examples:
```plaintext
OPENAI_API_KEY=
MOONSHOT_API_KEY=
BAICHUAN_API_KEY=
DEEPSEEK_API_KEY=
DASHSCOPE_API_KEY=
```
You need to fill in the corresponding API keys in the appropriate fields according to your needs. If you don't have the relevant API keys, you can contact the corresponding providers to apply for them.
Note: .env is optional. Alternatively, you can fill your API keys to the environment variables.

### 3.2 Knowledge Base Configuration

### 3.3 Deployment Configuration

You can choose the appropriate LLM provider and model, as well as the embedding vector provider and model, according to your needs. If the `LLM_MODEL` or `EMB_MODEL` field is empty, the application will use the default model defined in the provider section.

## IV. Usage Instructions

### 4.1 Starting the Chat Interface
After starting the application, enter `http://localhost:63342/unichat/frontend/index.html` in your browser to open the chat interface.

### 4.2 Asking Questions and Getting Answers
Enter your question in the input box on the chat interface and click the "Send" button. The application will send the question to the intelligent assistant, and the answer will be displayed in the chat window.

### 4.3 Configuring the Model and Knowledge Base
Click the configuration button (gear icon) in the upper - right corner of the chat interface to open the configuration window. In the configuration window, you can select different LLM providers and models, as well as embedding vector providers and models. You can also view and manage the knowledge base documents.

### 4.4 Uploading Knowledge Base Documents
If you need to upload your own knowledge base documents, you can use the API provided by the application. For specific operation methods, please refer to the development documentation or contact the technical support team.

## V. Frequently Asked Questions

### 5.1 Model Not Found
If the application prompts that a certain model is not found locally, you can use the `Ollama pull <model_name>` command in the terminal to download the model.

### 5.2 Network Error
If you encounter a network error, please check your network connection and ensure that the API keys and base URLs in the `.env` file are correct.

### 5.3 Server Error
If you receive a server error, please check the application's log file (`run.log`, located in the application's root directory) for more detailed information. You can also try restarting the application.

## VI. Contact Us
If you encounter any problems or have any suggestions during use, please feel free to contact our technical support team. We will be happy to assist you.

The above is the user manual for the UniChat application. We hope it will help you use the application smoothly. If you have any other questions, please refer to this manual or contact us at any time.