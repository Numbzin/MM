# 🎵 Migrador Bidirecional de Playlists

Migre suas playlists entre **Spotify** e **YouTube Music** de forma fácil e rápida!

## ✨ Funcionalidades

- ✅ **Spotify → YouTube Music**: Migre suas playlists do Spotify para o YT Music
- ✅ **YouTube Music → Spotify**: Migre suas playlists do YT Music para o Spotify
- 🧹 **Limpeza inteligente**: Remove músicas incorretas com proteção de músicas manuais
- 🎯 **Matching avançado**: Algoritmo inteligente que encontra as músicas certas
- 📊 **Interface visual**: Terminal colorido com progresso em tempo real
- 🛡️ **Proteção por data**: Preserve músicas adicionadas manualmente

---

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conta no Spotify
- Conta no YouTube Music

---

## 🚀 Instalação

### 1. Clone ou baixe o projeto

```bash
git clone https://github.com/Numbzin/MM.git
cd MM
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o Spotify

#### a) Crie um App no Spotify Developer Dashboard

1. Acesse: https://developer.spotify.com/dashboard
2. Faça login com sua conta Spotify
3. Clique em **"Create app"**
4. Preencha:
   - **App name**: "Migrador de Playlists" (ou qualquer nome)
   - **App description**: "Ferramenta para migrar playlists"
   - **Redirect URI**: `http://localhost:8888/callback`
5. Marque as caixas de termos e clique em **"Save"**
6. Na página do app, clique em **"Settings"**
7. Copie o **Client ID** e **Client Secret**

#### b) Configure o arquivo .env

1. Copie o arquivo de exemplo:

   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas credenciais:
   ```bash
   SPOTIFY_CLIENT_ID=seu_client_id_aqui
   SPOTIFY_CLIENT_SECRET=seu_client_secret_aqui
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

### 4. Configure o YouTube Music

Você tem **duas opções** para autenticar no YouTube Music:

#### **Opção 1: headers_auth.json (Recomendado - Mais Simples)**

1. Abra o YouTube Music no navegador e faça login
2. Abra as **Ferramentas do Desenvolvedor** (F12)
3. Vá para a aba **Network** (Rede)
4. Clique em qualquer música para começar a tocar
5. Na lista de requisições, procure por `browse` ou `next`
6. Clique com botão direito → **Copy** → **Copy as cURL**
7. Crie o arquivo `headers_auth.json` usando o ytmusicapi:

```bash
# Instale o ytmusicapi se ainda não tiver
pip install ytmusicapi

# Execute o comando para criar headers_auth.json
ytmusicapi browser
```

8. Quando solicitado, cole o comando cURL que você copiou
9. O arquivo `headers_auth.json` será criado automaticamente

#### **Opção 2: oauth.json (Alternativa)**

```bash
ytmusicapi oauth
```

Siga as instruções que aparecerem no terminal.

---

## 📖 Como Usar

### Executar o script

```bash
python migrador.py
```

### Menu Principal

```
🎵 MIGRADOR BIDIRECIONAL DE PLAYLISTS 🎵
Spotify ↔ YouTube Music

Escolha a operação:

  1 - Migrar: Spotify → YouTube Music
  2 - Migrar: YouTube Music → Spotify
  3 - Limpar: Remover incorretas do YouTube Music
  4 - Limpar: Remover incorretas do Spotify
  5 - Sair
```

---

## 🎯 Exemplos de Uso

### 1. Migrar do Spotify para YouTube Music

1. Escolha a opção **1**
2. Cole a URL da playlist do Spotify:
   ```
   https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
   ```
3. Digite o nome da playlist no YT Music (ou deixe em branco para usar o padrão)
4. Aguarde a migração!

### 2. Migrar do YouTube Music para Spotify

1. Escolha a opção **2**
2. Cole a URL da playlist do YouTube Music:
   ```
   https://music.youtube.com/playlist?list=PLxxxxxxxxxxxxxx
   ```
3. Digite o nome da playlist no Spotify
4. Aguarde a migração!

### 3. Limpar Playlist do YouTube Music

Remove músicas que não existem na playlist de referência do Spotify.

1. Escolha a opção **3**
2. Cole a URL da playlist do **Spotify** (referência)
3. Cole a URL da playlist do **YouTube Music** (será limpa)
4. Escolha se deseja proteger músicas adicionadas manualmente:
   - Se **sim**, informe a data da primeira migração (DD/MM/AAAA)
   - Músicas adicionadas **antes** dessa data serão protegidas
5. Confirme a remoção

### 4. Limpar Playlist do Spotify

Remove músicas que não existem na playlist de referência do YouTube Music.

1. Escolha a opção **4**
2. Cole a URL da playlist do **YouTube Music** (referência)
3. Cole a URL da playlist do **Spotify** (será limpa)
4. Configure a proteção por data (opcional)
5. Confirme a remoção

---

## 🛡️ Sistema de Proteção

O sistema de limpeza inclui proteção para músicas adicionadas manualmente:

**Exemplo:**

- Você migrou pela primeira vez em **10/11/2025**
- Tinha adicionado 50 músicas manualmente em **05/11/2025**
- Após a migração, 10 músicas incorretas foram adicionadas

**Resultado da limpeza:**

- ✅ As 50 músicas manuais (05/11) = **PROTEGIDAS**
- ❌ As 10 incorretas (10/11+) = **REMOVIDAS**

---

## 📊 Estatísticas

Ao final de cada operação, você verá um resumo completo:

```
╔════════════════════════════════════════════════════════════════════════════╗
║                           📊 ESTATÍSTICAS FINAIS                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  ✓ Músicas adicionadas:                                                 45 ║
║  ⊙ Músicas já existentes:                                                5 ║
║  ✗ Não encontradas:                                                      0 ║
║  📊 Total processado:                                                50/50 ║
║  📈 Taxa de sucesso:                                                 100.0% ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 🔧 Solução de Problemas

### Erro: "Credenciais do Spotify não configuradas"

Certifique-se de que:

1. O arquivo `.env` existe na mesma pasta do script
2. As credenciais estão corretas (sem espaços extras)
3. O arquivo não se chama `.env.example` (remova o `.example`)

### Erro: "Nenhum arquivo de autenticação encontrado" (YouTube Music)

Você precisa criar o arquivo `headers_auth.json` ou `oauth.json`. Veja a seção de configuração do YouTube Music.

### Músicas não encontradas

Algumas músicas podem não ser encontradas por:

- Nome muito diferente entre as plataformas
- Música não disponível na plataforma de destino
- Artistas escritos de forma diferente

O script salva automaticamente uma lista das músicas não encontradas em:

- `nao_encontradas_spotify_para_ytmusic_[timestamp].txt`
- `nao_encontradas_ytmusic_para_spotify_[timestamp].txt`

### Rate Limiting

Se receber muitos erros de rate limiting:

- O script já tem delays automáticos entre requisições
- Aguarde alguns minutos e execute novamente
- Músicas duplicadas não serão adicionadas novamente

---

## 🎨 Legenda de Ícones

Durante a execução, você verá os seguintes indicadores:

- ✓ **Verde** = Música adicionada com sucesso
- ⊙ **Amarelo** = Música já existe na playlist (pulada)
- ✗ **Vermelho** = Música não encontrada
- 🛡 **Azul** = Música protegida (não será removida)
- ⚠ **Amarelo** = Aviso importante
- ℹ **Ciano** = Informação

---

## 📝 Estrutura de Arquivos

```
migrador-playlists/
├── migrador.py              # Script principal
├── .env                     # Suas credenciais (não compartilhar!)
├── .env.example             # Exemplo de configuração
├── headers_auth.json        # Auth do YouTube Music (criar)
├── .spotify_cache           # Cache de autenticação (auto-gerado)
├── requirements.txt         # Dependências Python
├── README.md                # Esta documentação
└── nao_encontradas_*.txt    # Logs de músicas não encontradas (auto-gerado)
```

---

## ⚠️ Importante

- **Nunca compartilhe** seu arquivo `.env` ou `headers_auth.json`
- Estes arquivos contêm suas credenciais pessoais
- O `.gitignore` já está configurado para ignorá-los
- Mantenha suas credenciais em segurança!

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

---

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

---

## 💡 Dicas

1. **Primeira vez?** Comece com uma playlist pequena para testar
2. **Muitas músicas?** O script processa em lotes automaticamente
3. **Duplicatas?** Não se preocupe, o script detecta e pula músicas já adicionadas
4. **Limpeza?** Sempre use a proteção por data para preservar suas músicas manuais

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique a seção de Solução de Problemas
2. Confira se todas as dependências estão instaladas
3. Certifique-se de que as credenciais estão corretas

---

**Feito com ❤️ para facilitar sua vida musical! 🎵**
