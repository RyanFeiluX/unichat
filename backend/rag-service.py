import os, sys, re
import shutil
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import toml
import tomlkit  # Import tomlkit for round-trip parsing
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.llms.moonshot import Moonshot
# from langchain_community.llms.baichuan import BaichuanLLM
from langchain_community.chat_models import ChatZhipuAI, ChatBaichuan, ChatTongyi
from langchain_deepseek import ChatDeepSeek
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BaichuanTextEmbeddings, ZhipuAIEmbeddings
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_text_splitters.markdown import MarkdownTextSplitter
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from typing import List, Dict, Union

print(f'python version : {sys.version}')

if getattr(sys, 'frozen', False):
    # 如果是PyInstaller打包的exe
    app_root = os.path.dirname(sys.executable)
else:
    # 普通的Python脚本
    app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
print(f'APP ROOT: {app_root}')

# Load env variables from local .env file. Several parameters are there, including API_KEY.
dotenv_path = find_dotenv(filename='.env', raise_error_if_not_found=False)
if dotenv_path:
    print(f'dotenv={dotenv_path}')
    _ = load_dotenv(dotenv_path=os.path.abspath(dotenv_path))

# Load config parameters
scfg = toml.load(os.path.join(app_root, "backend", "sta_config.toml"))
dcfg = toml.load(os.path.join(app_root, "backend", "dyn_config.toml"))

# Load factory defaults
factory_cfg = toml.load(os.path.join(app_root, "backend", "factory.toml"))

# Merge dcfg with factory_cfg for missing or empty fields
def merge_with_factory_config(target_cfg, source_cfg):
    """
    Merge the target configuration with the factory defaults.

    This function ensures that empty fields in the target configuration
    are filled with values from the factory configuration.

    Args:
        target_cfg (dict): The target configuration dictionary to be updated.
        source_cfg (dict): The factory configuration dictionary containing default values.
    """
    for section, values in target_cfg.items():
        if values is None:
            target_cfg[section] = source_cfg[section] if section in source_cfg else None
        elif isinstance(values, dict):
            if section not in source_cfg:
                continue
            merge_with_factory_config(values, source_cfg[section])
        elif isinstance(values, list):
            if section not in source_cfg:
                continue
            if values is []:
                target_cfg[section] = source_cfg[section]
        elif isinstance(values, str):
            if section not in source_cfg:
                continue
            if values == '' or values is None:
                target_cfg[section] = source_cfg[section]


# Ensure dynamic configuration is merged with factory defaults
merge_with_factory_config(dcfg, factory_cfg)

# llm
llm_provider = dcfg['Deployment']['LLM_PROVIDER'].upper()  # os.getenv("LLM_PROVIDER")
if llm_provider:
    print(f'LLM provider : {llm_provider}')
    # llm_model = os.getenv("LLM_MODEL") or os.getenv(f'{llm_provider}_LLM_MODEL')
    llm_model = (dcfg['Deployment']['LLM_MODEL']
                 or scfg['Providers'][llm_provider][f'{llm_provider}_LLM_MODEL'].split(',')[0])
    print(f'LLM model : {llm_model}')
else:
    llm_provider = 'OPENAI'
    print(f'LLM provider : {llm_provider} picked by default.')
    # llm_model = os.getenv(f'{llm_provider}_LLM_MODEL')
    llm_model = scfg['Deployment'][llm_provider][f'{llm_provider}_LLM_MODEL'].split(',')[0]
    print(f'LLM model : {llm_model}')
if llm_provider == 'OPENAI':
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
elif llm_provider == 'MOONSHOT':
    llm = Moonshot(model=llm_model)
elif llm_provider == 'BAICHUAN':
    llm = ChatBaichuan(model=llm_model, temperature=0.3)
elif llm_provider == 'ZHIPUAI':
    llm = ChatZhipuAI(model=llm_model, temperature=0.3)
elif llm_provider == 'DEEPSEEK':
    llm = ChatDeepSeek(model=llm_model, temperature=0.3)
elif llm_provider == 'DASHSCOPE':
    llm = ChatTongyi(model=llm_model, top_p=0.3)
elif llm_provider == 'OLLAMA':
    llm = ChatOllama(model=llm_model, temperature=0.3)
else:
    raise RuntimeWarning(f'LLM provider {llm_provider} is not supported yet.')

# Load documents in the format of PDF,txt,docx,csv and etc.
files: str = dcfg['Knowledge']['DOCUMENTS']  # os.getenv("DOCUMENTS")
robot_desc: str = dcfg['Knowledge']['ROBOT_DESC']  # os.getenv("ROBOT_DESC")
pages = []
for file in files.split(','):
    file = os.path.abspath(os.path.join(app_root, 'local_docs', file.strip()))
    bn, ext = os.path.splitext(file)
    if ext.lower() == '.md':
        # Considering of loading markdown needing NLTK data. It makes it complicated. Here a workaround
        # is that markdown files are firstly converted to Word and then loaded as Word documents.
        from pypandoc import convert_file as cvt_doctype
        import tempfile
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        os.makedirs('temp')
        temp_file = os.path.join('temp', os.path.split(file)[1])
        temp_file = os.path.splitext(temp_file)[0] + '.docx'
        cvt_doctype(file, 'docx', outputfile=temp_file)
        ext = '.docx'
        file = temp_file

    if ext.lower() == '.txt':
        # Load .txt document
        print(f'Load text document {file} ...')
        loader = TextLoader(file, encoding='utf-8', autodetect_encoding=True)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file}'
    elif ext.lower() == '.md':
        # Load .MD document
        print(f'Load markdown document {file} ...')
        try:
            loader = UnstructuredMarkdownLoader(file, mode='elements', autodetect_coding=True, strategy="fast",)
        except Exception as e:
            raise RuntimeError(f'Loading {file} failed. {repr(e)}')
        documents = loader.load()
        text_splitter = MarkdownTextSplitter.from_language(language=Language("markdown"),
                                                           chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file}'
    elif ext.lower() == '.pdf':
        # Load .PDF document
        print(f'Load PDF document {file} ...')
        loader = PyMuPDFLoader(file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file}'
    elif ext.lower() == '.docx':
        # Load Word document
        print(f'Load Word document {file} ...')
        loader = Docx2txtLoader(file_path=file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file}'
    elif ext.lower() == '.csv':
        # Load CSV document
        print(f'Load CSV document {file} ...')
        loader = CSVLoader(file_path=file, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file}'
    else:
        raise RuntimeWarning(f'File type {ext} is not supported yet.')

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=20,
    length_function=len,
    add_start_index=True,
)
texts = text_splitter.create_documents(
    [page.page_content for page in pages]
)
for j, t in enumerate(texts):
    t.id = f'Doc-{j}'

emb_provider = dcfg['Deployment']['EMB_PROVIDER'].upper()  # os.getenv('EMB_PROVIDER')
if emb_provider:
    print(f'Embedding provider : {emb_provider}')
    emb_model = dcfg['Deployment']['EMB_MODEL']  # os.getenv(f"EMB_MODEL")
    print(f'Embedding model : {emb_model}')
else:
    emb_provider = 'OPENAI'
    print(f'Embedding provider : {emb_provider} picked by default.')
    emb_model = dcfg['Deployment'][f"{emb_provider}_EMB_MODEL"]  # os.getenv(f"{emb_provider}_EMB_MODEL")
    print(f'Embedding model : {emb_model}')
if emb_provider == 'OPENAI':
    embeddings = OpenAIEmbeddings(model=emb_model)  # "text-embedding-ada-002"
elif emb_provider == 'BAICHUAN':
    embeddings = BaichuanTextEmbeddings(model=emb_model) if emb_model else BaichuanTextEmbeddings()
elif emb_provider == 'ZHIPUAI':
    embeddings = ZhipuAIEmbeddings()  # 'glm-3-turbo'
elif emb_provider.startswith('OLLAMA'):  # This branch is handled specially.
    print(f'NOTE: You have chosen Ollama as embedding framework. Please run up Ollama locally beforehand.')
    assert emb_model, f'One model must be specified in case of Ollama for embedding.'
    embeddings = OllamaEmbeddings(model=emb_model)
else:
    raise RuntimeWarning(f'Embedding provider {emb_provider} is not supported. Please check your setting.')

# Maintain history
store = {}  # Keep all chat history. key:session_id,value:chat message
memory_key = "history"

context_system_prompt = (
    "Given a chat history and the latest user question which might reference context in the chat history, "
    "formulate a standalone question which can be understood without the chat history. "
    "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
)

context_question_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", context_system_prompt),
        MessagesPlaceholder(memory_key),
        ("human", "{input}"),
    ]
)


def get_session_history(session_id) -> BaseChatMessageHistory:  # A key/session_id pair for a question/answer pair
    if session_id not in store:
        # print(f'Create session \"{session_id}\"')
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# Choose vector DB and fill the DB
db = FAISS.from_documents(texts, embeddings)
# Get retriever and extract top results
retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 3})

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, context_question_prompt_template
)

# System message template
system_prompt = (f"""{robot_desc}。
               你的任务是根据下述给定的已知信息回答用户问题。
               确保你的回复完全依据下述已知信息，不要编造答案。
               请用中文回答用户问题。
               你采用了{llm_provider}大语言模型{llm_model}。

               已知信息:""" +
                 """"{context} """)
# Define prompt template and add MessagesPlaceholder for multi-q/a chat
qa_prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name=memory_key),
    ("user", "{input}")
])

qa_chain = create_stuff_documents_chain(llm, qa_prompt_template)
rag_qa_chain = create_retrieval_chain(history_aware_retriever, qa_chain)
msghist_chain = RunnableWithMessageHistory(
    rag_qa_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key=memory_key,
    output_messages_key="answer",
)

LOCAL_DOCS_DIR = os.path.join(app_root, "local_docs")

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


@app.post("/api/upload-documents")
async def upload_documents(documents: List[UploadFile] = File(...), system_prompt: str = Form(...), document_list: str = Form(...)):
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
        document_list = document_list.split(',') if document_list else []
        # You can further process the document_list here, like removing duplicates

        # Load the original TOML file with tomlkit to preserve structure and comments
        with open(os.path.join(app_root, "backend", "dyn_config.toml"), "r", encoding="utf-8") as f:
            dyn_config = tomlkit.parse(f.read())

        # Update the TOML structure with new values
        dyn_config['Knowledge']['DOCUMENTS'] = ','.join(document_list)
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


user_url = "http://localhost:63342/unichat/frontend/index.html"
print(f'If the chat page is not opened in few seconds, please click the link {user_url} instead.')

import webbrowser
@app.on_event("startup")
async def startup_event():
    webbrowser.open_new_tab(user_url)

@app.on_event("shutdown")
async def shutdown_event():
    # 在这里执行应用关闭时需要做的操作，如关闭数据库连接等
    print("Application shutdown")

if __name__ == "__main__":
    uvicorn.run('rag-service:app', host="127.0.0.1", port=8000, reload=False)
