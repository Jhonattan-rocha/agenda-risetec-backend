const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// NOVO: Objeto para armazenar o estado atual do cliente
const clientState = {
    status: 'INITIALIZING', // INITIALIZING, SCAN_QR, READY, DISCONNECTED
    qrCode: null,
    message: 'O cliente está iniciando...'
};

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'], // Necessário para rodar em alguns ambientes de servidor/docker
    }
});

client.on('qr', (qr) => {
    console.log('QR Code recebido, escaneie por favor:');
    qrcode.generate(qr, { small: true });

    // NOVO: Atualiza o estado para fornecer o QR Code pela API
    clientState.status = 'SCAN_QR';
    clientState.qrCode = qr;
    clientState.message = 'QR Code recebido. Por favor, escaneie.';
    console.log(qr);
});

client.on('authenticated', () => {
    console.log('Autenticado com sucesso!');
    // A autenticação ocorreu, mas ainda precisa estar pronto para operar
    clientState.message = 'Autenticado com sucesso. Sincronizando mensagens...';
});

client.on('auth_failure', msg => {
    console.error('Falha na autenticação!', msg);
    clientState.status = 'DISCONNECTED';
    clientState.message = 'Falha na autenticação.';
});

client.on('ready', () => {
    console.log('Cliente do WhatsApp está pronto e conectado!');
    // NOVO: Atualiza o estado para "Pronto"
    clientState.status = 'READY';
    clientState.qrCode = null; // Limpa o QR Code pois não é mais necessário
    clientState.message = 'Cliente conectado e pronto para uso.';
});

client.on('disconnected', (reason) => {
    console.log('Cliente foi desconectado.', reason);
    // NOVO: Atualiza o estado para "Desconectado"
    clientState.status = 'DISCONNECTED';
    clientState.message = 'Cliente desconectado.';
});


function initialize() {
    console.log('Iniciando o cliente do WhatsApp...');
    clientState.status = 'INITIALIZING';
    clientState.message = 'O cliente está iniciando...';
    client.initialize();
}

// NOVO: Função para obter o estado atual
function getState() {
    return clientState;
}

async function logout() {
    console.log('Recebido comando de logout...');
    await client.logout();
}

module.exports = {
    client,
    initialize,
    getState,
    logout // Exporta a nova função
};