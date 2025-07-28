import subprocess
import threading
import os
import signal
import sys
import time

# --- Configurações dos Serviços ---
# Altere aqui se os nomes das pastas ou comandos forem diferentes.

# Serviço de WhatsApp (Node.js)
WHATSAPP_SERVICE_DIR = r'C:\Users\Jhonattan.rocha\Documents\projetos\agenda-risetec-backend\whatsapp'
WHATSAPP_COMMAND = ['node', 'index.js']
WHATSAPP_LOG = r'whatsapp_service.log'

# Serviço da API Principal (FastAPI)
API_SERVICE_DIR = r'C:\Users\Jhonattan.rocha\Documents\projetos\agenda-risetec-backend'
# API_COMMAND = ['hypercorn', 'main:app', '--bind', '0.0.0.0:11100', '--certfile', '/etc/ssl/risetec/cloud.risetec.com.br.crt', '--keyfile', '/etc/ssl/risetec/cloud.risetec.com.br.key']
API_COMMAND = ['hypercorn', 'main:app', '--bind', '0.0.0.0:9000']
API_LOG = r'api_service.log'

# --- Gerenciador de Processos ---

# Dicionário para manter os processos filhos em execução
running_processes = {}

def start_service(command, directory, log_filename):
    """
    Inicia um serviço em um diretório específico e redireciona sua saída para um log.
    Retorna o objeto do processo criado.
    """
    # Garante que o processo filho também receba o sinal de encerramento
    preexec_fn = os.setsid if sys.platform != "win32" else None

    try:
        # Abre o arquivo de log para escrita
        log_file = open(log_filename, 'w')
        
        # Inicia o processo
        process = subprocess.Popen(
            command,
            cwd=directory,          # Define o diretório de trabalho
            stdout=log_file,        # Redireciona a saída padrão para o log
            stderr=subprocess.STDOUT, # Redireciona a saída de erro para o mesmo log
            preexec_fn=preexec_fn
        )
        
        # Armazena o processo no nosso dicionário global
        running_processes[process.pid] = process
        print(f"[{directory}] iniciado com sucesso. PID: {process.pid}. Logs em '{log_filename}'.")
        return process
        
    except FileNotFoundError:
        print(f"[ERRO] Comando '{' '.join(command)}' não encontrado. Verifique se o programa está instalado e no PATH.")
        return None
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o serviço em '{directory}': {e}")
        return None


def run_in_thread(target_func, *args):
    """Cria e inicia uma thread para executar uma função."""
    thread = threading.Thread(target=target_func, args=args)
    thread.daemon = True  # Permite que o programa principal saia mesmo que as threads estejam ativas
    thread.start()
    return thread


def signal_handler(sig, frame):
    """
    Lida com os sinais de interrupção (como Ctrl+C) para encerrar os processos filhos.
    """
    print("\nSinal de encerramento recebido. Parando todos os serviços...")
    
    for pid, process in running_processes.items():
        print(f"Enviando sinal de parada para o processo {pid}...")
        try:
            # Em sistemas não-Windows, matamos o grupo de processos para garantir
            # que todos os filhos do nosso processo também sejam encerrados.
            if sys.platform != "win32":
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            print(f"Processo {pid} já não existia.")
        except Exception as e:
            print(f"Erro ao tentar parar o processo {pid}: {e}")

    # Aguarda um pouco para os processos terminarem
    time.sleep(2)
    print("Todos os serviços foram parados. Encerrando.")
    sys.exit(0)


# --- Função Principal ---

def main():
    print("--- Iniciando o Gerenciador de Serviços ---")

    # Registra o handler para os sinais de encerramento
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler) # Comando 'kill'

    # Inicia cada serviço em sua própria thread
    run_in_thread(start_service, WHATSAPP_COMMAND, WHATSAPP_SERVICE_DIR, WHATSAPP_LOG)
    run_in_thread(start_service, API_COMMAND, API_SERVICE_DIR, API_LOG)

    print("\nAmbos os serviços estão iniciando em background.")
    print("Pressione Ctrl+C para parar todos os serviços de forma segura.")

    # Mantém o script principal em execução para monitorar
    try:
        while True:
            # O loop principal pode ser usado para verificar a saúde dos serviços, se desejado.
            time.sleep(10)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()