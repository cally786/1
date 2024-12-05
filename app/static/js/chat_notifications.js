// Función para actualizar el contador de chats pendientes (para admins)
async function updatePendingChatsCount() {
    try {
        const response = await fetch('/chat/pending/count');
        const data = await response.json();
        const badge = document.getElementById('pendingChatsCount');
        
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Error al actualizar contador de chats:', error);
    }
}

// Función para actualizar el contador de mensajes no leídos (para usuarios)
async function updateUnreadChatsCount() {
    try {
        const response = await fetch('/chat/unread/count');
        const data = await response.json();
        const badge = document.getElementById('unreadChatsCount');
        
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Error al actualizar contador de mensajes:', error);
    }
}

// Actualizar contadores cada 30 segundos
if (document.getElementById('pendingChatsCount')) {
    updatePendingChatsCount();
    setInterval(updatePendingChatsCount, 30000);
}

if (document.getElementById('unreadChatsCount')) {
    updateUnreadChatsCount();
    setInterval(updateUnreadChatsCount, 30000);
}
