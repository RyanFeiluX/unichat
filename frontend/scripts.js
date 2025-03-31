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
    document.getElementById('config-button').addEventListener('click', openConfigModal);
    document.querySelector('.close').addEventListener('click', closeConfigModal);
});

let llmModelsData = {};
let embeddingModelsData = {};

function initializeConfig() {
    fetch(`${BASE_URL}/api/models/fetch`, { // Separate endpoint for fetching configurations
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        llmModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.llm_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
        embeddingModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.emb_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
        populateSelect('llm-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));
        populateSelect('embedding-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));
        loadLastSelectedConfig();
    })
    .catch(error => console.error('Error fetching config:', error));
}

function loadLastSelectedConfig() {
    const lastConfig = JSON.parse(localStorage.getItem('lastConfig')) || {};
    const llmProvider = lastConfig.llmProvider || document.getElementById('llm-provider').options[0].value;
    const embeddingProvider = lastConfig.embeddingProvider || document.getElementById('embedding-provider').options[0].value;

    document.getElementById('llm-provider').value = llmProvider;
    document.getElementById('embedding-provider').value = embeddingProvider;

    updateLlmModels();
    updateEmbeddingModels();

    document.getElementById('llm-model').value = lastConfig.llmModel || document.getElementById('llm-model').options[0].value;
    document.getElementById('embedding-model').value = lastConfig.embeddingModel || document.getElementById('embedding-model').options[0].value;
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
    const messages = {
        en: 'Please ensure all configuration items have valid values.',
        zh: '请确保所有配置项均已选择有效值。'
    };

    const userLanguage = navigator.language.startsWith('zh') ? 'zh' : 'en'; // Detect user's language
    const validationMessage = messages[userLanguage];

    if (!llmProvider || !llmModel || !embProvider || !embModel) {
        alert(validationMessage);
        return;
    }

    const llmProvider = document.getElementById('llm-provider').value;
    const llmModel = document.getElementById('llm-model').value;
    const embProvider = document.getElementById('embedding-provider').value;
    const embModel = document.getElementById('embedding-model').value;

    // Validate configuration values
    if (!llmProvider || !llmModel || !embProvider || !embModel) {
        alert('请确保所有配置项均已选择有效值。');
        return;
    }
    fetch(`${BASE_URL}/api/models/save`, { // Separate endpoint for saving configurations
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })

    fetch(`${BASE_URL}/api/models`, { // Use BASE_URL
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(() => {
        updateButtonState(saveButton, true);
        Toastify({
            text: "Configuration saved successfully!",
            duration: 3000,
            gravity: "top",
            position: "center",
            backgroundColor: "#28a745", // Green for success
            stopOnFocus: true
        }).showToast();
        setTimeout(() => {
            const saveButton = document.querySelector('#model-tab .save-button');
            saveButton.disabled = true; // Disable the save button
            saveButton.style.backgroundColor = '#6c757d'; // Gray color for disabled state
            saveButton.style.cursor = 'not-allowed';
        }, 0); // Update button state after pop-up
    })
    .catch(error => {
        console.error('Error saving configuration:', error);

        // Show an error toast notification
        Toastify({
            text: "Error saving configuration.",
            duration: 3000,
            gravity: "top",
            position: "center",
            backgroundColor: "#dc3545", // Red for error
            stopOnFocus: true
        }).showToast();
        
    })
    .catch(error => {
        console.error('Error saving config:', error);
        alert('保存配置时发生错误');
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
            selectedDocumentsContent.push({
                name: file.name,
                content: event.target.result
            });
        };
        reader.readAsText(file); // Read the file as text
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
        const formData = new FormData(); // Create a new FormData object
        const input = document.getElementById('document-input');

        // Ensure at least one file is selected or accumulated
        if (input.files.length === 0 && accumulatedFilePaths.length === 0) {
            throw new Error('请至少选择一个文档或确保已添加文档路径。');
        }

        // Append files from the file input to FormData
        Array.from(input.files).forEach(file => {
            formData.append('documents', file); // Append each file object to the 'documents' field
        });

        // Append accumulated file paths to FormData
        accumulatedFilePaths.forEach(filePath => {
            const matchingFile = selectedDocumentsContent.find(doc => doc.name === filePath);
            if (matchingFile) {
                const fileContent = new Blob([matchingFile.content], { type: 'text/plain' }); // Create a Blob for the file content
                formData.append('documents', new File([fileContent], filePath)); // Add file content as a File object
            }
        });

        // Append system prompt to FormData
        const systemPrompt = document.getElementById('system-prompt').value.trim();
        if (!systemPrompt) {
            throw new Error('系统提示词不能为空，请输入有效的系统提示词。');
        }
        formData.append('system_prompt', systemPrompt); // Append the system prompt to the 'system_prompt' field

        // Append provider description to FormData
        const providerDescription = document.getElementById('provider-description-box').value.trim();
        if (!providerDescription) {
            throw new Error('提供者描述不能为空，请确保已选择有效的提供者。');
        }
        formData.append('provider_description', providerDescription); // Append the provider description

        // Send the FormData object as the request body
        fetch(`${BASE_URL}/api/upload-documents`, {
            method: 'POST',
            body: formData // Automatically sets the correct Content-Type header
        })
        .then(() => {
            updateButtonState(saveButton, true);
            selectedDocumentsContent = [];
            const saveButton = document.getElementById('save-knowledge-button');
            saveButton.disabled = true;
            saveButton.style.backgroundColor = '#6c757d'; // Gray color for disabled state
            saveButton.style.cursor = 'not-allowed';
        })
        .catch(() => {
            response.text().then(errorText => {
                throw new Error(`Failed to upload documents, system prompt, and provider description to the server. ${errorText}`);
            });
        // });
        })
        .catch(error => {
            console.error('Error during document upload:', error);
            alert(`上传文档、系统提示词和提供者描述时出错: ${error.message}`);
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
    const descriptions = {
        'ProviderA': 'ProviderA 提供高性能的语言模型，适用于多种场景。',
        'ProviderB': 'ProviderB 专注于低延迟和高效率的模型服务。',
        'ProviderC': 'ProviderC 提供丰富的模型选择，支持多语言处理。'
    };
    const descriptionBox = document.getElementById('provider-description-box');
    descriptionBox.value = descriptions[selectedProvider] || '暂无相关介绍。';
}

function initializeModelTab() {
    fetch(`${BASE_URL}/api/models`, { // Fetch model configuration options
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        llmModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.llm_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});
        embeddingModelsData = data.model_support.reduce((acc, item) => {
            acc[item.provider] = item.emb_model.map(model => ({ value: model, label: model }));
            return acc;
        }, {});

        // Populate LLM provider dropdown
        populateSelect('llm-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));

        // Populate embedding provider dropdown
        populateSelect('embedding-provider', data.model_support.map(item => ({ value: item.provider, label: item.provider })));

        // Trigger updates for models and descriptions
        updateLlmModels();
        updateEmbeddingModels();
        updateProviderDescription();
    })
    .catch(error => console.error('Error fetching model configuration:', error));
}

// Utility function to update button state
function updateButtonState(button, isDisabled) {
    button.disabled = isDisabled;
    button.style.backgroundColor = isDisabled ? '#6c757d' : '#28a745'; // Gray for disabled, green for enabled
    button.style.cursor = isDisabled ? 'not-allowed' : 'pointer';
}

// Attach the saveKnowledgeBase function to the save button
document.getElementById('save-knowledge-button').addEventListener('click', saveKnowledgeBase);
//     .catch(error => console.error('Error fetching config:', error));
// }
function disableSaveButton() {
// Attach the saveKnowledgeBase function to the save button
    updateButtonState(button, true);
    // Disable "保存" buttons initially
    document.querySelectorAll('.save-button').forEach(button => {
        button.disabled = true;
        button.style.backgroundColor = '#6c757d'; // Gray color for disabled state
        button.style.cursor = 'not-allowed';
    });
        updateButtonState(saveButton, false);
    const saveButton = document.querySelector(`#${tabId} .save-button`);
    if (saveButton) {
        saveButton.disabled = false;
        saveButton.style.backgroundColor = '#28a745'; // Green color for enabled state
        saveButton.style.cursor = 'pointer';

        // Attach the appropriate save function to the button
        if (tabId === 'model-tab') {
            saveButton.onclick = saveModelConfig; // Attach saveModelConfig for the "模型" tab
        } else if (tabId === 'knowledge-tab') {
            saveButton.onclick = saveKnowledgeBase; // Attach saveKnowledgeBase for the "知识库" tab
        }
    }
}

// Attach event listeners to detect changes in the "模型" tab
function attachModelTabListeners() {
    document.getElementById('llm-provider').addEventListener('change', () => enableSaveButton('model-tab'));
    document.getElementById('llm-model').addEventListener('change', () => enableSaveButton('model-tab'));
    document.getElementById('embedding-provider').addEventListener('change', () => enableSaveButton('model-tab'));
    document.getElementById('embedding-model').addEventListener('change', () => enableSaveButton('model-tab'));
}

// Attach event listeners to detect changes in the "知识库" tab
function attachKnowledgeTabListeners() {
    document.getElementById('system-prompt').addEventListener('input', () => enableSaveButton('knowledge-tab'));
    document.getElementById('document-input').addEventListener('change', () => enableSaveButton('knowledge-tab'));
    document.getElementById('add-document-button').addEventListener('click', () => enableSaveButton('knowledge-tab'));
    document.getElementById('delete-document-button').addEventListener('click', () => enableSaveButton('knowledge-tab'));
}

// Initialize save button state and attach listeners on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSaveButtonState();
    attachModelTabListeners();
    attachKnowledgeTabListeners();
});

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
}

// Call initializeKnowledgeTab on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeKnowledgeTab();
});

// Ensure the model tab is initialized on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeModelTab();
});

// Update references to saveConfig
document.querySelector('#model-tab .save-button').addEventListener('click', saveModelConfig);
document.querySelector('#knowledge-tab .save-button').addEventListener('click', saveKnowledgeBase);
