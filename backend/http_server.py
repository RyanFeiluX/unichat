import os, re
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import tomlkit  # Import tomlkit for round-trip parsing
from typing import List, Dict, Union
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from rag_service import *

user_url = "http://localhost:63342/unichat/frontend/index.html"
print(f'If the chat page is not opened in few seconds, please click the link {user_url} instead.')

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


# Define response model
class AnswerResponse(BaseModel):
    answer: str

# Provide query API http://127.0.0.1:8000/ask
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        # Get user question
        user_question = request.question
        session_id = "uid"
        print(f'session[{session_id}] question:\"{user_question}\"')

        # Build answer through RAG chain
        # answer = qa_chain.run(user_question)
        answer = msghist_chain.invoke({"input": user_question},
                                            config={"configurable": {"session_id": session_id}})

        ai_answer = answer['answer']
        ai_thinks = []
        thinks = re.findall(r'<think>([\s\S]*)</think>', ai_answer)
        if len(thinks) > 0:
            [ai_thinks.append(th.strip()) for th in thinks if len(th.strip())>0]
            if len(ai_thinks) > 0:
                reasoning = ('<<<<<< 推理开始 >>>>>>\n\n' + '\n------\n'.join(ai_thinks)
                             + '\n\n<<<<<< 推理完成 >>>>>>\n\n')
            else:
                reasoning = ''
        else:
            reasoning = ''
        if len(reasoning) > 0:
            summary = re.match(r'[\s\S]*</think>([\s\S]*)', ai_answer)
            if summary:
                summing = summary.group(1).strip()
            else:
                summing = ''
        else:
            summing = ai_answer.strip()
        final_answer = reasoning + summing

        # Return answer
        answer = AnswerResponse(answer=final_answer)
        print(f'answer:{summing}')
        return answer
    except Exception as e:
        print(f'{repr(e)}')
        m_code = re.match(r'(.*Response \[(\d+)\].*|.*Error code: (\d+).*|.*status_code: (\d+).*)', str(e))
        if m_code:
            status_code = sum([int(i) for i in m_code.groups()[1:] if i])
        else:
            status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get('/')
async def get_root():
    return {'message': 'Hello UniChat'}


class ModelSelect(BaseModel):
    llm_provider: str
    llm_model: str
    emb_provider: str
    emb_model: str


@app.get("/api")
async def fetch_any():
    print(f'GET: /api')
    return {'API': 'config'}

class ModelConfig(BaseModel):
    model_support: List[Dict[str, Union[str, List[str]]]]
    model_select: Dict[str, str]


# API for http://127.0.0.1:8000/api/models
@app.get("/api/models", response_model=ModelConfig)  # Updated endpoint
async def fetch_config():
    print(f'GET: /api/models')
    options: list = []
    for p in scfg['Providers'].keys():
        options.append({'provider': p,
                        'llm_model': scfg['Providers'][p][f'{p.upper()}_LLM_MODEL'].split(','),
                        'emb_model': scfg['Providers'][p][f'{p.upper()}_EMB_MODEL'].split(','),
                        'prov_intro': scfg['Providers'][p][f'{p.upper()}_INTRO']}
                       )
    sel = {'llm_provider': dcfg['Deployment']['LLM_PROVIDER'],
           'llm_model': dcfg['Deployment']['LLM_MODEL'],
           'emb_provider': dcfg['Deployment']['EMB_PROVIDER'],
           'emb_model': dcfg['Deployment']['EMB_MODEL']}
    return ModelConfig(model_support=options, model_select=sel)


# API for http://127.0.0.1:8000/api/models
@app.put("/api/models")  # Updated endpoint
async def save_config(options: ModelSelect):
    print(f'PUT: /api/models')
    dcfg['Deployment']['LLM_PROVIDER'] = options.llm_provider
    dcfg['Deployment']['LLM_MODEL'] = options.llm_model
    dcfg['Deployment']['EMB_PROVIDER'] = options.emb_provider
    dcfg['Deployment']['EMB_MODEL'] = options.emb_model

    # Load the original TOML file with tomlkit to preserve structure and comments
    with open(os.path.join(app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
        dyn_config = tomlkit.parse(f.read())

    # Update the TOML structure with new values
    dyn_config['Deployment']['LLM_PROVIDER'] = options.llm_provider
    dyn_config['Deployment']['LLM_MODEL'] = options.llm_model
    dyn_config['Deployment']['EMB_PROVIDER'] = options.emb_provider
    dyn_config['Deployment']['EMB_MODEL'] = options.emb_model

    # Write the updated TOML back to the file
    with open(os.path.join(app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(dyn_config))
        f.flush()

    return {"message": "Configuration updated successfully"}


def remove_useless(doc_list):
    # Get the latest document list
    latest_documents = [doc.strip() for doc in doc_list]

    # Get the path to the local_docs folder
    local_docs_dir = os.path.join(app_root, 'local_docs')

    # Get the list of all files in the local_docs folder
    all_files = os.listdir(local_docs_dir)

    # Identify the files that are not in the latest document list
    useless_files = [file for file in all_files if file not in latest_documents]

    # Remove the useless files
    for file in useless_files:
        file_path = os.path.join(local_docs_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Removed the useless: {file_path}")


@app.post("/api/upload-documents")
async def upload_documents(documents: List[UploadFile] = File(...),
                           system_prompt: str = Form(...), document_list: str = Form(...)):
    try:
        # Validate that at least one document is uploaded
        if not documents:
            raise HTTPException(status_code=422, detail="No documents were uploaded.")

        # Validate that the system prompt is not empty
        if not system_prompt.strip():
            raise HTTPException(status_code=422, detail="System prompt cannot be empty.")

        if not os.path.exists(LOCAL_DOCS_DIR):
            os.makedirs(LOCAL_DOCS_DIR)  # Ensure the directory for saving files exists

        file_names = []
        for document in documents:
            file_path = os.path.join(LOCAL_DOCS_DIR, document.filename)
            with open(file_path, "wb") as f:
                f.write(await document.read())  # Save the uploaded file content
            file_names.append(document.filename)

        # Update the document list
        documents = document_list.split(',') if document_list else []
        remove_useless(documents)
        # You can further process the document_list here, like removing duplicates

        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(os.path.join(app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Knowledge']['DOCUMENTS'] = ','.join(documents)
        dyn_config['Knowledge']['ROBOT_DESC'] = system_prompt.strip()

        # Write the updated TOML back to the file
        with open(os.path.join(app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(dyn_config))
            f.flush()

        return {"message": "Documents and system prompt uploaded and saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error uploading documents or saving system prompt: {str(e)}")


@app.post("/api/documents")
async def update_documents(system_prompt: str = Form(...), document_list: str = Form(...)):
    try:
        # Update the document list
        documents = document_list.split(',') if document_list else []
        remove_useless(documents)
        # You can further process the document_list here, like removing duplicates

        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(os.path.join(app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Knowledge']['DOCUMENTS'] = ','.join(documents)
        dyn_config['Knowledge']['ROBOT_DESC'] = system_prompt.strip()

        # Write the updated TOML back to the file
        with open(os.path.join(app_root, "backend", "dyn_config.toml"), "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(dyn_config))
            f.flush()

        return {"message": "Documents and system prompt uploaded and saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error uploading documents or saving system prompt: {str(e)}")


@app.get("/api/documents")
async def fetch_documents():
    try:
        # Fetch the list of documents and system prompt
        documents = dcfg['Knowledge']['DOCUMENTS'].split(',') if dcfg['Knowledge']['DOCUMENTS'] else []
        system_prompt = dcfg['Knowledge']['ROBOT_DESC']

        return {
            "documents": documents,
            "system_prompt": system_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents and system prompt: {str(e)}")

import webbrowser
@app.on_event("startup")
async def startup_event():
    webbrowser.open_new_tab(user_url)

@app.on_event("shutdown")
async def shutdown_event():
    # 在这里执行应用关闭时需要做的操作，如关闭数据库连接等
    print("Application shutdown")


# Function to stop the uvicorn server and quit the application
def exit_app():
    global server_thread
    # Here you need to add code to gracefully stop the uvicorn server
    # Since uvicorn does not have a built - in way to stop the server from another thread,
    # you can use a more complex solution like a signal or a flag to stop the server
    # For simplicity, we just quit the QApplication here
    app.quit()

if __name__ == "__main__":
    uvicorn.run('http_server:app', host="127.0.0.1", port=8000, reload=False)

