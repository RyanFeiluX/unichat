BASE_URL="http://localhost:8000"

function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;

    appendMessage('user', userInput);

    fetch(`${BASE_URL}/ask`, { // Use BASE_URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userInput }),
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
        appendMessage('assistant', data.answer);
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

function appendMessage(sender, message) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.className = sender;
    messageElement.innerText = message;
    chatBox.appendChild(messageElement);
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

function openConfigModal() {
    const configModal = document.getElementById('config-modal');
    configModal.style.display = 'block'; // Ensure the modal is displayed
}

function closeConfigModal() {
    const configModal = document.getElementById('config-modal');
    configModal.style.display = 'none'; // Ensure the modal is hidden
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
    });
    document.getElementById('llm-model').addEventListener('change', () => {
        enableSaveButton('model-tab'); // Enable save button when LLM model changes
    });
    document.getElementById('embedding-provider').addEventListener('change', () => {
        updateEmbeddingModels();
        enableSaveButton('model-tab'); // Enable save button when embedding provider changes
    });
    document.getElementById('embedding-model').addEventListener('change', () => {
        enableSaveButton('model-tab'); // Enable save button when embedding model changes
    });
    document.getElementById('save-model-button').addEventListener('click', saveModelConfig);

    // Attach event listeners for knowledge tab
    document.getElementById('add-document-button').addEventListener('click', triggerFileInput);
    document.getElementById('delete-document-button').addEventListener('click', deleteSelectedFile);
    document.getElementById('document-input').addEventListener('change', addDocuments);
    document.getElementById('system-prompt').addEventListener('input', () => enableSaveButton('knowledge-tab'));
    document.getElementById('save-knowledge-button').addEventListener('click', saveKnowledgeBase);

    // Initialize tabs
    initializeModelTab();
    initializeKnowledgeTab();
});

let llmModelsData = {};
let embeddingModelsData = {};

// function initializeConfig() {
//     fetch(`${BASE_URL}/api/models/fetch`, { // Separate endpoint for fetching configurations
//         method: 'GET'
//     })
//     .then(response => response.json())
//     .then(data => {
//         llmModelsData = data.model_support.reduce((acc, item) => {
//             acc[item.provider] = item.llm_model.map(model => ({ value: model, label: model }));
//             return acc;
//         }, {});
//         embeddingModelsData = data.model_support.reduce((acc, item) => {
//             acc[item.provider] = item.emb_model.map(model => ({ value: model, label: model }));
//             return acc;
//         }, {});
//         populateSelect('llm-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));
//         populateSelect('embedding-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));
//         loadLastSelectedConfig();
//     })
//     .catch(error => console.error('Error fetching config:', error));
// }

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
        updateLlmModels();

        // Populate embedding models based on the selected provider
        embeddingModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.emb_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
        updateEmbeddingModels();

        // Set selected values based on model_select
        document.getElementById('llm-provider').value = data.model_select.llm_provider || '';
        document.getElementById('llm-model').value = data.model_select.llm_model || '';
        document.getElementById('embedding-provider').value = data.model_select.emb_provider || '';
        document.getElementById('embedding-model').value = data.model_select.emb_model || '';

        // Update provider description
        // Organize provider descriptions
        provider_intro = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.prov_intro || '暂无相关介绍。'; // Default description if none provided
            return acc;
        }, {});
        updateProviderDescription();
    })
    .catch(error => console.error('Error fetching model configuration:', error));

    disableSaveButton('model-tab'); // Disable save button initially
}

// function loadLastSelectedConfig() {
//     const lastConfig = JSON.parse(localStorage.getItem('lastConfig')) || {};
//     const llmProvider = lastConfig.llmProvider || document.getElementById('llm-provider').options[0].value;
//     const embeddingProvider = lastConfig.embeddingProvider || document.getElementById('embedding-provider').options[0].value;

//     document.getElementById('llm-provider').value = llmProvider;
//     document.getElementById('embedding-provider').value = embeddingProvider;

//     updateLlmModels();
//     updateEmbeddingModels();

//     document.getElementById('llm-model').value = lastConfig.llmModel || document.getElementById('llm-model').options[0].value;
//     document.getElementById('embedding-model').value = lastConfig.embeddingModel || document.getElementById('embedding-model').options[0].value;
// }

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
        alert('请确保所有配置项均已选择有效值。');
        return;
    }

    const model_config = {
        llm_provider: llmProvider,
        llm_model: llmModel,
        emb_provider: embProvider,
        emb_model: embModel,
    };

    fetch(`${BASE_URL}/api/models`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(model_config)
    })
    .then(response => {
        if (response.ok) {
            alert('结果: 模型配置已保存');
            disableSaveButton('model-tab'); // Disable save button after saving
        } else {
            alert('结果: 保存模型配置时出错');
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        alert('保存模型配置时发生错误');
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
        updateDeleteButtonState(); // Update the delete button state
    } else {
        alert('请先选择一个文档');
    }
    enableSaveButton('knowledge-tab');
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
                formData.append('documents', new File([fileBlob], filePath));
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
                alert(`${target_cn}已成功上传到服务器并保存。`);
                disableSaveButton('knowledge-tab'); // Disable save button after saving
            } else {
                response.text().then(errorText => {
                    throw new Error(`Failed to upload ${target_en} to the server. ${errorText}`);
                });
            }
        })
        .catch(error => {
            console.error('Error during document upload:', error);
            alert(`上传文档(清单)和系统提示词时出错: ${error.message}`);
        });
    } catch (error) {
        console.error('Error:', error);
        alert(error.message);
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
        const tableBody = document.querySelector('#selected-files tbody');
        tableBody.innerHTML = ''; // Clear existing rows
        if (data.documents.length > 0) {
            data.documents.forEach(doc => {
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

        // Populate the system prompt
        const systemPrompt = document.getElementById('system-prompt');
        systemPrompt.value = data.system_prompt || '';

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

// Attach the saveKnowledgeBase function to the save button
// document.getElementById('save-knowledge-button').addEventListener('click', saveKnowledgeBase);
