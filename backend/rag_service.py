import os, sys
import shutil
# import uvicorn
# from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import toml
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
from pypandoc import convert_file as cvt_doctype
# from starlette.middleware.cors import CORSMiddleware
# from starlette.staticfiles import StaticFiles
from logging_config import setup_logging

# Configure logging
logger = setup_logging('run.log')

print(f'python version : {sys.version}')
global app_root
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
    logger.info(f'dotenv={dotenv_path}')
    _ = load_dotenv(dotenv_path=os.path.abspath(dotenv_path))
else:
    logger.info(f'No dotenv found')

scfg_path = os.path.join(app_root, "backend", "sta_config.toml")
dcfg_path = os.path.join(app_root, "backend", "dyn_config.toml")
if not os.path.exists(scfg_path):
    logger.error(f"Could not find {scfg_path}")
if not os.path.exists(dcfg_path):
    logger.error(f"Could not find {dcfg_path}")

# Load config parameters
scfg = toml.load(scfg_path)
dcfg = toml.load(dcfg_path)

factory_cfg_path = os.path.join(app_root, "backend", "factory.toml")
if not os.path.exists(factory_cfg_path):
    logger.error(f"Could not find {factory_cfg_path}")

# Load factory defaults
factory_cfg = toml.load(factory_cfg_path)

# Merge dcfg with factory_cfg for missing or empty fields
def merge_config(target_cfg, source_cfg):
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
            merge_config(values, source_cfg[section])
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
merge_config(dcfg, factory_cfg)

# llm
llm_provider = dcfg['Deployment']['LLM_PROVIDER'].upper()  # os.getenv("LLM_PROVIDER")
if llm_provider:
    logger.info(f'LLM provider : {llm_provider}')
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
    file_path = os.path.abspath(os.path.join(app_root, 'local_docs', file.strip()))
    if not os.path.exists(file_path):
        logger.warn(f'{file_path} does not exist and be ignored.')
        continue
    bn, ext = os.path.splitext(file_path)
    if ext.lower() == '.md':
        # Considering of loading markdown needing NLTK data. It makes it complicated. Here a workaround
        # is that markdown files are firstly converted to Word and then loaded as Word documents.
        if os.path.exists('temp'):
            shutil.rmtree('temp')
        os.makedirs('temp')
        temp_file = os.path.join('temp', os.path.split(file_path)[1])
        temp_file = os.path.splitext(temp_file)[0] + '.docx'
        cvt_doctype(file_path, 'docx', outputfile=temp_file)
        ext = '.docx'
        file_path = temp_file

    if ext.lower() == '.txt':
        # Load .txt document
        print(f'Load text document {file_path} ...')
        loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
    elif ext.lower() == '.md':
        # Load .MD document
        print(f'Load markdown document {file_path} ...')
        try:
            loader = UnstructuredMarkdownLoader(file_path, mode='elements', autodetect_coding=True, strategy="fast", )
        except Exception as e:
            raise RuntimeError(f'Loading {file_path} failed. {repr(e)}')
        documents = loader.load()
        text_splitter = MarkdownTextSplitter.from_language(language=Language("markdown"),
                                                           chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
    elif ext.lower() == '.pdf':
        # Load .PDF document
        print(f'Load PDF document {file_path} ...')
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
    elif ext.lower() == '.docx':
        # Load Word document
        print(f'Load Word document {file_path} ...')
        loader = Docx2txtLoader(file_path=file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
    elif ext.lower() == '.csv':
        # Load CSV document
        print(f'Load CSV document {file_path} ...')
        loader = CSVLoader(file_path=file_path, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
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
