const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// Usamos LocalAuth para salvar a sessão e evitar escanear o QR Code a cada reinicialização
const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', (qr) => {
    console.log('QR Code recebido, escaneie por favor:');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log('Autenticado com sucesso!');
});

client.on('auth_failure', msg => {
    console.error('Falha na autenticação!', msg);
});

client.on('ready', () => {
    console.log('Cliente do WhatsApp está pronto e conectado!');
});

function initialize() {
    client.initialize();
}

module.exports = {
    client,
    initialize
};