### Repository Overview
This repository contains a comprehensive local chatbot application based on Retrieval Augmented Generation (RAG) technology. It supports multiple Large Language Models (LLMs), allowing users to configure their preferred models easily.

### Key Features

#### 1. Multi - Model Support
The application supports a wide range of LLM providers such as Ollama, OpenAI, MoonShot, Baichuan, ZhipuAI, DeepSeek, and DashScope. The `backend/sta_config.toml` file details each provider's base URL, supported LLM models, embedding models, and introductions. For example, Ollama supports models like `moonshot - v1 - 8k` and `deepseek - r1:1.5b`, giving users diverse options to meet different application requirements.

#### 2. Knowledge Base Management
Users can manage knowledge base documents efficiently. In the front - end interface, by clicking the configuration button (gear icon) in the chat interface, they can view and manage knowledge base documents. The `frontend/scripts.js` file contains functions like `saveKnowledgeBase` for uploading and saving documents and system prompts. It supports various file formats such as PDF, DOCX, and CSV. The `backend/rag_service.py` includes a `remove_useless` method to clean up unnecessary documents and keep the knowledge base organized.

#### 3. RAG Service
The `RagService` class in `backend/rag_service.py` is the core of the project. It implements the chat service based on RAG technology, including document embedding, historical conversation management, and question answering. The `_embed_documents` method embeds documents and stores them in a vector database. When answering user questions, it retrieves relevant documents from the knowledge base to enhance the accuracy of the answers.

#### 4. Custom Console and Log Display
The `backend/console_window.py` file implements a custom console window for displaying log information. The `CustomConsole` class includes a text edit box and a toggle button. The `append_text` method adds text information to the console, and the `toggle_visibility` method toggles the visibility of the console window, facilitating users to monitor the system's running status.

### Deployment and Usage

#### 1. Environment Setup
The project provides `environment.yaml` and `requirements.txt` files to help users create the required Conda environment and install Python package dependencies.

#### 2. Packaging and Deployment
The `buildexe.bat` script uses PyInstaller to package the backend scripts into an executable file and copies relevant files to the packaging directory. The `innoSetup.iss` script uses the Inno Setup Compiler to create a single installation program `unisetup.exe`, simplifying the deployment process.

#### 3. Flexible Configuration
The project includes static configuration files (`backend/sta_config.toml`), factory configuration files (`backend/factory.toml`), and dynamic configuration files (`backend/dyn_config.toml`). Users can modify these configuration files as needed to adjust the model and knowledge base settings. The `merge_config` method in `backend/uni_config.py` ensures that empty fields in the configuration files are filled with factory default values.

### Community - Friendly
The project is licensed under the MIT license (`LICENSE` file), encouraging users to use, modify, and distribute it freely. It also provides detailed documentation, including `README.md`, `README_cn.md`, `developer_guide.md`, and `终端用户手册.md` (End - User Manual), enabling both developers and end - users to get started quickly.

### Main Files and Their Functions

#### Front - End Files
- `frontend/index.html`: Defines the HTML structure of the intelligent assistant, including the chat interface and configuration modal.
- `frontend/scripts.js`: Implements front - end interaction logic, such as sending messages, managing the configuration modal, and handling document uploads and deletions.
- `frontend/styles.css`: Defines the application's styles, including the appearance of the chat interface, configuration modal, and buttons.

#### Back - End Files
- `backend/http_server.py`: Uses the FastAPI framework to implement the backend API, handling requests such as model configuration, document uploads, and retrievals.
- `backend/rag_service.py`: Implements the core RAG service, including document embedding, historical conversation management, and question answering.
- `backend/uni_config.py`: Manages configuration files, including loading, updating, and merging configuration information.
- `backend/console_window.py`: Implements a custom console window for displaying log information.
- `backend/logging_config.py`: Provides a singleton entity for the logging service.

### Conclusion
This repository offers a complete implementation of a local chatbot application based on RAG technology. It has rich features and good configurability, making it suitable for users and developers who need to build local intelligent assistants. By supporting different LLMs and managing knowledge bases, users can customize the chatbot's functions according to their needs. Additionally, the project has a clear code structure and detailed documentation, facilitating developers to conduct secondary development and expansion.