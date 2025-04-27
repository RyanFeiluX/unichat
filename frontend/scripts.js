BASE_URL="http://localhost:8000"

marked.setOptions({sanitize: true});

let hasUnsavedModelChanges = false;
let hasUnsavedKnowledgeChanges = false;

// Store original values of dropdowns
let originalLlmProvider;
let originalLlmModel;
let originalEmbeddingProvider;
let originalEmbeddingModel;
let originalSystemPrompt;

// Add a variable to store the original document list
let originalDocumentList = [];
// Add a flag to indicate if the document list has changed
let hasUnsavedDocumentListChanges = false;

// Generate a unique session ID
function generateSessionId() {
    return crypto.randomUUID();
}

// Get or create a session ID
let sessionId = sessionStorage.getItem('sessionId');
if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem('sessionId', sessionId);
}
function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;

    appendMessage('user', userInput);

    const data = {
        question: userInput,
        session_id: sessionId
    };

    fetch(`${BASE_URL}/ask`, { // Use BASE_URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .catch(error => {
        console.error('Error during fetch:', error);
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(errorText => {
                throw new Error(`Server error: ${errorText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        appendMessage('assistant', data.answer, think=data.think);
    })
    .catch(error => {
        if (error instanceof TypeError) {
            console.error('Network error:', error);
            appendMessage('assistant', '网络错误，请检查您的网络连接。');
        } else {
            console.error('Server error:', error);
            appendMessage('assistant', '抱歉，服务器处理您的请求时出现错误。');
        }
    });

    document.getElementById('user-input').value = '';
    document.getElementById('user-input').focus();
}

function appendMessage(sender, message, think=null) {
    const chatBox = document.getElementById('chat-box');
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group';

    if (think && think.trim()!== "") {
        const reasoningElement = document.createElement('div');
        reasoningElement.className = 'assistant reasoning';
        reasoningElement.innerHTML = marked.parse(think);
        messageGroup.appendChild(reasoningElement);
    }

    const messageElement = document.createElement('div');
    messageElement.className = sender;  //'assistant';
    // Use marked to render the Markdown message
    messageElement.innerHTML = marked.parse(message);
    messageGroup.appendChild(messageElement);

    if (sender == 'assistant') {
        chatBox.appendChild(messageGroup);
    } else {
        chatBox.appendChild(messageElement);
    }
//    chatBox.appendChild(messageGroup);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function keyDown(e) {
    var keycode = e.keyCode || e.which || e.charCode;

    if (keycode == 13) //Enter=13
    {
        sendMessage(); //Invoke the function to send the message when the Enter key is pressed.
    }
}

window.onbeforeunload = function(){
    if (hasUnsavedModelChanges && hasUnsavedKnowledgeChanges) {
        return '您在模型配置和知识库配置中均有未保存的更改。确定要离开此页面吗？';
    } else if (hasUnsavedModelChanges) {
        return '您在模型配置中有未保存的更改。确定要离开此页面吗？';
    } else if (hasUnsavedKnowledgeChanges) {
        return '您在知识库配置中有未保存的更改。确定要离开此页面吗？';
    }
    var html = document.querySelector("html");
    sessionStorage.setItem("pre",html.innerHTML);
}

window.addEventListener("load",function(){
    var before = sessionStorage.getItem("loadtime");
    if(!before){
        sessionStorage.setItem("loadtime",1);
    }else{
        sessionStorage.setItem("loadtime",parseInt(before)+1);
    }//sessionStorage采用的是key-value形式，第二个参数为字符串类型，如果不对before值作整型处理，javascript会认为是字符串的拼接，这样就无法起到数字递增的效果
    var storetime = sessionStorage.getItem("loadtime");
    //console.log(storetime);
    if(storetime>1){
        var preHtml = sessionStorage.getItem("pre");
        var html = document.querySelector("html");
        html.innerHTML = preHtml;

    }else if(storetime==1){
        sessionStorage.removeItem("pre");
    }

    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;

    //后续控制交互行为或者处理业务的js代码
})

// Function to fetch config changes suspended state and update icon color
async function queryConfigChangesIcon() {
    try {
        const response = await fetch(`${BASE_URL}/api/config-suspense`, {method: 'GET'});
        const data = await response.json();
        const icon = document.getElementById('config-changes-icon');
        if (data.suspense) {
            icon.classList.remove('green');
            icon.classList.add('red');
        } else {
            icon.classList.remove('red');
            icon.classList.add('green');
        }
        updateApplyConfigButtonState();
    } catch (error) {
        console.error('Error in fetching config changes suspended state:', error);
    }
}
// Call the function when the page loads
window.addEventListener('DOMContentLoaded', function() {
    queryConfigChangesIcon();
});

function openConfigModal() {
    const configModal = document.getElementById('config-modal');
    configModal.style.display = 'block'; // Ensure the modal is displayed
}

function closeConfigModal() {
    const configModal = document.getElementById('config-modal');
    const closeButton = configModal.getElementsByClassName('close')[0];
    if (closeButton.disabled) {
        return; // If the close button is disabled, do nothing
    }
    console.log('hasUnsavedModelChanges:', hasUnsavedModelChanges);
    console.log('hasUnsavedKnowledgeChanges:', hasUnsavedKnowledgeChanges);
    console.log('hasUnsavedDocumentListChanges:', hasUnsavedDocumentListChanges);
    if (hasUnsavedModelChanges || hasUnsavedKnowledgeChanges || hasUnsavedDocumentListChanges) {
        showCustomAlert('确认', '您有未保存的更改。是否要丢弃更改并关闭配置页面？', () => {
            const configModal = document.getElementById('config-modal');
            configModal.style.display = 'none'; // Ensure the modal is hidden

            // Rollback model tab selections
            document.getElementById('llm-provider').value = originalLlmProvider;
            updateLlmModels();
            document.getElementById('llm-model').value = originalLlmModel;
            document.getElementById('embedding-provider').value = originalEmbeddingProvider;
            updateEmbeddingModels();
            document.getElementById('embedding-model').value = originalEmbeddingModel;
            updateProviderDescription();

            // Rollback knowledge tab system prompt
            document.getElementById('system-prompt').value = originalSystemPrompt;

            // Rollback document list
            if (hasUnsavedDocumentListChanges) {
                revertDocumentList(originalDocumentList)
            }

            // Disable save buttons
            disableSaveButton('model-tab');
            disableSaveButton('knowledge-tab');

            hasUnsavedModelChanges = false;
            hasUnsavedKnowledgeChanges = false;
        });
    } else {
        const configModal = document.getElementById('config-modal');
        configModal.style.display = 'none'; // Ensure the modal is hidden
    }
}

// Attach the openConfigModal function to the config button
document.addEventListener('DOMContentLoaded', () => {
    // Disable "保存" buttons initially
    document.querySelectorAll('.save-button').forEach(button => {
        button.disabled = true;
        button.style.backgroundColor = '#6c757d'; // Gray color for disabled state
        button.style.cursor = 'not-allowed';
    });

    // Attach event listeners for modal and tabs
    document.getElementById('config-button').addEventListener('click', openConfigModal);
    document.querySelector('.close').addEventListener('click', closeConfigModal);
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('keydown', keyDown);

    // Attach event listeners for model tab
    document.getElementById('llm-provider').addEventListener('change', () => {
        updateLlmModels();
        updateProviderDescription();
        enableSaveButton('model-tab'); // Enable save button when LLM provider changes
        hasUnsavedModelChanges = true;
    });
    document.getElementById('llm-model').addEventListener('change', () => {
        enableSaveButton('model-tab'); // Enable save button when LLM model changes
        hasUnsavedModelChanges = true;
    });
    document.getElementById('embedding-provider').addEventListener('change', () => {
        updateEmbeddingModels();
        enableSaveButton('model-tab'); // Enable save button when embedding provider changes
        hasUnsavedModelChanges = true;
    });
    document.getElementById('embedding-model').addEventListener('change', () => {
        enableSaveButton('model-tab'); // Enable save button when embedding model changes
        hasUnsavedModelChanges = true;
    });
    document.getElementById('save-model-button').addEventListener('click', () => {
        saveModelConfig();
//        hasUnsavedModelChanges = false;
    });

    // Attach event listeners for knowledge tab
    document.getElementById('add-document-button').addEventListener('click', triggerFileInput);
    document.getElementById('delete-document-button').addEventListener('click', deleteSelectedFile);
    document.getElementById('document-input').addEventListener('change', addDocuments);
    document.getElementById('system-prompt').addEventListener('input', () => {
        enableSaveButton('knowledge-tab');
        hasUnsavedKnowledgeChanges = true;
    });
    document.getElementById('save-knowledge-button').addEventListener('click', () => {
        saveKnowledgeBase();
//        hasUnsavedKnowledgeChanges = false;
    });

    // Initialize tabs
    initializeModelTab();
    initializeKnowledgeTab();

    updateApplyConfigButtonState();

    document.getElementById('apply-config-button').addEventListener('click', () => {
        applyConfigChanges();
//        queryConfigChangesIcon();
    });
});

let llmModelsData = {};
let embeddingModelsData = {};

provider_intro = {}

function initializeModelTab() {
    fetch(`${BASE_URL}/api/models`, { // Fetch model configuration options
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.model_support || !Array.isArray(data.model_support)) {
            throw new Error('Invalid or missing model_support data.');
        }
        if (!data.model_select) {
            throw new Error('Invalid or missing model_select data.');
        }

        // Populate LLM provider dropdown
        populateSelect('llm-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));

        // Populate embedding provider dropdown
        populateSelect('embedding-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));

        // Populate LLM models based on the selected provider
        llmModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.llm_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
//        updateLlmModels();

        // Populate embedding models based on the selected provider
        embeddingModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.emb_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
//        updateEmbeddingModels();

        // Set selected values based on model_select
        document.getElementById('llm-provider').value = data.model_select.llm_provider || '';
        updateLlmModels(); // Populate models based on selected provider
        document.getElementById('llm-model').value = data.model_select.llm_model || '';
        document.getElementById('embedding-provider').value = data.model_select.emb_provider || '';
        updateEmbeddingModels(); // Populate models based on selected provider
        document.getElementById('embedding-model').value = data.model_select.emb_model || '';

        // Store original values
        originalLlmProvider = data.model_select.llm_provider || '';
        originalLlmModel = data.model_select.llm_model || '';
        originalEmbeddingProvider = data.model_select.emb_provider || '';
        originalEmbeddingModel = data.model_select.emb_model || '';

        // Update provider description
        // Organize provider descriptions
        provider_intro = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.prov_intro || '暂无相关介绍。'; // Default description if none provided
            return acc;
        }, {});
        updateProviderDescription();

        queryConfigChangesIcon();
    })
    .catch(error => console.error('Error fetching model configuration:', error));

    disableSaveButton('model-tab'); // Disable save button initially
}

function updateLlmModels() {
    const selectedProvider = document.getElementById('llm-provider').value;
    const models = llmModelsData[selectedProvider] || [];
    populateSelect('llm-model', models);
    updateProviderDescription(); // Update provider description when LLM provider changes
}

function updateEmbeddingModels() {
    const selectedProvider = document.getElementById('embedding-provider').value;
    const models = embeddingModelsData[selectedProvider] || [];
    populateSelect('embedding-model', models);
}

function populateSelect(elementId, options) {
    const select = document.getElementById(elementId);
    select.innerHTML = ''; // Clear existing options
    if (Array.isArray(options)) { // Ensure options is a valid array
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.value;
            opt.textContent = option.label;
            select.appendChild(opt);
        });
    } else {
        console.warn(`Invalid options provided for elementId: ${elementId}`);
    }
}

function saveModelConfig() {
    const llmProvider = document.getElementById('llm-provider').value;
    const llmModel = document.getElementById('llm-model').value;
    const embProvider = document.getElementById('embedding-provider').value;
    const embModel = document.getElementById('embedding-model').value;

    // Validate configuration values
    if (!llmProvider || !llmModel || !embProvider || !embModel) {
//        alert('请确保所有配置项均已选择有效值。');
        showCustomAlert ('警告', '请确保所有配置项均已选择有效值。');
        return;
    }

    const model_config = {
        llm_provider: llmProvider,
        llm_model: llmModel,
        emb_provider: embProvider,
        emb_model: embModel,
    };

    fetch(`${BASE_URL}/api/models`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(model_config)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(errorText => {
                throw new Error(`Server error: ${errorText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status_ok) {
            showCustomAlert('成功', data.message);
            disableSaveButton('model-tab'); // Disable save button after saving

            // Update original values after successful save
            originalLlmProvider = llmProvider;
            originalLlmModel = llmModel;
            originalEmbeddingProvider = embProvider;
            originalEmbeddingModel = embModel;
            hasUnsavedModelChanges = false;

            queryConfigChangesIcon()
        } else {
            showCustomAlert('失败', data.message);
        }
    })
    .catch(error => {
        console.error('Error in saving configuration:', error);
        showCustomAlert('错误', '保存模型配置时发生错误');
    });
}

function switchTab(tabId) {
    // Remove active class from all tabs and buttons
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(button => button.classList.remove('active'));

    // Add active class to the selected tab and button
    document.getElementById(tabId).classList.add('active');
    document.querySelector(`.tab-button[data-tab="${tabId}"]`).classList.add('active');
}

let accumulatedFilePaths = []; // Accumulate selected file paths
let selectedDocumentsContent = []; // Store the content of selected documents

function triggerFileInput() {
    document.getElementById('document-input').click();
}

function populateDocumentList(documentList) {
    const tableBody = document.querySelector('#selected-files tbody');
        tableBody.innerHTML = ''; // Clear existing rows
        if (documentList.length > 0) {
            documentList.forEach(doc => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${doc}</td>`;
                row.onclick = () => toggleRowSelection(row); // Add click event for selection
                tableBody.appendChild(row);

                // Add the document name to accumulatedFilePaths
                accumulatedFilePaths.push(doc);
            });
        } else {
            // Add a placeholder row if no documents exist
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'empty-row';
            emptyRow.innerHTML = `<td>暂无文档</td>`;
            tableBody.appendChild(emptyRow);
        }
}

function addDocuments() {
    const input = document.getElementById('document-input');
    const tableBody = document.querySelector('#selected-files tbody');
    const emptyRow = tableBody.querySelector('.empty-row');

    if (emptyRow) {
        emptyRow.remove(); // Remove placeholder row if it exists
    }

    Array.from(input.files).forEach(file => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${file.name}</td>`;
        row.onclick = () => toggleRowSelection(row); // Add click event for selection
        tableBody.appendChild(row);

        // Add the file path to accumulatedFilePaths
        accumulatedFilePaths.push(file.name);

        // Read the file content and store it for future use
        const reader = new FileReader();
        reader.onload = (event) => {
            const fileContent = event.target.result;
            selectedDocumentsContent.push({
                name: file.name,
                content: fileContent,
                type: file.type // 存储文件类型
            });
        };

        if (file.type === 'application/pdf'  || file.type === 'application/msword'
            || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            || file.type === 'text/csv'
            || file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            || file.type === 'application/vnd.ms-excel'
            || file.type === 'application/vnd.ms-powerpoint'
            || file.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
            reader.readAsArrayBuffer(file); // 以二进制方式读取 PDF 文件
        } else {
            reader.readAsText(file); // Read the file as text
        }

        enableSaveButton('knowledge-tab');

        // Set the flag to indicate that the document list has changed
        hasUnsavedDocumentListChanges = true;
    });

    input.value = ''; // Clear the input
}

function updateDeleteButtonState() {
    const deleteButton = document.getElementById('delete-document-button');
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    deleteButton.disabled = !selectedRow; // Disable if no row is selected
}

function deleteSelectedFile() {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow) {
        selectedRow.remove(); // Remove the selected row
        const fileName = selectedRow.querySelector('td').textContent;
        // Remove the file name from accumulatedFilePaths
        const index = accumulatedFilePaths.indexOf(fileName);
        if (index > -1) {
            accumulatedFilePaths.splice(index, 1);
        }
        updateDeleteButtonState(); // Update the delete button state

        enableSaveButton('knowledge-tab');

        // Set the flag to indicate that the document list has changed
        hasUnsavedDocumentListChanges = true;
    } else {
        showCustomAlert('提示', '请先选择一个文档');
    }
}

function clearSelectedFiles() {
    accumulatedFilePaths = []; // Clear the accumulated file paths
    selectedDocumentsContent = []; // Clear the stored document content
    const tableBody = document.querySelector('#selected-files tbody');
    tableBody.innerHTML = ''; // Clear the file list display

    // Add a placeholder row to indicate no files are selected
    const emptyRow = document.createElement('tr');
    emptyRow.className = 'empty-row';
    emptyRow.innerHTML = `<td>暂无文档</td>`;
    tableBody.appendChild(emptyRow);

    updateDeleteButtonState(); // Update the delete button state
}

function revertDocumentList() {
    populateDocumentList(originalDocumentList)
    accumulatedFilePaths = originalDocumentList.slice();
    hasUnsavedDocumentListChanges = false;
}

function saveKnowledgeBase() {
    try {
        const formData = new FormData();
        const input = document.getElementById('document-input');

        // Ensure at least one file is selected or accumulated
        if (input.files.length === 0 && accumulatedFilePaths.length === 0) {
            throw new Error('请至少选择一个文档或确保已添加文档路径。');
        }

        // Append file content to FormData
        let docCnt = 0;
        accumulatedFilePaths.forEach(filePath => {
            const matchingFile = selectedDocumentsContent.find(doc => doc.name === filePath);
            if (matchingFile) {
                let fileBlob;
                if (matchingFile.type === 'application/pdf') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/pdf' });
                } else if (matchingFile.type === 'application/msword') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/msword' });
                } else if (matchingFile.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
                } else if (matchingFile.type === 'text/csv') {
                    fileBlob = new Blob([matchingFile.content], { type: 'text/csv' });
                } else if (matchingFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                } else if (matchingFile.type === 'application/vnd.ms-excel') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/vnd.ms-excel' });
                } else if (matchingFile.type === 'application/vnd.ms-powerpoint') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/vnd.ms-powerpoint' });
                } else if (matchingFile.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
                    fileBlob = new Blob([matchingFile.content], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' });
                } else {
                    fileBlob = new Blob([matchingFile.content], { type: 'text/plain' });
                }
                formData.append('doc_blob_list', new File([fileBlob], filePath));
                docCnt = docCnt + 1;
            }
        });

        const systemPrompt = document.getElementById('system-prompt').value.trim();
        if (!systemPrompt) {
            throw new Error('系统提示词不能为空，请输入有效的系统提示词。');
        }
        formData.append('system_prompt', systemPrompt);

        // Append the new document list to the form data
        formData.append('document_list', accumulatedFilePaths.join(','));

        let path_sufix;
        let target_cn;
        let target_en;
        if(docCnt > 0) {
            path_sufix = 'upload-documents'
            target_cn = '文档和系统提示词'
            target_en = 'documents and system prompt'
        } else {
            path_sufix = 'documents'
            target_cn = '文档清单和系统提示词'
            target_en = 'documents list and system prompt'
        }
        fetch(`${BASE_URL}/api/${path_sufix}`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                selectedDocumentsContent = []
                showCustomAlert('成功', `${target_cn}已成功上传到服务器并保存。`);
                disableSaveButton('knowledge-tab'); // Disable save button after saving

                // Update original values after successful save
                originalSystemPrompt = systemPrompt;
                originalDocumentList = accumulatedFilePaths.slice();
                hasUnsavedKnowledgeChanges = false;
                hasUnsavedDocumentListChanges = false;

                queryConfigChangesIcon();
            } else {
                response.text().then(errorText => {
                    throw new Error(`Failed to upload ${target_en} to the server. ${errorText}`);
                });
            }
        })
        .catch(error => {
            if (error instanceof TypeError) {
                console.error('Network error:', error);
                showCustomAlert('错误', '网络错误，请检查您的网络连接。');
            } else {
                console.error('Error during document upload:', error);
                showCustomAlert('错误', `上传文档(清单)和系统提示词时出错: ${error.message}`);
            }
        });
    } catch (error) {
        console.error('Error in saving knowledge base:', error);
        showCustomAlert('异常', error.message);
    }
}

function toggleRowSelection(row) {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow && selectedRow !== row) {
        selectedRow.classList.remove('selected'); // Unselect previously selected row
    }
    row.classList.toggle('selected'); // Toggle selection for the clicked row

    updateDeleteButtonState(); // Update the delete button state
}

function updateProviderDescription() {
    const selectedProvider = document.getElementById('llm-provider').value;
    const description = provider_intro[selectedProvider];
    const descriptionBox = document.getElementById('provider-description-box');
    descriptionBox.value = description || '暂无相关介绍。';
}

function initializeKnowledgeTab() {
    fetch(`${BASE_URL}/api/documents`, { // Fetch documents and system prompt
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        // Populate the document list
        populateDocumentList(data.documents)

        // Populate the system prompt
        const systemPrompt = document.getElementById('system-prompt');
        systemPrompt.value = data.system_prompt || '';

        // Store the original document list
        originalDocumentList = data.documents;

        // Store original system prompt
        originalSystemPrompt = data.system_prompt || '';

        // Disable the save button after initialization
        const saveButton = document.getElementById('save-knowledge-button');
        saveButton.disabled = true;
        saveButton.style.backgroundColor = '#6c757d'; // Gray color for disabled state
        saveButton.style.cursor = 'not-allowed';
    })
    .catch(error => console.error('Error initializing knowledge tab:', error));

    disableSaveButton('knowledge-tab'); // Disable save button initially
}

// Utility function to update button state
function updateButtonState(button, isDisabled) {
    button.disabled = isDisabled;
    button.style.backgroundColor = isDisabled ? '#6c757d' : '#28a745'; // Gray for disabled, green for enabled
    button.style.cursor = isDisabled ? 'not-allowed' : 'pointer';
}

function enableSaveButton(tabId) {
    const saveButton = document.querySelector(`#${tabId} .save-button`);
    if (saveButton) {
        saveButton.disabled = false;
        saveButton.style.backgroundColor = '#28a745'; // Green color for enabled state
        saveButton.style.cursor = 'pointer';
    }
}

function disableSaveButton(tabId) {
    const saveButton = document.querySelector(`#${tabId} .save-button`);
    if (saveButton) {
        saveButton.disabled = true;
        saveButton.style.backgroundColor = '#6c757d'; // Gray color for disabled state
        saveButton.style.cursor = 'not-allowed';
    }
}

// Function to show awaiting status
function showAwaitingStatus() {
    const applyButton = document.getElementById('apply-config-button');
    applyButton.disabled = true;
    applyButton.textContent = '配置变更部署进行中...';

    const configModal = document.getElementById('config-modal');
    if (configModal) {
        const closeButton = configModal.getElementsByClassName('close')[0];
        if (closeButton) {
            closeButton.disabled = true;
            closeButton.style.color = '#6c757d'; // Set the text color to gray
            closeButton.style.cursor = 'not-allowed';
        }
    }
}

// Function to hide awaiting status
function hideAwaitingStatus() {
    const applyButton = document.getElementById('apply-config-button');
    applyButton.disabled = false;
    applyButton.textContent = '应用配置变更';

    const configModal = document.getElementById('config-modal');
    if (configModal) {
        const closeButton = configModal.getElementsByClassName('close')[0];
        if (closeButton) {
            closeButton.disabled = false;
            closeButton.style.color = '#aaa'; // Restore the original text color
            closeButton.style.cursor = 'pointer';
        }
    }
}

// Function to apply configuration changes
async function applyConfigChanges() {
    try {
        showAwaitingStatus();
        const response = await fetch(`${BASE_URL}/api/config-apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        if (!response.ok) {
            throw new Error(`Server error: ${await response.text()}`);
        }
        const data = await response.json();
        if (data.status_ok) {
            showCustomAlert('成功', '配置变更已成功应用。');

            // Reset the session ID
            sessionId = generateSessionId();
            sessionStorage.setItem('sessionId', sessionId);

            queryConfigChangesIcon();

            // Send the message when the config change deployment is completed
            appendMessage('assistant', 'Config change deployment completed. New chat starts...');
        } else {
            showCustomAlert('失败', '应用配置变更时出现错误。');
        }
    } catch (error) {
        console.error('Error in applying configuration changes:', error);
        showCustomAlert('错误', '应用配置变更时发生错误。');
    } finally {
        hideAwaitingStatus();
    }
}

function updateApplyConfigButtonState() {
    const icon = document.getElementById('config-changes-icon');
    const applyButton = document.getElementById('apply-config-button');
    if (icon.classList.contains('red')) {
        applyButton.disabled = false;
        applyButton.style.backgroundColor = ''; // Reset background color
        applyButton.style.cursor = 'pointer';
    } else {
        applyButton.disabled = true;
        applyButton.style.backgroundColor = '#6c757d'; // Gray color for disabled state
        applyButton.style.cursor = 'not-allowed';
    }
}
