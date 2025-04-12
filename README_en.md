# Inputs

## Potentially relevant code snippets from the current codebase
File path: README.md
```
# Unichat Brief
Deploy a chatbot locally based on Retrieval Augmented Generation (RAG) technologies. Multiple large language model (LLM) options are supported, making it easy to configure the LLM of your choice.

# Details

These code files form an intelligent assistant application, encompassing front - end pages, back - end services, style settings, log handling, console display, and packaging scripts. Here is a detailed introduction to each file:

## Front - end Files
### index.html
- Function: Defines the HTML structure of the intelligent assistant, including the chat interface and the configuration modal.
- Key elements:
  - A chat container, an input box, and a send button for user - assistant interaction.
  - A configuration button that, when clicked, opens the configuration modal.
  - The configuration modal contains two tabs, "Model" and "Knowledge Base", for setting model parameters and managing knowledge base documents.

### scripts.js
- Function: Implements front - end interaction logic, including sending messages, managing the configuration modal, handling document uploads and deletions, etc.
- Key functions:
  - sendMessage(): Sends the user's input question to the back - end and displays the assistant's response.
  - openConfigModal() and closeConfigModal(): Open and close the configuration modal.
  - addDocuments() and deleteSelectedFile(): Add and delete knowledge base documents.
  - saveKnowledgeBase(): Saves knowledge base documents and system prompts to the back - end.

### styles.css
- Function: Defines the application's styles, including the appearance of the chat interface, configuration modal, buttons, etc.
- Key styles:
  - Styles for the chat container and message boxes, differentiating between user and assistant messages.
  - Styles for the configuration modal, including tabs, dropdowns, and save buttons.
  - Styles for the document list and operation buttons, such as add, delete, and save buttons.

## Back - end Files
### http_server.py
- Function: Implements the back - end API using the FastAPI framework to handle requests for model configuration, document uploads, and retrievals.
- Key routes:
  - GET /api/models: Retrieves configuration information about supported and selected models.
  - PUT /api/models: Saves model configuration information to the dyn_config.toml file.
  - GET /api/documents: Retrieves the list of knowledge base documents and system prompts.
  - POST /api/upload - documents and POST /api/documents: Uploads documents and saves system prompts to the back - end.

### console_window.py
- Function: Implements a custom console window for displaying log information.
- Key classes and methods:
  - CustomConsole: A custom console window class that includes a text edit box and a toggle button.
  - append_text(): Adds text information to the console window.
  - toggle_visibility(): Toggles the visibility of the console window.

### logging_config.py
- Function: Configures log handling to redirect log information to the custom console window.
- Key classes and methods:
  - CustomStream: A custom stream class for writing log information to the console window.
  - redirect_stream(): Redirects the log stream to the specified stream object.

## Packaging Scripts
### buildexe.bat
- Function: Uses PyInstaller to package the back - end scripts into an executable file and copies relevant files to the packaging directory.
- Key steps:
  - Checks if PyInstaller is installed.
  - Generates a version information file.
  - Uses PyInstaller to package the back - end scripts.
  - Copies configuration files, front - end files, resource files, and documents to the packaging directory.

### Setup.nsi
- Function: An installation program script based on the NSIS scripting language, which finally creates a single installation program, unichatSetup.exe.
- Tools:
  - NSIS software. [Download link](https://nsis.sourceforge.io/Download)

In summary, these code files together build a complete intelligent assistant application, covering front - end interfaces, back - end services, log handling, and packaging and deployment features.
```