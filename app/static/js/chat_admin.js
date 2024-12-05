// Función para cerrar un chat
async function closeChat(chatId) {
    try {
        const response = await fetch(`/chat/${chatId}/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Actualizar la UI para reflejar que el chat está cerrado
            const chatElement = document.querySelector(`#chat-${chatId}`);
            if (chatElement) {
                chatElement.classList.add('chat-closed');
                const closeButton = chatElement.querySelector('.close-chat-btn');
                if (closeButton) {
                    closeButton.disabled = true;
                }
            }
            
            // Mostrar mensaje de éxito
            alert('Chat cerrado exitosamente');
            
            // Actualizar contadores
            if (typeof updatePendingChatsCount === 'function') {
                updatePendingChatsCount();
            }
        } else {
            throw new Error(data.message || 'Error al cerrar el chat');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'Error al cerrar el chat');
    }
}

// Agregar event listeners a los botones de cerrar chat
document.addEventListener('DOMContentLoaded', function() {
    const closeButtons = document.querySelectorAll('.close-chat-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            if (confirm('¿Estás seguro de que deseas cerrar este chat?')) {
                closeChat(chatId);
            }
        });
    });
});
