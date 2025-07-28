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

// --- SISTEMA DE FILA ---
const messageQueue = [];
let isProcessing = false;

// Função que processa a fila
const processQueue = async () => {
    if (messageQueue.length === 0) {
        isProcessing = false;
        return; // Fila vazia, para o processamento
    }

    isProcessing = true;
    const { phone_number, message } = messageQueue.shift(); // Pega o primeiro da fila

    if (getState().status === 'READY') {
        try {
            console.log(`Enviando mensagem para ${phone_number}...`);
            await client.sendMessage(`${phone_number}@c.us`, message);
            console.log(`Mensagem para ${phone_number} enviada com sucesso.`);
        } catch (err) {
            console.error(`Falha ao enviar para ${phone_number}:`, err);
        }
    } else {
        console.warn(`Cliente não está pronto. Mensagem para ${phone_number} não enviada.`);
    }

    // Intervalo convincente e aleatório entre as mensagens (ex: entre 5 e 12 segundos)
    const delay = Math.floor(Math.random() * (12000 - 5000 + 1) + 5000);
    console.log(`Aguardando ${delay / 1000}s para a próxima mensagem.`);
    setTimeout(processQueue, delay);
};

// Modifica o endpoint para adicionar à fila em vez de enviar diretamente
app.post('/send-message', (req, res) => {
    const { phone_number, message } = req.body;
    console.log(phone_number, message)
    if (!phone_number || !message) {
        return res.status(400).send({ status: 'error', message: 'phone_number e message são obrigatórios' });
    }
    
    // Adiciona a mensagem na fila
    messageQueue.push({ phone_number: phone_number, message });
    console.log(`Mensagem para ${phone_number} adicionada à fila. Tamanho da fila: ${messageQueue.length}`);
    
    // Se a fila não estiver sendo processada, inicia o processo
    if (!isProcessing) {
        processQueue();
    }
    
    // Retorna 202 Accepted para indicar que a mensagem foi aceita para processamento
    res.status(202).send({ status: 'queued' });
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