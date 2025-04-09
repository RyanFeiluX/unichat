function showCustomAlert(title, message, callback = null) {
    // 创建模态框元素
    const modal = document.createElement('div');
    modal.classList.add('custom-alert-modal');

    // 创建模态框内容元素
    const modalContent = document.createElement('div');
    modalContent.classList.add('custom-alert-modal-content');

    // 创建标题元素
    const modalTitle = document.createElement('h2');
    modalTitle.textContent = title;

    // 创建消息元素
    const modalMessage = document.createElement('p');
    modalMessage.textContent = message;

    // 创建按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('button-container');

    // 创建关闭按钮元素
    const closeButton = document.createElement('button');
    closeButton.textContent = '继续';
    closeButton.classList.add('custom-alert-close-button'); // Add class
    closeButton.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    buttonContainer.appendChild(closeButton);

    if (callback) {
        const confirmButton = document.createElement('button');
        confirmButton.textContent = '放弃';
        confirmButton.classList.add('custom-alert-confirm-button'); // Add class
        confirmButton.addEventListener('click', () => {
            document.body.removeChild(modal);
            callback();
        });
        buttonContainer.appendChild(confirmButton);
    }

    // 将元素添加到模态框内容中
    modalContent.appendChild(modalTitle);
    modalContent.appendChild(modalMessage);
    modalContent.appendChild(buttonContainer);

    // 将模态框内容添加到模态框中
    modal.appendChild(modalContent);

    // 将模态框添加到页面中
    document.body.appendChild(modal);
}
