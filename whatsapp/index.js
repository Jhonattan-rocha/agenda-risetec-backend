const express = require('express');
// NOVO: Importa a função getState
const { client, initialize, getState } = require('./client');

const app = express();
const port = 3000;

app.use(express.json());

// ALTERADO: O endpoint de status agora retorna o estado detalhado
app.get('/status', (req, res) => {
    const currentState = getState();
    res.status(200).json(currentState);
});

// NOVO: Endpoint para forçar a reinicialização do cliente
app.post('/reconnect', (req, res) => {
    console.log('Recebida requisição para reconectar...');
    initialize(); // Chama a função de inicialização
    res.status(202).json({ success: true, message: 'Processo de reinicialização iniciado.' });
});

// Endpoint para enviar mensagens (sem alterações)
app.post('/send-message', async (req, res) => {
    const { number, message } = req.body;

    if (getState().status !== 'READY') {
        return res.status(409).json({ success: false, error: 'O cliente de WhatsApp não está pronto.' });
    }

    if (!number || !message) {
        return res.status(400).json({ success: false, error: 'Número e mensagem são obrigatórios.' });
    }

    try {
        const chatId = `${number.replace('+', '')}@c.us`;
        await client.sendMessage(chatId, message);
        res.status(200).json({ success: true, message: 'Mensagem enviada com sucesso!' });
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        res.status(500).json({ success: false, error: 'Falha ao enviar mensagem.' });
    }
});

app.post('/logout', async (req, res) => {
    try {
        await logout();
        res.status(200).json({ success: true, message: 'Cliente desconectado com sucesso.' });
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        res.status(500).json({ success: false, error: 'Falha ao desconectar.' });
    }
});

app.listen(port, () => {
    console.log(`Servidor da API de WhatsApp rodando em http://localhost:${port}`);
    initialize();
});