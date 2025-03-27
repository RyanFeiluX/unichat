function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    if (userInput.trim() === "") return;

    appendMessage('user', userInput);

    fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        appendMessage('assistant', data.answer);
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage('assistant', '抱歉，处理您的请求时出现错误。');
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
    var keycode = event.keyCode||e.which||e.charCode;

    if (keycode == 13 ) //Enter=13
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
    document.getElementById('config-modal').style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('config-modal').style.display = 'none';
}

let llmModelsData = {};
let embeddingModelsData = {};

function initializeConfig() {
    fetch('http://localhost:8000/api/config', // Corrected fetch URL
        {
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
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option.value;
        opt.textContent = option.label;
        select.appendChild(opt);
    });
}

function saveConfig() {
    const config = {
        llm_provider: document.getElementById('llm-provider').value,
        llm_model: document.getElementById('llm-model').value,
        emb_provider: document.getElementById('embedding-provider').value,
        emb_model: document.getElementById('embedding-model').value
    };

    fetch('http://localhost:8000/api/config', { // Corrected fetch URL
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => {
        if (response.ok) {
            alert('结果: 配置已保存');
            localStorage.setItem('lastConfig', JSON.stringify(config));
            closeConfigModal();
        } else {
            alert('结果: 保存配置时出错');
        }
    })
    .catch(error => console.error('Error saving config:', error));
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
    });

    input.value = ''; // Clear the input
}

function toggleRowSelection(row) {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow && selectedRow !== row) {
        selectedRow.classList.remove('selected'); // Unselect previously selected row
    }
    row.classList.toggle('selected'); // Toggle selection for the clicked row

    updateDeleteButtonState(); // Update the delete button state
}

function updateDeleteButtonState() {
    const deleteButton = document.getElementById('delete-document-button');
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    deleteButton.disabled = !selectedRow; // Disable if no row is selected
}

function deleteSelectedRow() {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow) {
        selectedRow.remove(); // Remove the selected row
        alert('选中的文档已删除');
        updateDeleteButtonState(); // Update the delete button state
    } else {
        alert('请先选择一个文档');
    }
}

function clearSelectedFiles() {
    accumulatedFilePaths = []; // Clear the accumulated file paths
    const fileList = document.getElementById('selected-files');
    fileList.innerHTML = ''; // Clear the file list display
}

function saveSelectedFiles() {
    fetch('http://localhost:8000/api/save-selected-files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_paths: accumulatedFilePaths })
    })
    .then(response => {
        if (response.ok) {
            alert('选中文档路径已保存');
        } else {
            alert('保存选中文档路径时出错');
        }
    })
    .catch(error => console.error('Error saving selected file paths:', error));
}

function toggleEditMode() {
    const systemPrompt = document.getElementById('system-prompt');
    if (systemPrompt.readOnly) {
        systemPrompt.readOnly = false;
        systemPrompt.focus();
    } else {
        systemPrompt.readOnly = true;
        saveSystemPrompt(systemPrompt.value);
    }
}

function saveSystemPrompt(promptText) {
    fetch('http://localhost:8000/api/save-knowledge', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ system_prompt: promptText })
    })
    .then(response => {
        if (response.ok) {
            alert('系统提示词已保存');
        } else {
            alert('保存系统提示词时出错');
        }
    })
    .catch(error => console.error('Error saving system prompt:', error));
}

function saveKnowledge() {
    const knowledgeText = document.getElementById('knowledge-text').value;
    const systemPrompt = document.getElementById('system-prompt').value;

    fetch('http://localhost:8000/api/save-knowledge', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ knowledge: knowledgeText, system_prompt: systemPrompt })
    })
    .then(response => {
        if (response.ok) {
            alert('知识库保存成功');
        } else {
            alert('知识库保存失败');
        }
    })
    .catch(error => console.error('Error saving knowledge:', error));
}

document.addEventListener('DOMContentLoaded', () => {
    initializeConfig(); // Ensure configuration is initialized on page load
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll chat box to the bottom
});

function deleteSelectedFile() {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow) {
        selectedRow.remove(); // Remove the selected row
        updateDeleteButtonState(); // Update the delete button state
    } else {
        alert('请先选择一个文档');
    }
}

function saveKnowledgeBase() {
    const fileList = Array.from(document.querySelectorAll('#selected-files tbody tr td:first-child')).map(td => td.textContent);
    const systemPrompt = document.getElementById('system-prompt').value;
    console.log('Saving knowledge base:', { fileList, systemPrompt });
    alert('知识库已保存');
    // Add logic to save the data (e.g., send to server)
}

function triggerFileInput() {
    const input = document.getElementById('document-input');
    input.click(); // Trigger the file input dialog
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
    });

    input.value = ''; // Clear the input
}

function toggleRowSelection(row) {
    const selectedRow = document.querySelector('#selected-files tbody tr.selected');
    if (selectedRow && selectedRow !== row) {
        selectedRow.classList.remove('selected'); // Unselect previously selected row
    }
    row.classList.toggle('selected'); // Toggle selection for the clicked row

    updateDeleteButtonState(); // Update the delete button state
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
        // alert('选中的文档已删除');
        updateDeleteButtonState(); // Update the delete button state
    } else {
        alert('请先选择一个文档');
    }
}

function saveKnowledgeBase() {
    const fileList = Array.from(document.querySelectorAll('#selected-files tbody tr td:first-child')).map(td => td.textContent);
    const systemPrompt = document.getElementById('system-prompt').value;
    console.log('Saving knowledge base:', { fileList, systemPrompt });
    // Add logic to save the data (e.g., send to server)
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

function modifyFile(button) {
    alert('修改功能尚未实现'); // Placeholder for modify functionality
}

function deleteSelectedFiles() {
    const tableBody = document.querySelector('#selected-files tbody');
    tableBody.innerHTML = ''; // Clear all rows in the table
    alert('所有文档已删除');
}

