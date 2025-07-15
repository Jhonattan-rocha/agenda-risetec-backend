# radicale_config/config.py

# -- Server Configuration --
[server]
hosts = 0.0.0.0:5232

# -- Storage Configuration --
[storage]
# Usaremos um backend de armazenamento customizado
type = radicale_storage.storage

# -- Authentication Configuration --
[auth]
# Usaremos um backend de autenticação customizado
type = radicale_storage.auth
# O realm é o nome que aparece na janela de login
realm = RiseTec Agenda

# -- Logging Configuration --
[logging]
# Isso ajuda a ver o que o Radicale está fazendo durante o desenvolvimento
level = DEBUG