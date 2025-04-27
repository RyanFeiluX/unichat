import os, sys, re
import argparse
import psutil
from PIL import Image
import yaml
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import tomlkit  # Import tomlkit for round-trip parsing
from typing import List, Dict, Union
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QMetaObject, Qt
import threading
import asyncio
import webbrowser
# import signal
import win32gui, win32api, win32con
from win32con import WS_CAPTION

from utils import check_model_avail
# import win32console  # Import win32console to access the console buffer
from logging_config import setup_logging
import time
from ollama_setting import OllamaSetting


if getattr(sys, 'frozen', False):
    # If it is a PyInstaller packaged executable
    app_root = os.path.abspath(os.path.dirname(sys.executable))
else:
    # For a normal Python script
    app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Configure logging
logger = setup_logging(logfile=os.path.join(app_root, 'run.log'))

logger.info(f'python version : {sys.version}')

current_process = psutil.Process(os.getpid())
process_name = os.path.normcase(current_process.name())
cnt_found = 0
for proc in psutil.process_iter(['name']):
    p_name = os.path.normcase(proc.info['name'])
    if p_name == process_name and proc.pid != current_process.pid:
        logger.warning(f'Another {p_name} instance(PID={proc.pid}) is running. Exiting...')
        sys.exit(0)


logger.info(f'APP ROOT: {app_root}')


from rag_service import RagService
rag_service = RagService(app_root, logger)
LOCAL_DOCS_DIR = rag_service.modconfig.local_docs_dir()
logger.info(f'LOCAL_DOCS_DIR: {LOCAL_DOCS_DIR }')
rag_service.setup_service(LOCAL_DOCS_DIR)

try:
    # Open and read the .yml file
    with open(os.path.join(app_root, 'metadata.yml'), 'r') as file:
        metadata = yaml.safe_load(file)
    version = metadata['Version'].strip()
    logger.info(f'App version: {version}')
except FileNotFoundError:
    version = 'Unknown'
    logger.warning('Version file not found. Using "Unknown" as version number.')

user_url = "http://localhost:63342/unichat/frontend/index.html"
print(f'If the chat page is not opened within few seconds, please click the link {user_url} instead.')

# Create FastAPI application for API service
app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(app_root, 'frontend')), 'static')

# Optional in case of CORS on frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Define request model
class QuestionRequest(BaseModel):
    question: str
    session_id: str


# Define response model
class AnswerResponse(BaseModel):
    think: str
    answer: str


# Provide query API http://127.0.0.1:8000/ask
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        # Get user question
        user_question = request.question
        session_id = request.session_id
        logger.debug(f'question:{user_question}')

        # Build answer through RAG chain
        # answer = qa_chain.run(user_question)
        ai_answering, ai_reasoning = rag_service.__ask__(session_id, user_question)

        final_answer = AnswerResponse(think=ai_reasoning, answer=ai_answering)
        logger.debug(f'answer:{ai_answering}')
        return final_answer
    except asyncio.exceptions.CancelledError:
        logger.info("Async task cancelled during ask_question. Ignoring...")
        raise HTTPException(status_code=503, detail="Service is temporarily unavailable.")
    except Exception as ee:
        logger.error(f'{repr(ee)}')
        m_code = re.match(r'(.*Response \[(\d+)\].*|.*Error code: (\d+).*|.*status_code: (\d+).*)', str(ee))
        if m_code:
            status_code = sum([int(i) for i in m_code.groups()[1:] if i])
        else:
            status_code = 500
        raise HTTPException(status_code=status_code, detail=str(ee))


@app.get('/')
async def get_root():
    return {'message': 'Hello UniChat!'}


class ModelSelect(BaseModel):
    llm_provider: str
    llm_model: str
    emb_provider: str
    emb_model: str


@app.get("/api")
async def fetch_any():
    logger.info(f'GET: /api')
    return {'API': ['models', 'documents', 'upload-documents']}


class ModelConfig(BaseModel):
    model_support: List[Dict[str, Union[str, List[str]]]]
    model_select: Dict[str, str]


# API for http://127.0.0.1:8000/api/models
@app.get("/api/models", response_model=ModelConfig)  # Updated endpoint
async def fetch_config():
    logger.info(f'GET: /api/models')
    options = rag_service.cfg.aggregate_provider_profile()
    sel = rag_service.cfg.get_deployment_profile()
    return ModelConfig(model_support=options, model_select=sel)

class ModelConfigResult(BaseModel):
    message: str
    status_ok: bool

# API for http://127.0.0.1:8000/api/models
@app.post("/api/models", response_model=ModelConfigResult)  # Updated endpoint
async def save_config(options: ModelSelect):
    logger.info(f'POST: /api/models')
    unavail_models = set()
    if options.llm_provider == 'Ollama':
        if not check_model_avail(options.llm_model):
            unavail_models.add(options.llm_model)
    if options.emb_provider == 'Ollama':
        if not check_model_avail(options.emb_model):
            unavail_models.add(options.emb_model)
    if unavail_models:
        logger.warning(f'Model{"s" if len(unavail_models)>1 else ""} {",".join(unavail_models)} {"are" if len(unavail_models)>0 else "is"} not downloaded yet.')
        return {"message": f'Configuration failed because model{"s" if len(unavail_models)>0 else ""} {",".join(unavail_models)} {"are" if len(unavail_models)>0 else "is"} not downloaded yet.',
                "status_ok": False}

    rag_service.cfg.update_deployment_profile(options)

    return {"message": "Configuration updated successfully", "status_ok": True}


class UploadDocumentsResult(BaseModel):
    message: str
    status_ok: bool

@app.post("/api/upload-documents", response_model=UploadDocumentsResult)
async def upload_documents(doc_blob_list: List[UploadFile] = File(...),
                           system_prompt: str = Form(...), document_list: str = Form(...)):
    logger.info(f'POST: /api/upload-documents')
    try:
        # Validate that at least one document is uploaded
        if not doc_blob_list:
            raise HTTPException(status_code=422, detail="No documents were uploaded.")

        # Validate that the system prompt is not empty
        if (not system_prompt) or (len(system_prompt.strip()) == 0):
            raise HTTPException(status_code=422, detail="System prompt cannot be empty.")

        if not os.path.exists(LOCAL_DOCS_DIR):
            os.makedirs(LOCAL_DOCS_DIR)  # Ensure the directory for saving files exists

        file_names = []
        for document in doc_blob_list:
            file_path = os.path.join(LOCAL_DOCS_DIR, document.filename)
            with open(file_path, "wb") as f:
                f.write(await document.read())  # Save the uploaded file content
                f.flush()
                logger.info(f'{document.filename} is uploaded.')
            file_names.append(document.filename)

        # Update the document list
        doc_list = document_list.split(',') if document_list else []
        rag_service.remove_useless(doc_list)
        # You can further process the document_list here, like removing duplicates

        rag_service.cfg.update_knowledge_base(doc_list=doc_list, robot_desc=system_prompt.strip())

        return {"message": "Documents and system prompt uploaded and saved successfully.", "status_ok": True}
    except Exception as ee:
        logger.error(f"Exception in uploading documents or saving system prompt: {str(ee)}")
        raise HTTPException(status_code=422, detail=f"Exception in uploading documents or saving system prompt: {str(ee)}")

class DocumentsConfigResult(BaseModel):
    message: str
    status_ok: bool

@app.post("/api/documents", response_model=DocumentsConfigResult)
async def update_documents(system_prompt: str = Form(...), document_list: str = Form(...)):
    logger.info(f'POST: /api/documents')
    try:
        # Update the document list
        doc_list = document_list.split(',') if document_list else []
        rag_service.remove_useless(doc_list)
        # You can further process the document_list here, like removing duplicates

        rag_service.cfg.update_knowledge_base(doc_list=doc_list, robot_desc=system_prompt.strip())

        return {"message": "Documents and system prompt uploaded and saved successfully.", "status_ok": True}
    except Exception as ee:
        raise HTTPException(status_code=422, detail=f"Error in updating document list or system prompt: {str(ee)}")

class DocumentFetchResult(BaseModel):
    documents: list
    system_prompt: str

@app.get("/api/documents", response_model=DocumentFetchResult)
async def fetch_documents():
    logger.info(f'GET: /api/documents')
    try:
        # Fetch the list of documents and system prompt
        # docs = rag_service.cfg.get_documents()
        documents = rag_service.cfg.get_documents()
        system_prompt = rag_service.cfg.get_robot_desc()  #dcfg['Knowledge']['ROBOT_DESC']

        return {
            "documents": documents,
            "system_prompt": system_prompt
        }
    except Exception as ee:
        logger.error(f'Exception in fetching documents and system prompt: {str(ee)}')
        raise HTTPException(status_code=500, detail=f"Exception in fetching documents and system prompt: {str(ee)}")

class ChangesSuspense(BaseModel):
    suspense: bool

@app.get('/api/config-suspense', response_model=ChangesSuspense)
async def query_config_suspense():
    logger.info(f'GET: /api/config-suspense')
    return {'suspense': rag_service.cfg.changes_suspense}

class ChangesApply(BaseModel):
    status_ok: bool

@app.post('/api/config-apply', response_model=ChangesApply)
async def apply_changes_suspense():
    logger.info(f'POST: /api/config-apply')
    logger.info(f'Re-establishing the knowledge base...')
    try:
        # Here you can add the logic to apply the configuration changes
        # For example, restart the service
        rag_service.restart_service()
        return {'status_ok': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def toggle_console_state(win_handler, q_action):
    visible = win32gui.IsWindowVisible(win_handler)
    if visible:
        win32gui.ShowWindow(win_handler, win32con.SW_HIDE)
        q_action.setText('Show Console')
    else:
        win32gui.ShowWindow(win_handler, win32con.SW_SHOW)
        q_action.setText('Hide Console')

def update_tray_menu(visible, q_action):
    # Update tray icon state
    if visible:
        q_action.setText('Hide Console')
    else:
        q_action.setText('Show Console')

ollsetting = OllamaSetting(logger, app_root)

# Function to create and show the system tray icon
def create_system_tray(win_handler):
    # Create a system tray icon
    icon_path = os.path.join(app_root, "resources", "icon2.png")
    if not os.path.exists(icon_path):
        logger.error(f"Icon file {icon_path} not found.")
    else:
        tray_icon = QSystemTrayIcon(QIcon(icon_path), qapp)
        tray_icon.setToolTip("UniChat is running")

        # Create a menu for the system tray icon
        tray_menu = QMenu()

        ollama_action = QAction('Ollama Setting', tray_menu)
        ollama_action.triggered.connect(ollsetting.open_ollama_settings)
        tray_menu.addAction(ollama_action)

        wv = win32gui.IsWindowVisible(hwnd)
        console_action = QAction('Hide Console' if wv else 'Show Console', tray_menu)
        console_action.triggered.connect(lambda action: toggle_console_state(win_handler, console_action))
        tray_menu.addAction(console_action)

        exit_action = QAction("Exit", tray_menu)
        exit_action.triggered.connect(exit_app)
        tray_menu.addAction(exit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()

    sys.exit(qapp.exec_())


server = None
qapp = None
hwnd = None


@app.on_event("startup")
async def startup_event():
    webbrowser.open_new_tab(user_url)


@app.on_event("shutdown")
async def shutdown_event():
    try:
        # Necessary operations, like disconnecting database.
        logger.info("Clean up resources")
    except asyncio.exceptions.CancelledError:
        logger.info("Async task cancelled during shutdown. Ignoring...")


# Function to start the uvicorn server
def start_server():
    global server
    logger.info(f'Start the server...')
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000))
    server.run()


# Function to stop the uvicorn server and quit the application
def exit_app():
    global server, qapp, hwnd, mutex
    try:
        # Log the start of the shutdown process
        logger.info("Starting graceful shutdown of the application...")

        # Stop the Uvicorn server
        if server:
            logger.info("Stopping the Uvicorn server...")
            server.should_exit = True
            server.force_exit = True
            # Wait for the server to stop
            server_thread = next((t for t in threading.enumerate() if t.name == 'unichat_server'), None)
            if server_thread:
                server_thread.join()
            logger.info("Uvicorn server stopped.")

        # Quit the QApplication
        if qapp:
            logger.info("Quitting the QApplication...")
            # qapp.quit()
            QMetaObject.invokeMethod(qapp, 'quit', Qt.QueuedConnection)
            logger.info("QApplication quit.")

        # Close the console window
        if hwnd:
            logger.info("Closing the console window...")
            win32gui.CloseWindow(hwnd)
            logger.info("Console window closed.")

        # Log the end of the shutdown process
        logger.info("Application shut down gracefully.")
    except asyncio.exceptions.CancelledError:
        logger.info("Async task cancelled during shutdown. Ignoring...")
    except Exception as e:
        logger.error(f"Error in during shutdown: {e}")

    # Exit the application
    sys.exit(0)


# Signal handler
def signal_handler(sig, frame):
    _, _ = sig, frame
    logger.info('Received Ctrl+C. Exiting application...')
    exit_app()


# signal.signal(signal.SIGINT, signal_handler)  # SIGINT triggered by Ctrl+C
# signal.signal(signal.SIGTERM, signal_handler)  # Sent to request a process to terminate gracefully. Unsupported on Windows

# Function to show the console window
def show_console_window():
    if os.name == 'nt':
        global hwnd
        # hwnd = win32gui.GetForegroundWindow()
        if win32gui.IsWindow(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        elif hwnd:
            logger.critical(f'Target window handler is invalid.')
        else:
            logger.critical(f'Target window handler is unknown.')


# Hide the console window on Windows
def hide_console_window():
    if os.name == 'nt':
        global hwnd
        # hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)


# Function to handle console close event
def console_ctrl_handler(ctrl_type):
    if ctrl_type == win32con.CTRL_C_EVENT:  # Ctrl+C event
        logger.info('You pressed Ctrl+C! Exiting...')
        exit_app()
        return True
    elif ctrl_type == win32con.CTRL_LOGOFF_EVENT:  # Logout event
        logger.info('You is logging off. Performing cleanup...')
        exit_app()
        return True
    elif ctrl_type == win32con.CTRL_SHUTDOWN_EVENT:  # Shutdown event
        logger.info('System is shutting down. Saving data...')
        exit_app()
        return True
    elif ctrl_type == win32con.CTRL_CLOSE_EVENT:
        logger.info('You are closing the console window. Exiting...')
        exit_app()
        return True
    return True

if os.name == 'nt':
    # Register the console control handler
    win32api.SetConsoleCtrlHandler(console_ctrl_handler, True)


# from console_window import CustomConsole, CustomConsoleWriter
from utils import running_in_pycharm, pycharm_hosted
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist-mode', dest='dist_mode', action='store_true',
                        help="Distribution mode specified. Development mode by default.")
    args = parser.parse_args()

    max_retries = 5
    retry_delay = 1  # Delay 1 second
    addressed = False
    for i in range(max_retries):
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            addressed = True
            logger.info(f'Locate the console {win32gui.GetWindowText(hwnd)}')
            break
        time.sleep(retry_delay)
    if not addressed:
        logger.error(f'Main console window not found. Exit...')
        exit(-1)

    app_name = os.path.basename(sys.argv[0]).split('.')[0]
    try:
        win32gui.SetWindowText(hwnd, app_name)
        win_text = win32gui.GetWindowText(hwnd)
        if win_text != app_name:
            logger.warning(f'Failed to modify the window text: {win_text}')
        else:
            logger.info(f'Successfully set the window title to {app_name}')
    except Exception as e:
        logger.error(f'Error in setting window title: {str(e)}')

    # Set the application icon
    icon_path = os.path.normpath(os.path.join(app_root, "resources", "icon2.ico"))
    if os.path.exists(icon_path):
        try:
            # Try to open the icon file using Pillow
            with Image.open(icon_path) as img:
                icon = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 0, 0,
                                          win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE)

                if icon:
                    # Set the icon for the console window
                    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon)
                    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon)
                else:
                    logger.warning(f"Failed to load icon from {icon_path}. Using default icon.")
        except Exception as e:
            logger.warning(f"Failed to set Icon from {icon_path} with message: {str(e)}. Using default icon.")
    else:
        logger.warning(f"Icon file {icon_path} not found. Using default icon.")

    # Disable the close button
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    style = style & ~win32con.WS_SYSMENU & ~win32con.WS_MINIMIZEBOX & ~win32con.WS_MAXIMIZEBOX
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
    win32gui.SetWindowPos(hwnd, None, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    # global qapp
    qapp = QApplication(sys.argv)

    # Set the application icon
    icon_path = os.path.join(app_root, "resources", "icon2.ico")
    if os.path.exists(icon_path):
        qapp.setWindowIcon(QIcon(icon_path))
    else:
        logger.warning(f"Icon file {icon_path} not found. Using default icon.")

    pych_context = running_in_pycharm()
    pych_hosted = pycharm_hosted()
    inPyCharm = pych_context or pych_hosted
    logger.info(f'PyCharm Context: {inPyCharm}')

    # Hide the default main console in case of Windows but not PyCharm environment.
    if args.dist_mode and os.name == 'nt':
        hide_console_window()

    # uvicorn.run('http_server:app', host="127.0.0.1", port=8000, reload=False)
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, name='unichat_server', daemon = True)
    # server_thread.daemon = True
    server_thread.start()

    # Create and show the system tray icon
    create_system_tray(hwnd)

    server_thread.join()
    logger.info("Exiting application...")

    # # Keep the main thread alive
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     logger.info("Exiting application...")
    #     time.sleep(1)
    sys.exit(qapp.exec_())
