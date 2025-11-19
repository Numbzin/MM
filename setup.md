# 🚀 Guia Rápido de Instalação

Siga estes passos para configurar o Migrador de Playlists em menos de 5 minutos!

---

## 📦 Passo 1: Instalar Python

### Windows

1. Baixe Python em: https://www.python.org/downloads/
2. **IMPORTANTE**: Marque a opção "Add Python to PATH" durante a instalação
3. Clique em "Install Now"

### Linux/Mac

Python já vem instalado. Verifique a versão:

```bash
python3 --version
```

---

## 📥 Passo 2: Baixar o Projeto

### Opção A: Download direto

1. Clique no botão verde "Code" no GitHub
2. Clique em "Download ZIP"
3. Extraia o arquivo em uma pasta de sua escolha

### Opção B: Git clone

```bash
git clone https://github.com/Numbzin/MM.git
cd MM
```

---

## 🔧 Passo 3: Instalar Dependências

Abra o terminal/prompt de comando na pasta do projeto e execute:

### Windows

```bash
pip install -r requirements.txt
```

### Linux/Mac

```bash
pip3 install -r requirements.txt
```

**Aguarde a instalação terminar** (pode levar alguns minutos)

---

## 🎵 Passo 4: Configurar Spotify

### 4.1. Criar App no Spotify

1. Acesse: https://developer.spotify.com/dashboard
2. Faça login (ou crie uma conta grátis)
3. Clique em **"Create app"**
4. Preencha:
   ```
   App name: Migrador de Playlists
   App description: Ferramenta pessoal para migrar playlists
   Redirect URI: http://localhost:8888/callback
   ```
5. Marque as caixas de concordância
6. Clique em **"Save"**

### 4.2. Obter Credenciais

1. Na página do app, clique em **"Settings"**
2. Copie o **Client ID**
3. Clique em **"View client secret"** e copie o **Client Secret**

### 4.3. Criar arquivo .env

1. Copie o arquivo `.env.example` e renomeie para `.env`

   **Windows (Prompt de Comando)**:

   ```bash
   copy .env.example .env
   ```

   **Linux/Mac (Terminal)**:

   ```bash
   cp .env.example .env
   ```

2. Abra o arquivo `.env` com um editor de texto (Bloco de Notas, VS Code, etc.)

3. Cole suas credenciais:

   ```bash
   SPOTIFY_CLIENT_ID=cole_seu_client_id_aqui
   SPOTIFY_CLIENT_SECRET=cole_seu_client_secret_aqui
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

4. **Salve o arquivo**

---

## 🎬 Passo 5: Configurar YouTube Music

### 5.1. Instalar ytmusicapi (se ainda não instalou)

```bash
pip install ytmusicapi
```

### 5.2. Criar headers_auth.json

> **Recomendação:** Use o navegador **Google Chrome** para capturar os headers do YouTube Music. Outros navegadores podem gerar comandos cURL incompatíveis ou incompletos.

1. Abra o **YouTube Music** no navegador: https://music.youtube.com
2. Faça login na sua conta
3. Pressione **F12** para abrir as Ferramentas do Desenvolvedor
4. Vá para a aba **Network** (Rede)
5. Clique em qualquer música para começar a tocar
6. Na lista de requisições, procure por **browse** ou **next**
7. Clique com botão direito → **Copy** → **Copy as cURL (bash)**

8. No terminal/prompt, execute:

   ```bash
   ytmusicapi browser
   ```

9. Cole o comando cURL quando solicitado e pressione Enter
10. O arquivo `headers_auth.json` será criado automaticamente! ✅

---

## ✅ Passo 6: Testar

Execute o script:

### Windows

```bash
python migrador.py
```

### Linux/Mac

```bash
python3 migrador.py
```

Se aparecer o menu principal colorido, está tudo pronto! 🎉

---

## 🎯 Primeiro Uso Recomendado

1. Escolha a opção **1** (Spotify → YouTube Music)
2. Use uma playlist pequena (10-20 músicas) para testar
3. Verifique se as músicas foram adicionadas corretamente
4. Depois migre suas playlists maiores!

---

## ❓ Problemas Comuns

### "pip não é reconhecido como comando"

- **Solução**: Reinstale o Python e marque "Add Python to PATH"

### "ModuleNotFoundError: No module named 'dotenv'"

- **Solução**: Execute novamente `pip install -r requirements.txt`

### "Credenciais do Spotify não configuradas"

- **Solução**: Verifique se o arquivo `.env` existe e está preenchido corretamente
- Certifique-se de que não há espaços extras nas credenciais

### "Nenhum arquivo de autenticação encontrado" (YouTube Music)

- **Solução**: Execute `ytmusicapi browser` e siga o passo 5.2 novamente

### Browser não abre no OAuth do Spotify

- **Solução**: Copie o link que aparece no terminal e cole no navegador manualmente

---

## 📝 Checklist Final

Antes de usar, certifique-se de que:

- [ ] Python 3.7+ instalado
- [ ] Todas as dependências instaladas (`requirements.txt`)
- [ ] Arquivo `.env` criado com credenciais do Spotify
- [ ] Arquivo `headers_auth.json` criado para YouTube Music
- [ ] Script abre e mostra o menu principal

---

## 🎊 Pronto!

Agora você está pronto para migrar suas playlists!

**Dica**: Comece com playlists pequenas e depois vá para as maiores. 😊

---

## 💬 Precisa de Ajuda?

- Leia o **README.md** completo para mais detalhes
- Verifique a seção de **Solução de Problemas** no README
- Abra uma issue no GitHub se o problema persistir

**Boas migrações! 🎵**
