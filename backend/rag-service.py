import os, sys, re
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
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


print(f'python version : {sys.version}')

if getattr(sys, 'frozen', False):
    # 如果是PyInstaller打包的exe
    app_root = os.path.dirname(sys.executable)
else:
    # 普通的Python脚本
    app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
print(f'APP ROOT: {app_root}')

# Load env variables from local .env file. Several parameters are there, including API_KEY.
os.chdir(os.path.dirname(__file__))
dotenv_path=find_dotenv(filename='.env', raise_error_if_not_found=True)
print(f'dotenv={dotenv_path}')
_ = load_dotenv(dotenv_path=os.path.abspath(dotenv_path))

# llm
llm_provider = os.getenv("LLM_PROVIDER")
if llm_provider:
    print(f'LLM provider : {llm_provider}')
    llm_model = os.getenv("LLM_MODEL") or os.getenv(f'{llm_provider}_LLM_MODEL')
    print(f'LLM model : {llm_model}')
else:
    llm_provider = 'OPENAI'
    print(f'LLM provider : {llm_provider} picked by default.')
    llm_model = os.getenv(f'{llm_provider}_LLM_MODEL')
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
files: str = os.getenv("DOCUMENTS")
robot_desc: str = os.getenv("ROBOT_DESC")
pages = []
for file in files.split(','):
    file = os.path.abspath(os.path.join(app_root, file.strip()))
    _, ext = os.path.splitext(file)
    if ext == '.txt':
        # Load .txt document
        print(f'Load text document {file} ...')
        loader = TextLoader(file, encoding='utf-8', autodetect_encoding=True)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.md':
        # Load .MD document
        print(f'Load markdown document {file} ...')
        loader = UnstructuredMarkdownLoader(file, mode='elements', encoding='utf-8')
        documents = loader.load()
        text_splitter = MarkdownTextSplitter.from_language(language=Language("markdown"),
                                                                     chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.pdf':
        # Load .PDF document
        print(f'Load PDF document {file} ...')
        loader = PyMuPDFLoader(file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.docx':
        # Load Word document
        print(f'Load Word document {file} ...')
        loader = Docx2txtLoader(file_path=file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.csv':
        # Load CSV document
        print(f'Load CSV document {file} ...')
        loader = CSVLoader(file_path=file, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
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
    t.id=f'Doc-{j}'

emb_provider = os.getenv('EMB_PROVIDER')
if emb_provider:
    print(f'Embedding provider : {emb_provider}')
    emb_model = os.getenv(f"EMB_MODEL")
    print(f'Embedding model : {emb_model}')
else:
    emb_provider = 'OPENAI'
    print(f'Embedding provider : {emb_provider} picked by default.')
    emb_model = os.getenv(f"{emb_provider}_EMB_MODEL")
    print(f'Embedding model : {emb_model}')
if emb_provider == 'OPENAI':
    embeddings = OpenAIEmbeddings(model=emb_model) #"text-embedding-ada-002"
elif emb_provider == 'BAICHUAN':
    embeddings = BaichuanTextEmbeddings(model=emb_model) if emb_model else BaichuanTextEmbeddings()
elif emb_provider == 'ZHIPUAI':
    embeddings = ZhipuAIEmbeddings() #'glm-3-turbo'
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

               已知信息:"""+
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


# Create FastAPI application for API service
app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(app_root, 'frontend')), 'static')

user_url = "http://localhost:63342/unichat/frontend/index.html"
print(f'Please browse {user_url} for chat.')

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
        answer = msghist_chain.invoke({"input":user_question},
                                      config={"configurable": {"session_id": session_id}})

        ai_answer = answer['answer']
        ai_thinks = []
        thinks = re.findall(r'<think>([\s\S]*)</think>', ai_answer)
        if len(thinks)>0:
            [ai_thinks.append(th.strip()) for th in thinks]
            if len(ai_thinks)>0:
                reasoning = ('<<<<<< 推理开始 >>>>>>\n\n' + '\n------\n'.join(ai_thinks)
                             + '\n\n<<<<<< 推理完成 >>>>>>\n\n')
            else:
                reasoning = ''
        else:
            reasoning = ''
        if len(thinks) > 0:
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


#  Build API for external use
@app.get("/")
async def get_status():
    return {"method": "get", "name": "Chat status"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, app_dir=app_root)
