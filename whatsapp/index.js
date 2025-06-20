const express = require('express');
const { client, initialize } = require('./client');

const app = express();
const port = 3000;

// Middleware para parsear o corpo das requisições como JSON
app.use(express.json());

// Endpoint de verificação de status
app.get('/status', (req, res) => {
    res.status(200).json({ status: 'Serviço de WhatsApp está online e pronto.' });
});

// Endpoint para enviar mensagens
app.post('/send-message', async (req, res) => {
    const { number, message } = req.body; // Pega número e mensagem do corpo da requisição

    if (!number || !message) {
        return res.status(400).json({ success: false, error: 'Número e mensagem são obrigatórios.' });
    }

    try {
        // Formata o número para o padrão do WhatsApp (ex: 5511999998888@c.us)
        const chatId = `${number.replace('+', '')}@c.us`;

        console.log(`Enviando mensagem para: ${chatId}`);
        await client.sendMessage(chatId, message);
        
        res.status(200).json({ success: true, message: 'Mensagem enviada com sucesso!' });
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        res.status(500).json({ success: false, error: 'Falha ao enviar mensagem.' });
    }
});

// Inicia o servidor Express
app.listen(port, () => {
    console.log(`Servidor da API de WhatsApp rodando em http://localhost:${port}`);
    initialize();
});