# unichat brief
Deploy chatbot locally based on RAG technologies. Multiple LLM models are supported. It is easy to setting the LLM model you expects.

# Details

这些代码文件构成了一个智能助手应用程序，包含前端页面、后端服务、样式设置、日志处理、控制台显示以及打包脚本等部分。以下是对各文件的详细介绍：
## 前端文件
### index.html
* 功能：定义了智能助手的 HTML 结构，包含聊天界面、配置模态框等。
* 关键元素：
  * 聊天容器、输入框和发送按钮，用于用户与助手交互。
  * 配置按钮，点击可打开配置模态框。
  * 配置模态框包含模型和知识库两个标签页，用于设置模型参数和管理知识库文档。
### scripts.js
* 功能：实现前端交互逻辑，包括发送消息、管理配置模态框、处理文档上传和删除等。
* 关键函数：
  * sendMessage()：发送用户输入的问题到后端，并显示助手的回复。
  * openConfigModal() 和 closeConfigModal()：打开和关闭配置模态框。
  * addDocuments() 和 deleteSelectedFile()：添加和删除知识库文档。
  * saveKnowledgeBase()：保存知识库文档和系统提示词到后端。
### styles.css
* 功能：定义了应用程序的样式，包括聊天界面、配置模态框、按钮等的外观。
* 关键样式：
  * 聊天容器和消息框的样式，区分用户和助手的消息。
  * 配置模态框的样式，包括标签页、下拉框和保存按钮。
  * 文档列表和操作按钮的样式，如添加、删除和保存按钮。
## 后端文件
### http_server.py
* 功能：使用 FastAPI 框架实现后端 API，处理模型配置、文档上传和获取等请求。
* 关键路由：
  * GET /api/models：获取模型支持和选择的配置信息。
  * PUT /api/models：保存模型配置信息到 dyn_config.toml 文件。
  * GET /api/documents：获取知识库文档列表和系统提示词。
  * POST /api/upload-documents 和 POST /api/documents：上传文档和保存系统提示词到后端。
### console_window.py
* 功能：实现自定义控制台窗口，用于显示日志信息。
* 关键类和方法：
  * CustomConsole：自定义控制台窗口类，包含文本编辑框和切换按钮。
  * append_text()：向控制台窗口添加文本信息。
  * toggle_visibility()：切换控制台窗口的可见性。
### logging_config.py
* 功能：配置日志处理，将日志信息重定向到自定义控制台窗口。
* 关键类和方法：
  * CustomStream：自定义流类，用于将日志信息写入控制台窗口。
  * redirect_stream()：将日志流重定向到指定的流对象。
## 打包脚本
### buildexe.bat
* 功能：使用 PyInstaller 将后端脚本打包成可执行文件，并复制相关文件到打包目录。
  * 关键步骤：
  * 检查 PyInstaller 是否安装。
  * 生成版本信息文件。
  * 使用 PyInstaller 打包后端脚本。
  * 复制配置文件、前端文件、资源文件和文档到打包目录。

综上所述，这些代码文件共同构建了一个完整的智能助手应用程序，包括前端界面、后端服务、日志处理和打包部署等功能。