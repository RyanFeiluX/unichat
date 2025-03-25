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

