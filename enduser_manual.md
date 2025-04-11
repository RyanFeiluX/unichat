# UniChat Application User Manual

## I. Introduction
UniChat is an intelligent assistant application that combines multiple large language models (LLMs) and knowledge base documents to provide users with accurate and useful answers. This manual will guide you through the installation, configuration, and usage of the application.

## II. Installation

### 2.1 Obtaining the Installation Package
UniChat is distributed as an installation package. You can get its installation package from a public location.

### 2.2 Starting the Application
After installation, you can launch the application as the other ordinate application. Once started, a console window will pop up, and the application will start an HTTP server. A few seconds later, a webpage is automatically opened for you. You can start your operation from the web page. 

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

### 3.2 Deployment Configuration
![img_1.png](resources\unichat1.png)
![img_2.png](resources\unichat2.png)

### 3.3 Knowledge Base Configuration
![img_3.png](resources\unichat3.png)

You can choose the appropriate LLM provider and model, as well as the embedding vector provider and model, according to your needs. If the `LLM_MODEL` or `EMB_MODEL` field is empty, the application will use the default model defined in the provider section.

### 3.4 Ollama Installation
Before you can start your chat, you need download and install Ollama application.

### 3.5 Models downloading
The application is characterized of local model deployment. As a result, you also need download specific LLM models.
LLM models often have large size. You might want to specify a specific location for them. You can open Ollama Setting from system tray and specify the specific location.
![img_4.png](resources\unichat4.png)
![img_5.png](resources\unichat5.png)

## IV. Usage Instructions

### 4.1 Starting the Chat Interface
After starting the application, enter `http://localhost:63342/unichat/frontend/index.html` in your browser to open the chat interface. Actually, the interface is automatically opened during launching the application.

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