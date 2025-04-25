import os, sys, re
import shutil
from typing import List, Dict, Union, Tuple
from pydantic import BaseModel
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

from langchain_core.messages import HumanMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from pypandoc import convert_file as cvt_doctype
from uni_config import UniConfig


class ModelConfig():
    def __init__(self, app_root, logger, cfg: UniConfig):
        # self.super().__init__()
        self.logger = logger
        self.app_root = app_root
        self.LOCAL_DOCS_DIR = os.path.abspath(os.path.join(app_root, "local_docs"))
        self.cfg = cfg
        # Load documents in the format of PDF,txt,docx,csv and etc.
        self.files: list = cfg.get_documents()  #dcfg['Knowledge']['DOCUMENTS']  # os.getenv("DOCUMENTS")
        self.robot_desc: str = cfg.get_robot_desc()  #dcfg['Knowledge']['ROBOT_DESC']  # os.getenv("ROBOT_DESC")
        self.logger = logger

    def local_docs_dir(self):
        return self.LOCAL_DOCS_DIR

    def instantiate_llm(self, llm_provider: str, llm_model: str):
        if llm_provider.upper() == 'OPENAI':
            llm = ChatOpenAI(model=llm_model, temperature=0.3)
        elif llm_provider.upper() == 'MOONSHOT':
            llm = Moonshot(model=llm_model)
        elif llm_provider.upper() == 'BAICHUAN':
            llm = ChatBaichuan(model=llm_model, temperature=0.3)
        elif llm_provider.upper() == 'ZHIPUAI':
            llm = ChatZhipuAI(model=llm_model, temperature=0.3)
        elif llm_provider.upper() == 'DEEPSEEK':
            llm = ChatDeepSeek(model=llm_model, temperature=0.3)
        elif llm_provider.upper() == 'DASHSCOPE':
            llm = ChatTongyi(model=llm_model, top_p=0.3)
        elif llm_provider.upper() == 'OLLAMA':
            llm = ChatOllama(model=llm_model, temperature=0.3)
        else:
            # raise RuntimeWarning(f'LLM provider {llm_provider} is not supported yet.')
            self.logger.error(f'LLM provider {llm_provider} is not supported. '
                              f'Default LLM config shall be taken.')
            self.cfg.update_llmconfig(*self.cfg.get_default_llmconfig())
            self.logger.warning(f'Please close and restart the app to take new LLM config effective...')
            while True:
                pass
        return llm

    def instantiate_emb(self, emb_provider: str, emb_model: str):
        if emb_provider.upper() == 'OPENAI':
            embeddings = OpenAIEmbeddings(model=emb_model)  # "text-embedding-ada-002"
        elif emb_provider.upper() == 'BAICHUAN':
            embeddings = BaichuanTextEmbeddings(model=emb_model) if emb_model else BaichuanTextEmbeddings()
        elif emb_provider.upper() == 'ZHIPUAI':
            embeddings = ZhipuAIEmbeddings()  # 'glm-3-turbo'
        elif emb_provider.upper().startswith('OLLAMA'):  # This branch is handled specially.
            self.logger.info(f'NOTE: You have chosen Ollama as embedding framework. '
                             f'Please run up Ollama locally beforehand.')
            assert emb_model, f'One model must be specified in case of Ollama for embedding.'
            embeddings = OllamaEmbeddings(model=emb_model)
        else:
            # raise RuntimeWarning(f'Embedding provider {emb_provider} is not supported. Please check your setting.')
            self.logger.error(f'Embedding provider {emb_provider} is not supported. '
                              f'Default embedding config shall be taken.')
            self.cfg.update_embconfig(*self.cfg.get_default_embconfig())
            self.logger.warning(f'Please close and restart the app to take new embedding config effective...')
            while True:
                pass
        return embeddings

    def read_documents(self)->list:
        pages = []
        for file in self.files:
            file_path = os.path.join(self.LOCAL_DOCS_DIR, file.strip())
            if not os.path.exists(file_path):
                self.logger.warn(f'{file_path} does not exist and be ignored.')
                continue
            bn, ext = os.path.splitext(file_path)
            assert len(ext.strip()) > 0, f'Extension name is missing from {file_path}'
            if ext.lower() == '.md':
                # Considering of loading markdown needing NLTK data. It makes it complicated.
                # Here a workaround is that markdown files are firstly converted to Word and
                # then loaded as Word documents.
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
                self.logger.info(f'Load text document {file_path} ...')
                loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
                pages.extend(text_splitter.split_documents(documents))
                assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
            elif ext.lower() == '.md':
                # Load .MD document
                self.logger.info(f'Load markdown document {file_path} ...')
                try:
                    loader = UnstructuredMarkdownLoader(file_path, mode='elements',
                                                        autodetect_coding=True, strategy="fast", )
                except Exception as e:
                    raise RuntimeError(f'Loading {file_path} failed. {repr(e)}')
                documents = loader.load()
                text_splitter = MarkdownTextSplitter.from_language(language=Language("markdown"),
                                                                   chunk_size=300, chunk_overlap=20)
                pages.extend(text_splitter.split_documents(documents))
                assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
            elif ext.lower() == '.pdf':
                # Load .PDF document
                self.logger.info(f'Load PDF document {file_path} ...')
                loader = PyMuPDFLoader(file_path)
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
                doc_pages = text_splitter.split_documents(documents)
                pages.extend(doc_pages)
                assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
            elif ext.lower() == '.docx':
                # Load Word document
                self.logger.info(f'Load Word document {file_path} ...')
                loader = Docx2txtLoader(file_path=file_path)
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
                doc_pages = text_splitter.split_documents(documents)
                pages.extend(doc_pages)
                assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
            elif ext.lower() == '.csv':
                # Load CSV document
                self.logger.info(f'Load CSV document {file_path} ...')
                loader = CSVLoader(file_path=file_path, encoding='utf-8')
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
                doc_pages = text_splitter.split_documents(documents)
                pages.extend(doc_pages)
                assert len(pages) > 0, f'No content is loaded yet. Please check document {file_path}'
            else:
                raise RuntimeWarning(f'File type {ext} is not supported yet.')

        return pages

class RagService():
    # Maintain history
    store = {}  # Keep all chat history. key:session_id,value:chat message
    memory_key = "history"
    hb_size_limit = 128

    context_q_system_prompt = (
        "Given a chat history and the latest user question which might reference context in the chat history, "
        "formulate a standalone question which can be understood without the chat history. "
        "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
    )

    def __init__(self, app_root, logger):
        # self.super().__init__()
        self._local_docs_dir = None
        self.app_root = app_root
        self.logger = logger
        self.cfg = UniConfig(app_root, logger)
        self.modconfig = ModelConfig(app_root, logger, self.cfg)
        self._conversation_chain = None

    @property
    def msg_chain(self):
        return self._conversation_chain

    def remove_useless(self, doc_list: list):
        # Get the latest document list
        latest_documents = [doc.strip() for doc in doc_list]

        # Get the list of all files in the local_docs folder
        all_files = os.listdir(self._local_docs_dir)

        # Identify the files that are not in the latest document list
        useless_files = [f for f in all_files if f not in latest_documents]

        # Remove the useless files
        for f in useless_files:
            file_path = os.path.join(self._local_docs_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                self.logger.info(f"Removed the useless: {file_path}")

    def _embed_documents(self):
        pages = self.modconfig.read_documents()
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

        embeddings = self.modconfig.instantiate_emb(*self.cfg.retrieve_embconfig())

        # Choose vector DB and fill the DB
        db = FAISS.from_documents(texts, embeddings)
        # Get retriever and extract top results
        retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 3})

        return retriever

    def get_session_history(self, session_id) -> BaseChatMessageHistory:  # A key/session_id pair for a question/answer pair
        if session_id not in self.store:
            self.logger.info(f'Create session \"{session_id}\"')
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def setup_service(self, local_docs_dir, reset: bool = False):
        if reset:
            self.cfg.reload_config()
            self.store.clear()
        self._local_docs_dir = local_docs_dir

        retriever = self._embed_documents()

        llm = self.modconfig.instantiate_llm(*self.cfg.retrieve_llmconfig())

        # Step 1: Contextualize the query based on chat history
        contextualize_query_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.context_q_system_prompt),
                MessagesPlaceholder(variable_name=self.memory_key),
                ("human", "{input}"),
            ]
        )

        # Step 2: Build a history-aware retriever to replace classic retriever in following steps.
        history_aware_retriever = create_history_aware_retriever(
            llm,
            retriever,
            contextualize_query_prompt
        )

        # Step 3: Build system prompt
        deployment = self.cfg.get_deployment_profile()
        system_prompt = (f"""{self.cfg.get_robot_desc()}。
                       你的任务是根据下述给定的已知信息回答用户问题。
                       确保你的回复完全依据下述已知信息，不要编造答案。
                       请用中文回答用户问题。
                       你采用了{deployment['llm_provider']}大语言模型{deployment['llm_model']}。
        
                       已知信息:""" +
                         """"{context} """)

        # Step 4: Define question-answer prompt with history for later conversation.
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name=self.memory_key),
            ("human", "{input}")
        ])

        # Step 5: Set up a sub-chain for question-answer purpose. LLM | Prompt
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        # Step 6: Construct the chain based on RAG+History for multi-loop question-answer.
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Step 7: Construct runnable object of RAG+History chain.
        conversation_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key=self.memory_key,
            output_messages_key="answer",
        )

        self._conversation_chain = conversation_rag_chain

    def _split_ai_answer(self, ai_message: str)->Tuple[str, str]:
        ai_thinks = []
        m_thinks = re.findall(r'<think>([\s\S]*)</think>', ai_message)
        if len(m_thinks) > 0:
            [ai_thinks.append(th.strip()) for th in m_thinks if len(th.strip()) > 0]
            if len(ai_thinks) > 0:
                # reasoning = ('<<<<<< 推理开始 >>>>>>\n\n' + '\n------\n'.join(ai_thinks)
                #              + '\n\n<<<<<< 推理完成 >>>>>>\n\n')
                ai_reasoning = '\n'.join(ai_thinks)
            else:
                ai_reasoning = ''
        else:
            ai_reasoning = ''
        if len(ai_reasoning) > 0:
            m_summary = re.match(r'[\s\S]*</think>([\s\S]*)', ai_message)
            if m_summary:
                ai_summary = m_summary.group(1).strip()
            else:
                ai_summary = ''
        else:
            ai_summary = ai_message.strip()
        return ai_summary, ai_reasoning

    def __ask__(self, session_id: str, question: str)->Tuple[str,str]:
        output = self._conversation_chain.invoke(
            {'input': question},
            config={'configurable': {'session_id': session_id}}
        )
        ai_answering, ai_reasoning = self._split_ai_answer(output['answer'])
        # Add the summary answer to the chat history only
        session_history = self.get_session_history(session_id)
        if session_history.messages[-1].type == 'ai':
            session_history.messages[-1].content = ai_answering  # Exclude reasoning
        num_excess = len(session_history.messages) - self.hb_size_limit
        if num_excess > 0:
            self.logger.info(f'Discard the earliest {num_excess} messages as history buffer size imit.')
            [session_history.messages.pop(0) for _ in range(num_excess)]
        return ai_answering, ai_reasoning

    def restart_service(self):
        self.setup_service(self._local_docs_dir, reset=True)
