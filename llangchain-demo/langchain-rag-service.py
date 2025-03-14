import os, sys
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.llms.moonshot import Moonshot
# from langchain_community.llms.baichuan import BaichuanLLM
from langchain_community.chat_models import ChatZhipuAI, ChatBaichuan
from langchain_deepseek import ChatDeepSeek
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BaichuanTextEmbeddings, ZhipuAIEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, UnstructuredWordDocumentLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from starlette.middleware.cors import CORSMiddleware


print(f'python version : {sys.version}')

# 加载环境变量，读取本地 .env 文件，里面定义了各种配置参数，包括API_KEY
_ = load_dotenv(find_dotenv())

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
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.01)
elif llm_provider == 'MOONSHOT':
    llm = Moonshot(model=llm_model)
elif llm_provider == 'BAICHUAN':
    llm = ChatBaichuan(model=llm_model, temperature=0.01)
elif llm_provider == 'ZHIPUAI':
    llm = ChatZhipuAI(model=llm_model, temperature=0)
elif llm_provider == 'DEEPSEEK':
    llm = ChatDeepSeek(model=llm_model, temperature=0.01)
else:
    raise RuntimeWarning(f'LLM provider {llm_provider} is not supported yet.')


# Maintain history
store = {}  # 所有用户的聊天记录都保存到store。key:session_id,value:历史聊天记录
memory_key = "chat_history"
# # 2、定义提示词模版、引入MessagesPlaceholder来处理多轮对话
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "你是一个乐于助人的助手。用{language}尽你所能回答所有问题。"),
#     MessagesPlaceholder(variable_name=memory_key),
#     ("human", "{input}"),
# ])

# # 4、使用 LangChain 的链式操作来构建问答链。
# chain = prompt | model

def get_session_history(session_id):  # 一轮对话的内容只存储在一个key/session_id
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# 加载文档,可换成PDF、txt、doc等其他格式文档
files: str = os.getenv("DOCUMENTS")
pages = []
for file in files.split(','):
    file = file.strip()
    # file: str = '../docs/解答手册.md'
    # file: str = "../docs/eBook-How-to-Build-a-Career-in-AI.pdf"
    _, ext = os.path.splitext(file)
    if ext == '.md':
        # 加载MD
        print(f'Load markdown document {file} ...')
        loader = TextLoader(file, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter.from_language(language=Language("markdown"),
                                                                     chunk_size=300, chunk_overlap=20)
        pages.extend(text_splitter.split_documents(documents))
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.pdf':
        # 加载PDF
        print(f'Load PDF document {file} ...')
        loader = PyMuPDFLoader(file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.docx':
        # Load Word document
        print(f'Load Word document...')
        loader = Docx2txtLoader(file_path=file)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    elif ext == '.csv':
        # Load CSV document
        print(f'Load CSV document...')
        loader = CSVLoader(file_path=file, encoding='utf-8')
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        doc_pages = text_splitter.split_documents(documents)
        pages.extend(doc_pages)
        assert len(pages)>0, f'No content is loaded yet. Please check document {file}'
    else:
        raise RuntimeWarning(f'File type {ext} is not supported yet.')

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=10,
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

# 选择向量模型，并灌库
db = FAISS.from_documents(texts, embeddings)
# 获取检索器，选择 top-2 相关的检索结果
retriever = db.as_retriever(search_kwargs={"k": 1})

# 创建带有 system 消息的模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", f"""你是一个对接问题排查机器人，采用来自{llm_provider}的大模型。
               你的任务是根据下述给定的已知信息回答用户问题。
               确保你的回复完全依据下述已知信息，不要编造答案。
               请用中文回答用户问题。

               已知信息:"""+
               """"{context} """),
    # MessagesPlaceholder(variable_name=memory_key),
    ("user", "{question}")
])

# 自定义的提示词参数
chain_type_kwargs = {
    "prompt": prompt_template,
}

# 定义RetrievalQA链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 使用stuff模式将上下文拼接到提示词中
    chain_type_kwargs=chain_type_kwargs,
    retriever=retriever
)

# 构建 FastAPI 应用，提供服务
app = FastAPI()

user_url = "http://localhost:63342/unichat/frontend/index.html"
print(f'Please browse {user_url} for chat.')

# 可选，前端报CORS时
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# 定义请求模型
class QuestionRequest(BaseModel):
    question: str


# 定义响应模型
class AnswerResponse(BaseModel):
    answer: str


# 提供查询接口 http://127.0.0.1:8000/ask
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        # 获取用户问题
        user_question = request.question
        print(f'question:{user_question}')

        # 通过RAG链生成回答
        # answer = qa_chain.run(user_question)
        answer = qa_chain.invoke(user_question)

        # 返回答案
        answer = AnswerResponse(answer=answer['result'])
        print(f'answer:{answer.answer}')
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
