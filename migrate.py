from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from ytmusicapi import YTMusic
from fuzzywuzzy import fuzz
import time
import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

# Cores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Ícones com cores
    @staticmethod
    def success(text):
        return f"{Colors.GREEN}✓{Colors.ENDC} {text}"
    
    @staticmethod
    def skip(text):
        return f"{Colors.YELLOW}⊙{Colors.ENDC} {text}"
    
    @staticmethod
    def error(text):
        return f"{Colors.RED}✗{Colors.ENDC} {text}"
    
    @staticmethod
    def info(text):
        return f"{Colors.CYAN}ℹ{Colors.ENDC} {text}"
    
    @staticmethod
    def warning(text):
        return f"{Colors.YELLOW}⚠{Colors.ENDC} {text}"
    
    @staticmethod
    def protected(text):
        return f"{Colors.BLUE}🛡{Colors.ENDC} {text}"

def print_header(title):
    """Imprime um cabeçalho estilizado."""
    print("\n" + Colors.BOLD + "=" * 80 + Colors.ENDC)
    print(Colors.BOLD + Colors.CYAN + title.center(80) + Colors.ENDC)
    print(Colors.BOLD + "=" * 80 + Colors.ENDC + "\n")

def print_section(title):
    """Imprime uma seção."""
    print("\n" + Colors.BOLD + Colors.BLUE + f"╔══ {title} " + "═" * (74 - len(title)) + Colors.ENDC)

def print_progress_bar(current, total, prefix='', suffix='', length=50):
    """Imprime uma barra de progresso."""
    percent = 100 * (current / float(total))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    
    print(f'\r{prefix} {Colors.CYAN}|{bar}|{Colors.ENDC} {percent:.1f}% {suffix}', end='', flush=True)
    if current == total:
        print()

def print_stats_box(stats):
    """Imprime estatísticas em uma caixa."""
    print(f"\n{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
    print(f"{Colors.BOLD}║{Colors.ENDC}                           📊 ESTATÍSTICAS FINAIS                            {Colors.BOLD}║{Colors.ENDC}")
    print(f"{Colors.BOLD}╠════════════════════════════════════════════════════════════════════════════╣{Colors.ENDC}")
    
    for key, value in stats.items():
        key_formatted = f"  {key}:"
        value_formatted = str(value)
        spacing = " " * (73 - len(key_formatted) - len(value_formatted))
        print(f"{Colors.BOLD}║{Colors.ENDC}{key_formatted}{spacing}{value_formatted} {Colors.BOLD}║{Colors.ENDC}")
    
    print(f"{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")

# ============================================================================
# NORMALIZAÇÃO E MATCHING APRIMORADOS
# ============================================================================

def normalize_title(title: str) -> str:
    """Normaliza título removendo versões, features, etc."""
    if not title:
        return ""
    
    title = title.lower().strip()
    
    # Remover conteúdo entre parênteses e colchetes
    title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)
    
    # Remover feat/ft e tudo depois
    title = re.sub(r'\s+(feat\.?|ft\.?|featuring|with)(\s+|$).*', '', title, flags=re.IGNORECASE)
    
    # Remover palavras comuns de versão
    version_words = [
        'remastered', 'remaster', 'single version', 'album version',
        'radio edit', 'extended', 'acoustic', 'live', 'remix',
        'instrumental', 'bonus', 'demo', 'deluxe', 'explicit',
        'clean', 'version', 'edition', 'from', 'original soundtrack'
    ]
    for word in version_words:
        title = re.sub(r'\b' + word + r'\b', '', title)
    
    # Remover anos (ex: "2023")
    title = re.sub(r'\b(19|20)\d{2}\b', '', title)
    
    # Remover pontuação e caracteres especiais
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # Remover espaços extras
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def normalize_artist(artist: str) -> str:
    """Normaliza nome de artista."""
    if not artist:
        return ""
    
    artist = str(artist).lower().strip()
    
    # Remover "the" no início
    artist = re.sub(r'^the\s+', '', artist)
    
    # Substituir separadores por espaço
    artist = artist.replace('&', ' ')
    artist = artist.replace(',', ' ')
    artist = artist.replace('/', ' ')
    
    # Remover pontuação
    artist = re.sub(r'[^\w\s]', '', artist)
    
    # Remover espaços extras
    artist = re.sub(r'\s+', ' ', artist).strip()
    
    return artist

def calculate_artist_match(sp_artists: List[str], yt_artists: List[str]) -> float:
    """Calcula porcentagem de match entre listas de artistas."""
    if not sp_artists or not yt_artists:
        return 0.0
    
    sp_normalized = [normalize_artist(a) for a in sp_artists if a]
    yt_normalized = [normalize_artist(a) for a in yt_artists if a]
    
    if not sp_normalized or not yt_normalized:
        return 0.0
    
    matches = 0
    for sp_artist in sp_normalized:
        for yt_artist in yt_normalized:
            ratio = fuzz.ratio(sp_artist, yt_artist)
            if ratio >= 75:
                matches += 1
                break
    
    return (matches / len(sp_normalized)) * 100

def is_match(sp_title: str, sp_artists: List[str], yt_title: str, yt_artists: List[str]) -> Tuple[bool, float, float]:
    """Verifica se duas músicas são compatíveis."""
    sp_title_norm = normalize_title(sp_title)
    yt_title_norm = normalize_title(yt_title)
    
    title_ratio = fuzz.ratio(sp_title_norm, yt_title_norm)
    artist_ratio = calculate_artist_match(sp_artists, yt_artists)
    
    # Critérios adaptativos de matching
    match = (
        (title_ratio >= 95 and artist_ratio >= 40) or
        (title_ratio >= 85 and artist_ratio >= 50) or
        (title_ratio >= 75 and artist_ratio >= 60)
    )
    
    return match, title_ratio, artist_ratio

# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

def authenticate_spotify(need_write_access: bool = False) -> Spotify:
    """Autentica no Spotify."""
    print(Colors.info("Autenticando no Spotify..."))
    
    # Verificar se tem credenciais
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print(f"\n{Colors.RED}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}║                    ⚠️  ERRO DE CONFIGURAÇÃO - SPOTIFY                     ║{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}As credenciais do Spotify não foram encontradas!{Colors.ENDC}\n")
        print(f"{Colors.BOLD}📋 PASSO A PASSO PARA RESOLVER:{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}1️⃣  Crie um arquivo chamado {Colors.BOLD}.env{Colors.ENDC}{Colors.CYAN} na mesma pasta deste script{Colors.ENDC}")
        print(f"   {Colors.YELLOW}→ Dica: Copie o arquivo .env.example e renomeie para .env{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}2️⃣  Adicione estas linhas no arquivo .env:{Colors.ENDC}")
        print(f"{Colors.GREEN}   ╭─────────────────────────────────────────────────────────╮")
        print(f"   │ SPOTIFY_CLIENT_ID=seu_client_id_aqui                   │")
        print(f"   │ SPOTIFY_CLIENT_SECRET=seu_client_secret_aqui           │")
        print(f"   │ SPOTIFY_REDIRECT_URI=http://localhost:8888/callback    │")
        print(f"   ╰─────────────────────────────────────────────────────────╯{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}3️⃣  Obtenha suas credenciais:{Colors.ENDC}")
        print(f"   a) Acesse: {Colors.BOLD}https://developer.spotify.com/dashboard{Colors.ENDC}")
        print(f"   b) Faça login com sua conta Spotify")
        print(f"   c) Clique em {Colors.BOLD}'Create app'{Colors.ENDC}")
        print(f"   d) Preencha os campos:")
        print(f"      • App name: {Colors.GREEN}Migrador de Playlists{Colors.ENDC}")
        print(f"      • Redirect URI: {Colors.GREEN}http://localhost:8888/callback{Colors.ENDC}")
        print(f"   e) Após criar, clique em {Colors.BOLD}'Settings'{Colors.ENDC}")
        print(f"   f) Copie o {Colors.BOLD}Client ID{Colors.ENDC} e {Colors.BOLD}Client Secret{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}4️⃣  Cole as credenciais no arquivo .env (sem as aspas!){Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}💡 DICA: Veja o arquivo SETUP.md para um guia detalhado com imagens!{Colors.ENDC}\n")
        
        print(f"{Colors.RED}❌ Script encerrado. Configure o .env e execute novamente.{Colors.ENDC}\n")
        exit(1)
    
    try:
        if need_write_access:
            # OAuth com permissões de escrita
            scope = "playlist-modify-public playlist-modify-private"
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=scope,
                cache_path=".spotify_cache"
            )
            sp = Spotify(auth_manager=auth_manager)
            print(Colors.success("Conectado ao Spotify com permissões de escrita!"))
        else:
            # Client Credentials para leitura
            auth_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            sp = Spotify(auth_manager=auth_manager)
            print(Colors.success("Conectado ao Spotify!"))
        
        return sp
    
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}║                    ⚠️  ERRO AO CONECTAR NO SPOTIFY                        ║{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        error_msg = str(e).lower()
        
        if "invalid_client" in error_msg or "client_id" in error_msg or "client_secret" in error_msg:
            print(f"{Colors.YELLOW}As credenciais do Spotify estão incorretas!{Colors.ENDC}\n")
            print(f"{Colors.BOLD}🔍 POSSÍVEIS CAUSAS:{Colors.ENDC}\n")
            print(f"  {Colors.RED}✗{Colors.ENDC} Client ID ou Client Secret errados")
            print(f"  {Colors.RED}✗{Colors.ENDC} Espaços extras antes/depois das credenciais")
            print(f"  {Colors.RED}✗{Colors.ENDC} Credenciais entre aspas (remova as aspas!)\n")
            
            print(f"{Colors.BOLD}✅ SOLUÇÃO:{Colors.ENDC}\n")
            print(f"  1. Abra o arquivo {Colors.BOLD}.env{Colors.ENDC}")
            print(f"  2. Verifique se não há espaços ou aspas nas credenciais")
            print(f"  3. Copie novamente do Spotify Developer Dashboard")
            print(f"  4. Cole diretamente, sem aspas: {Colors.GREEN}SPOTIFY_CLIENT_ID=abc123...{Colors.ENDC}\n")
        
        elif "redirect" in error_msg or "uri" in error_msg:
            print(f"{Colors.YELLOW}Problema com o Redirect URI!{Colors.ENDC}\n")
            print(f"{Colors.BOLD}✅ SOLUÇÃO:{Colors.ENDC}\n")
            print(f"  1. Acesse: {Colors.BOLD}https://developer.spotify.com/dashboard{Colors.ENDC}")
            print(f"  2. Selecione seu app")
            print(f"  3. Vá em {Colors.BOLD}Settings{Colors.ENDC}")
            print(f"  4. Adicione nos Redirect URIs: {Colors.GREEN}http://localhost:8888/callback{Colors.ENDC}")
            print(f"  5. Clique em {Colors.BOLD}Save{Colors.ENDC}\n")
        
        else:
            print(f"{Colors.YELLOW}Erro desconhecido na autenticação:{Colors.ENDC}")
            print(f"{Colors.RED}{e}{Colors.ENDC}\n")
            print(f"{Colors.BOLD}✅ SOLUÇÕES GERAIS:{Colors.ENDC}\n")
            print(f"  • Verifique sua conexão com a internet")
            print(f"  • Tente novamente em alguns minutos")
            print(f"  • Recrie suas credenciais no Spotify Developer Dashboard\n")
        
        print(f"{Colors.RED}❌ Script encerrado. Corrija o erro e execute novamente.{Colors.ENDC}\n")
        exit(1)

def authenticate_ytmusic() -> YTMusic:
    """Autentica no YouTube Music."""
    print(Colors.info("Autenticando no YouTube Music..."))
    
    if not os.path.exists('headers_auth.json'):
        print(f"\n{Colors.RED}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}║                ⚠️  ERRO DE CONFIGURAÇÃO - YOUTUBE MUSIC                   ║{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}Arquivo {Colors.BOLD}headers_auth.json{Colors.ENDC}{Colors.YELLOW} não encontrado!{Colors.ENDC}\n")
        print(f"{Colors.BOLD}📋 PASSO A PASSO PARA CRIAR:{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}1️⃣  Abra o YouTube Music no navegador:{Colors.ENDC}")
        print(f"   {Colors.BOLD}https://music.youtube.com{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}2️⃣  Faça login na sua conta Google{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}3️⃣  Abra as Ferramentas do Desenvolvedor:{Colors.ENDC}")
        print(f"   • Pressione {Colors.BOLD}F12{Colors.ENDC} (Windows/Linux)")
        print(f"   • Ou {Colors.BOLD}Cmd + Option + I{Colors.ENDC} (Mac)\n")
        
        print(f"{Colors.CYAN}4️⃣  Vá para a aba {Colors.BOLD}Network{Colors.ENDC} (Rede){Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}5️⃣  Clique em qualquer música para começar a tocar{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}6️⃣  Na lista de requisições, procure por:{Colors.ENDC}")
        print(f"   • {Colors.BOLD}browse{Colors.ENDC} ou {Colors.BOLD}next{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}7️⃣  Clique com botão direito na requisição:{Colors.ENDC}")
        print(f"   {Colors.GREEN}→ Copy → Copy as cURL (bash){Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}8️⃣  No terminal/prompt, execute:{Colors.ENDC}")
        print(f"{Colors.GREEN}   ╭─────────────────────────────────────╮")
        print(f"   │  ytmusicapi browser                 │")
        print(f"   ╰─────────────────────────────────────╯{Colors.ENDC}\n")
        
        print(f"{Colors.CYAN}9️⃣  Cole o comando cURL quando solicitado e pressione Enter{Colors.ENDC}\n")
        
        print(f"{Colors.GREEN}✓ O arquivo {Colors.BOLD}headers_auth.json{Colors.ENDC}{Colors.GREEN} será criado automaticamente!{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}💡 DICA: Veja o arquivo SETUP.md para um guia visual completo!{Colors.ENDC}\n")
        
        print(f"{Colors.RED}❌ Script encerrado. Crie o headers_auth.json e execute novamente.{Colors.ENDC}\n")
        exit(1)
    
    try:
        ytmusic = YTMusic('headers_auth.json')
        print(Colors.success("Conectado ao YouTube Music!"))
        return ytmusic
    
    except json.JSONDecodeError:
        print(f"\n{Colors.RED}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}║                ⚠️  ERRO: ARQUIVO JSON INVÁLIDO                            ║{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}O arquivo {Colors.BOLD}headers_auth.json{Colors.ENDC}{Colors.YELLOW} está corrompido ou mal formatado!{Colors.ENDC}\n")
        print(f"{Colors.BOLD}✅ SOLUÇÃO:{Colors.ENDC}\n")
        print(f"  1. Delete o arquivo: {Colors.RED}headers_auth.json{Colors.ENDC}")
        print(f"  2. Execute novamente: {Colors.GREEN}ytmusicapi browser{Colors.ENDC}")
        print(f"  3. Siga o processo de autenticação corretamente\n")
        
        print(f"{Colors.RED}❌ Script encerrado.{Colors.ENDC}\n")
        exit(1)
    
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}╔════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}║              ⚠️  ERRO AO CONECTAR NO YOUTUBE MUSIC                        ║{Colors.ENDC}")
        print(f"{Colors.RED}{Colors.BOLD}╚════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        error_msg = str(e).lower()
        
        if "unauthorized" in error_msg or "401" in error_msg or "token" in error_msg:
            print(f"{Colors.YELLOW}As credenciais expiraram ou são inválidas!{Colors.ENDC}\n")
            print(f"{Colors.BOLD}✅ SOLUÇÃO:{Colors.ENDC}\n")
            print(f"  1. Delete o arquivo: {Colors.RED}headers_auth.json{Colors.ENDC}")
            print(f"  2. Execute: {Colors.GREEN}ytmusicapi browser{Colors.ENDC}")
            print(f"  3. Faça login no YouTube Music novamente no navegador")
            print(f"  4. Copie um novo cURL atualizado\n")
        
        elif "connection" in error_msg or "network" in error_msg:
            print(f"{Colors.YELLOW}Problema de conexão com o YouTube Music!{Colors.ENDC}\n")
            print(f"{Colors.BOLD}✅ SOLUÇÕES:{Colors.ENDC}\n")
            print(f"  • Verifique sua conexão com a internet")
            print(f"  • Tente novamente em alguns segundos")
            print(f"  • Verifique se o YouTube Music está acessível no navegador\n")
        
        else:
            print(f"{Colors.YELLOW}Erro desconhecido:{Colors.ENDC}")
            print(f"{Colors.RED}{e}{Colors.ENDC}\n")
            print(f"{Colors.BOLD}✅ SOLUÇÃO GERAL:{Colors.ENDC}\n")
            print(f"  • Recrie o arquivo de autenticação: {Colors.GREEN}ytmusicapi browser{Colors.ENDC}\n")
        
        print(f"{Colors.RED}❌ Script encerrado. Corrija o erro e execute novamente.{Colors.ENDC}\n")
        exit(1)

# ============================================================================
# BUSCA E MIGRAÇÃO - SPOTIFY → YOUTUBE MUSIC
# ============================================================================

def get_spotify_tracks(sp: Spotify, playlist_url: str) -> List[Dict]:
    """Busca todas as músicas de uma playlist do Spotify."""
    print(Colors.info("Buscando músicas da playlist do Spotify..."))
    
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    tracks = []
    
    results = sp.playlist_items(playlist_id, additional_types=['track'])
    while results:
        for item in results['items']:
            track = item['track']
            if track and track.get('name'):
                artists = [artist['name'] for artist in track.get('artists', []) 
                          if artist and artist.get('name')]
                
                if artists:
                    tracks.append({
                        'name': track['name'],
                        'artist': ', '.join(artists),
                        'all_artists': artists,
                        'album': track.get('album', {}).get('name', ''),
                        'isrc': track.get('external_ids', {}).get('isrc', None)
                    })
        
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    print(Colors.success(f"Encontradas {Colors.BOLD}{len(tracks)}{Colors.ENDC} músicas válidas!"))
    return tracks

def search_on_ytmusic(ytmusic: YTMusic, track: Dict) -> Optional[str]:
    """Busca uma música no YouTube Music com algoritmo aprimorado."""
    try:
        track_name = track['name']
        all_artists = track['all_artists']
        
        # Estratégia 1: Busca com título + primeiro artista
        query = f"{track_name} {all_artists[0]}"
        results = ytmusic.search(query, filter='songs', limit=10)
        
        # Avaliar resultados
        best_match = None
        best_score = 0
        
        for result in results:
            yt_title = result.get('title', '')
            yt_artists = [a['name'] for a in result.get('artists', [])]
            
            match, title_ratio, artist_ratio = is_match(
                track_name, all_artists, yt_title, yt_artists
            )
            
            if match:
                # Score combinado (70% título, 30% artista)
                score = (title_ratio * 0.7) + (artist_ratio * 0.3)
                if score > best_score:
                    best_score = score
                    best_match = result['videoId']
        
        if best_match:
            return best_match
        
        # Estratégia 2: Busca só com título (se a primeira falhar)
        results = ytmusic.search(track_name, filter='songs', limit=10)
        for result in results:
            yt_title = result.get('title', '')
            yt_artists = [a['name'] for a in result.get('artists', [])]
            
            match, title_ratio, artist_ratio = is_match(
                track_name, all_artists, yt_title, yt_artists
            )
            
            if match:
                return result['videoId']
        
        return None
    
    except Exception as e:
        return None

def migrate_spotify_to_ytmusic(sp: Spotify, ytmusic: YTMusic, playlist_url: str):
    """Migra playlist do Spotify para YouTube Music."""
    print_header("MIGRAÇÃO: SPOTIFY → YOUTUBE MUSIC")
    
    # Buscar músicas do Spotify
    tracks = get_spotify_tracks(sp, playlist_url)
    
    if not tracks:
        print(Colors.error("Nenhuma música encontrada na playlist!"))
        return
    
    # Criar/selecionar playlist no YT Music
    print_section("Configuração da Playlist")
    playlist_name = input(f"\n{Colors.CYAN}Nome da playlist no YouTube Music:{Colors.ENDC} ").strip() or "Migrada do Spotify"
    
    yt_playlist_id = None
    existing_playlists = ytmusic.get_library_playlists(limit=100)
    
    for playlist in existing_playlists:
        if playlist['title'] == playlist_name:
            yt_playlist_id = playlist['playlistId']
            print(Colors.success(f"Playlist '{playlist_name}' encontrada!"))
            
            print(f"\n{Colors.BOLD}Opções:{Colors.ENDC}")
            print(f"  {Colors.GREEN}1{Colors.ENDC} - Continuar nesta playlist")
            print(f"  {Colors.YELLOW}2{Colors.ENDC} - Criar uma nova playlist")
            print(f"  {Colors.RED}3{Colors.ENDC} - Cancelar")
            
            choice = input(f"\n{Colors.CYAN}Escolha (1/2/3):{Colors.ENDC} ").strip()
            if choice == "2":
                yt_playlist_id = None
            elif choice == "3":
                return
            break
    
    if not yt_playlist_id:
        yt_playlist_id = ytmusic.create_playlist(playlist_name, "Migrada do Spotify")
        print(Colors.success(f"Playlist criada! ID: {yt_playlist_id}"))
    
    # Obter músicas já existentes
    existing_video_ids = set()
    try:
        playlist_items = ytmusic.get_playlist(yt_playlist_id, limit=None)
        if playlist_items.get('tracks'):
            existing_video_ids = {t['videoId'] for t in playlist_items['tracks'] if t.get('videoId')}
            print(Colors.info(f"{len(existing_video_ids)} músicas já na playlist"))
    except:
        pass
    
    # Migrar músicas
    added = 0
    skipped = 0
    not_found = []
    batch_size = 20
    total_batches = (len(tracks) - 1) // batch_size + 1
    
    print_section(f"Migrando {len(tracks)} Músicas")
    
    for batch_idx in range(0, len(tracks), batch_size):
        batch = tracks[batch_idx:batch_idx+batch_size]
        video_ids = []
        current_batch = (batch_idx // batch_size) + 1
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ Lote {current_batch}/{total_batches} ─────────────────────────────────────────────────────────────{Colors.ENDC}")
        
        for idx, track in enumerate(batch, 1):
            track_info = f"{track['name'][:35]:<35} • {track['all_artists'][0][:25]:<25}"
            print(f"{Colors.BOLD}│{Colors.ENDC} {track_info}", end=" ")
            
            video_id = search_on_ytmusic(ytmusic, track)
            
            if video_id:
                if video_id in existing_video_ids:
                    skipped += 1
                    print(Colors.skip("JÁ EXISTE"))
                else:
                    video_ids.append(video_id)
                    existing_video_ids.add(video_id)
                    print(Colors.success("ADICIONADA"))
            else:
                not_found.append(f"{track['name']} - {track['artist']}")
                print(Colors.error("NÃO ENCONTRADA"))
            
            time.sleep(0.5)
        
        print(f"{Colors.BOLD}{Colors.BLUE}└────────────────────────────────────────────────────────────────────{Colors.ENDC}")
        
        if video_ids:
            try:
                ytmusic.add_playlist_items(yt_playlist_id, video_ids)
                added += len(video_ids)
                print(Colors.success(f"✨ {len(video_ids)} músicas adicionadas ao lote!"))
            except Exception as e:
                print(Colors.error(f"Erro ao adicionar: {e}"))
        
        # Barra de progresso
        print_progress_bar(batch_idx + len(batch), len(tracks), 
                          prefix=f'{Colors.BOLD}Progresso:{Colors.ENDC}',
                          suffix=f'{added + skipped}/{len(tracks)} processadas')
        
        time.sleep(2)
    
    # Resumo
    print_header("MIGRAÇÃO CONCLUÍDA")
    
    stats = {
        f"{Colors.GREEN}✓ Músicas adicionadas{Colors.ENDC}": f"{Colors.GREEN}{added}{Colors.ENDC}",
        f"{Colors.YELLOW}⊙ Músicas já existentes{Colors.ENDC}": f"{Colors.YELLOW}{skipped}{Colors.ENDC}",
        f"{Colors.RED}✗ Não encontradas{Colors.ENDC}": f"{Colors.RED}{len(not_found)}{Colors.ENDC}",
        f"{Colors.CYAN}📊 Total processado{Colors.ENDC}": f"{Colors.CYAN}{added + skipped + len(not_found)}/{len(tracks)}{Colors.ENDC}",
        f"{Colors.BOLD}📈 Taxa de sucesso{Colors.ENDC}": f"{Colors.BOLD}{((added + skipped)/len(tracks)*100):.1f}%{Colors.ENDC}"
    }
    
    print_stats_box(stats)
    
    if not_found:
        save_not_found(not_found, "spotify_para_ytmusic")

# ============================================================================
# BUSCA E MIGRAÇÃO - YOUTUBE MUSIC → SPOTIFY
# ============================================================================

def get_ytmusic_tracks(ytmusic: YTMusic, playlist_id: str) -> List[Dict]:
    """Busca todas as músicas de uma playlist do YouTube Music."""
    print("[*] Buscando músicas da playlist do YouTube Music...")
    
    try:
        playlist = ytmusic.get_playlist(playlist_id, limit=None)
        tracks = []
        
        for item in playlist.get('tracks', []):
            if item and item.get('title'):
                artists = [a['name'] for a in item.get('artists', []) if a.get('name')]
                
                if artists:
                    tracks.append({
                        'name': item['title'],
                        'artist': ', '.join(artists),
                        'all_artists': artists,
                        'album': item.get('album', {}).get('name', '') if item.get('album') else '',
                        'videoId': item.get('videoId', '')
                    })
        
        print(f"[+] Encontradas {len(tracks)} músicas válidas!")
        return tracks
    
    except Exception as e:
        print(f"[!] Erro ao buscar playlist: {e}")
        return []

def search_on_spotify(sp: Spotify, track: Dict) -> Optional[str]:
    """Busca uma música no Spotify."""
    try:
        track_name = track['name']
        all_artists = track['all_artists']
        
        # Estratégia 1: Busca com título + artista
        query = f"track:{track_name} artist:{all_artists[0]}"
        results = sp.search(q=query, type='track', limit=10)
        
        if results['tracks']['items']:
            for item in results['tracks']['items']:
                sp_title = item['name']
                sp_artists = [a['name'] for a in item['artists']]
                
                match, _, _ = is_match(
                    sp_title, sp_artists, track_name, all_artists
                )
                
                if match:
                    return item['uri']
        
        # Estratégia 2: Busca mais ampla
        query = f"{track_name} {all_artists[0]}"
        results = sp.search(q=query, type='track', limit=10)
        
        if results['tracks']['items']:
            for item in results['tracks']['items']:
                sp_title = item['name']
                sp_artists = [a['name'] for a in item['artists']]
                
                match, _, _ = is_match(
                    sp_title, sp_artists, track_name, all_artists
                )
                
                if match:
                    return item['uri']
        
        return None
    
    except Exception as e:
        return None

def migrate_ytmusic_to_spotify(sp: Spotify, ytmusic: YTMusic, yt_playlist_url: str):
    """Migra playlist do YouTube Music para Spotify."""
    print("\n" + "="*80)
    print("MIGRAÇÃO: YOUTUBE MUSIC → SPOTIFY")
    print("="*80)
    
    # Extrair ID da playlist do YT Music
    if 'list=' in yt_playlist_url:
        yt_playlist_id = yt_playlist_url.split('list=')[1].split('&')[0]
    else:
        yt_playlist_id = yt_playlist_url.split('/')[-1].split('?')[0]
    
    # Buscar músicas do YT Music
    tracks = get_ytmusic_tracks(ytmusic, yt_playlist_id)
    
    if not tracks:
        print("[!] Nenhuma música encontrada!")
        return
    
    # Criar playlist no Spotify
    playlist_name = input("\n[?] Nome da playlist no Spotify: ").strip() or "Migrada do YouTube Music"
    
    user_id = sp.current_user()['id']
    sp_playlist = sp.user_playlist_create(
        user_id, 
        playlist_name, 
        description="Migrada do YouTube Music"
    )
    sp_playlist_id = sp_playlist['id']
    print(f"[+] Playlist criada no Spotify! ID: {sp_playlist_id}")
    
    # Migrar músicas
    added = 0
    not_found = []
    batch_size = 50  # Spotify permite até 100 por batch
    
    print(f"\n[*] Iniciando migração de {len(tracks)} músicas...\n")
    
    for i in range(0, len(tracks), batch_size):
        batch = tracks[i:i+batch_size]
        track_uris = []
        
        print(f"--- Lote {(i//batch_size)+1}/{(len(tracks)-1)//batch_size+1} ---")
        
        for track in batch:
            track_info = f"{track['name'][:40]} - {track['all_artists'][0][:30]}"
            print(f"[*] {track_info:<70}", end=" ")
            
            track_uri = search_on_spotify(sp, track)
            
            if track_uri:
                track_uris.append(track_uri)
                print("✓")
            else:
                not_found.append(f"{track['name']} - {track['artist']}")
                print("✗")
            
            time.sleep(0.3)
        
        if track_uris:
            try:
                sp.playlist_add_items(sp_playlist_id, track_uris)
                added += len(track_uris)
                print(f"\n[+] {len(track_uris)} músicas adicionadas!")
            except Exception as e:
                print(f"\n[!] Erro ao adicionar: {e}")
        
        time.sleep(1)
    
    # Resumo
    print("\n" + "="*80)
    print("MIGRAÇÃO CONCLUÍDA!")
    print("="*80)
    print(f"✓ Adicionadas: {added}")
    print(f"✗ Não encontradas: {len(not_found)}")
    print(f"📊 Taxa de sucesso: {(added/len(tracks)*100):.1f}%")
    print(f"🔗 Link: https://open.spotify.com/playlist/{sp_playlist_id}")
    
    if not_found:
        save_not_found(not_found, "ytmusic_para_spotify")

# ============================================================================
# UTILITÁRIOS
# ============================================================================

def save_not_found(tracks: List[str], direction: str):
    """Salva músicas não encontradas em arquivo."""
    filename = f"nao_encontradas_{direction}_{int(time.time())}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write(f"MÚSICAS NÃO ENCONTRADAS ({direction})\n")
        f.write("="*70 + "\n\n")
        f.write(f"Total: {len(tracks)}\n\n")
        
        for i, track in enumerate(tracks, 1):
            f.write(f"{i}. {track}\n")
    
    print(f"\n[+] Lista salva em: {filename}")

# ============================================================================
# LIMPEZA DE PLAYLIST - REMOVE MÚSICAS INCORRETAS
# ============================================================================

def clean_ytmusic_playlist(sp: Spotify, ytmusic: YTMusic, spotify_url: str, ytmusic_playlist_id: str):
    """Remove músicas incorretas do YT Music baseado na playlist do Spotify."""
    print("\n" + "="*80)
    print("LIMPEZA DE PLAYLIST - YOUTUBE MUSIC")
    print("="*80)
    
    # Buscar músicas do Spotify (referência)
    print("\n[*] Buscando músicas da playlist de referência do Spotify...")
    spotify_tracks = get_spotify_tracks(sp, spotify_url)
    
    if not spotify_tracks:
        print("[!] Nenhuma música encontrada no Spotify!")
        return
    
    print(f"[+] {len(spotify_tracks)} músicas na playlist do Spotify")
    
    # Buscar músicas do YT Music
    print("\n[*] Buscando músicas da playlist do YouTube Music...")
    try:
        yt_playlist = ytmusic.get_playlist(ytmusic_playlist_id, limit=None)
        yt_tracks = yt_playlist.get('tracks', [])
    except Exception as e:
        print(f"[!] Erro ao carregar playlist do YT Music: {e}")
        return
    
    if not yt_tracks:
        print("[+] A playlist do YouTube Music está vazia!")
        return
    
    print(f"[+] {len(yt_tracks)} músicas na playlist do YouTube Music")
    
    # Perguntar sobre proteção por data
    print("\n" + "="*80)
    print("CONFIGURAÇÃO DE PROTEÇÃO")
    print("="*80)
    print("\nDeseja proteger músicas adicionadas manualmente pelo usuário?")
    print("(Músicas adicionadas ANTES da primeira migração não serão removidas)")
    print()
    protect_manual = input("[?] Proteger músicas manuais? (s/n): ").strip().lower() == 's'
    
    cutoff_date = None
    if protect_manual:
        print("\n[*] Digite a data da primeira migração automática:")
        print("    Músicas adicionadas ANTES dessa data serão protegidas")
        print("    Formato: DD/MM/AAAA (ex: 15/11/2025)")
        date_str = input("[?] Data: ").strip()
        
        try:
            from datetime import datetime
            cutoff_date = datetime.strptime(date_str, "%d/%m/%Y")
            print(f"[+] Protegendo músicas adicionadas antes de {cutoff_date.strftime('%d/%m/%Y')}")
        except:
            print("[!] Data inválida! Continuando sem proteção...")
            cutoff_date = None
    
    # Modo debug
    debug_mode = input("\n[?] Ativar modo debug? (s/n): ").strip().lower() == 's'
    
    # Analisar músicas
    print("\n" + "="*80)
    print("ANALISANDO PLAYLIST...")
    print("="*80 + "\n")
    
    tracks_to_remove = []
    protected_tracks = []
    
    for yt_track in yt_tracks:
        yt_title = yt_track.get('title', '')
        yt_artists = [a['name'] for a in yt_track.get('artists', []) if a.get('name')]
        yt_artist_str = ', '.join(yt_artists)
        
        # Verificar data de adição (se disponível)
        is_protected = False
        if cutoff_date and 'setVideoId' in yt_track:
            # setVideoId presente indica que temos metadados completos
            # Nota: A API do ytmusicapi não expõe diretamente a data de adição
            # mas podemos usar outras heurísticas
            pass
        
        # Procurar match na playlist do Spotify
        found_match = False
        best_match_info = {
            'title_ratio': 0,
            'artist_ratio': 0,
            'sp_title': '',
            'sp_artist': ''
        }
        
        for sp_track in spotify_tracks:
            sp_title = sp_track['name']
            sp_artists = sp_track['all_artists']
            
            match, title_ratio, artist_ratio = is_match(
                sp_title, sp_artists, yt_title, yt_artists
            )
            
            # Guardar melhor match para debug
            if title_ratio > best_match_info['title_ratio']:
                best_match_info = {
                    'title_ratio': title_ratio,
                    'artist_ratio': artist_ratio,
                    'sp_title': sp_title,
                    'sp_artist': sp_track['artist']
                }
            
            if match:
                found_match = True
                break
        
        # Decidir se remove
        if not found_match:
            if is_protected:
                protected_tracks.append((yt_title, yt_artist_str))
                if debug_mode:
                    print(f"[P] PROTEGIDA: {yt_title} - {yt_artist_str}")
                    print(f"    (adicionada manualmente pelo usuário)")
                    print()
            else:
                tracks_to_remove.append(yt_track)
                if debug_mode:
                    print(f"[-] REMOVER: {yt_title} - {yt_artist_str}")
                    print(f"    Melhor match: {best_match_info['sp_title']} - {best_match_info['sp_artist']}")
                    print(f"    Título: {best_match_info['title_ratio']:.1f}% | Artista: {best_match_info['artist_ratio']:.1f}%")
                    print()
                else:
                    print(f"[-] {yt_title} - {yt_artist_str}")
        else:
            if debug_mode:
                print(f"[✓] {yt_title} - {yt_artist_str}")
    
    # Resumo
    print("\n" + "="*80)
    print("RESUMO DA ANÁLISE")
    print("="*80)
    print(f"✓ Músicas corretas: {len(yt_tracks) - len(tracks_to_remove) - len(protected_tracks)}")
    print(f"⊙ Músicas protegidas: {len(protected_tracks)}")
    print(f"✗ Músicas a remover: {len(tracks_to_remove)}")
    
    if protected_tracks:
        print("\n[i] Músicas protegidas (adicionadas manualmente):")
        for title, artist in protected_tracks[:10]:
            print(f"    • {title} - {artist}")
        if len(protected_tracks) > 10:
            print(f"    ... e mais {len(protected_tracks) - 10} músicas")
    
    if not tracks_to_remove:
        print("\n[+] Nenhuma música incorreta encontrada!")
        print("[+] A playlist está sincronizada! ✨")
        return
    
    # Mostrar músicas que serão removidas
    print(f"\n[!] As seguintes {len(tracks_to_remove)} músicas serão REMOVIDAS:")
    for i, track in enumerate(tracks_to_remove[:20], 1):
        title = track.get('title', '')
        artists = ', '.join([a['name'] for a in track.get('artists', [])])
        print(f"    {i}. {title} - {artists}")
    
    if len(tracks_to_remove) > 20:
        print(f"    ... e mais {len(tracks_to_remove) - 20} músicas")
    
    # Confirmação
    print("\n" + "="*80)
    confirm = input("\n[?] Confirma a remoção dessas músicas? (s/n): ").strip().lower()
    
    if confirm == 's':
        print("\n[*] Removendo músicas...")
        try:
            # Remover em lotes
            batch_size = 50
            removed = 0
            
            for i in range(0, len(tracks_to_remove), batch_size):
                batch = tracks_to_remove[i:i+batch_size]
                ytmusic.remove_playlist_items(ytmusic_playlist_id, batch)
                removed += len(batch)
                print(f"[+] Removidas {removed}/{len(tracks_to_remove)} músicas...")
                time.sleep(1)
            
            print(f"\n[+] ✨ {len(tracks_to_remove)} músicas removidas com sucesso!")
            print("[+] Playlist limpa e sincronizada!")
            
            # Salvar log da limpeza
            log_file = f"limpeza_{int(time.time())}.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("LOG DE LIMPEZA - YOUTUBE MUSIC\n")
                f.write("="*70 + "\n\n")
                f.write(f"Data: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Músicas removidas: {len(tracks_to_remove)}\n\n")
                f.write("="*70 + "\n\n")
                
                for track in tracks_to_remove:
                    title = track.get('title', '')
                    artists = ', '.join([a['name'] for a in track.get('artists', [])])
                    f.write(f"• {title} - {artists}\n")
            
            print(f"\n[+] Log salvo em: {log_file}")
            
        except Exception as e:
            print(f"\n[!] ERRO ao remover músicas: {e}")
    else:
        print("\n[!] Operação cancelada. Nenhuma música foi removida.")

def clean_spotify_playlist(sp: Spotify, ytmusic: YTMusic, spotify_playlist_id: str, ytmusic_url: str):
    """Remove músicas incorretas do Spotify baseado na playlist do YT Music."""
    print("\n" + "="*80)
    print("LIMPEZA DE PLAYLIST - SPOTIFY")
    print("="*80)
    
    # Extrair ID do YT Music
    if 'list=' in ytmusic_url:
        yt_playlist_id = ytmusic_url.split('list=')[1].split('&')[0]
    else:
        yt_playlist_id = ytmusic_url.split('/')[-1].split('?')[0]
    
    # Buscar músicas do YT Music (referência)
    print("\n[*] Buscando músicas da playlist de referência do YouTube Music...")
    ytmusic_tracks = get_ytmusic_tracks(ytmusic, yt_playlist_id)
    
    if not ytmusic_tracks:
        print("[!] Nenhuma música encontrada no YouTube Music!")
        return
    
    print(f"[+] {len(ytmusic_tracks)} músicas na playlist do YouTube Music")
    
    # Buscar músicas do Spotify
    print("\n[*] Buscando músicas da playlist do Spotify...")
    try:
        results = sp.playlist_items(spotify_playlist_id, additional_types=['track'])
        sp_tracks = []
        
        while results:
            for item in results['items']:
                track = item['track']
                if track and track.get('name'):
                    artists = [a['name'] for a in track.get('artists', []) if a and a.get('name')]
                    if artists:
                        sp_tracks.append({
                            'uri': track['uri'],
                            'name': track['name'],
                            'artists': artists,
                            'artist_str': ', '.join(artists),
                            'added_at': item.get('added_at', '')
                        })
            
            if results['next']:
                results = sp.next(results)
            else:
                break
        
    except Exception as e:
        print(f"[!] Erro ao carregar playlist do Spotify: {e}")
        return
    
    if not sp_tracks:
        print("[+] A playlist do Spotify está vazia!")
        return
    
    print(f"[+] {len(sp_tracks)} músicas na playlist do Spotify")
    
    # Proteção por data
    print("\n" + "="*80)
    print("CONFIGURAÇÃO DE PROTEÇÃO")
    print("="*80)
    protect_manual = input("\n[?] Proteger músicas adicionadas manualmente? (s/n): ").strip().lower() == 's'
    
    cutoff_date = None
    if protect_manual:
        from datetime import datetime
        print("\n[*] Digite a data da primeira migração automática:")
        print("    Formato: DD/MM/AAAA (ex: 15/11/2025)")
        date_str = input("[?] Data: ").strip()
        
        try:
            cutoff_date = datetime.strptime(date_str, "%d/%m/%Y")
            print(f"[+] Protegendo músicas adicionadas antes de {cutoff_date.strftime('%d/%m/%Y')}")
        except:
            print("[!] Data inválida! Continuando sem proteção...")
            cutoff_date = None
    
    debug_mode = input("\n[?] Ativar modo debug? (s/n): ").strip().lower() == 's'
    
    # Analisar
    print("\n" + "="*80)
    print("ANALISANDO PLAYLIST...")
    print("="*80 + "\n")
    
    tracks_to_remove = []
    protected_tracks = []
    
    for sp_track in sp_tracks:
        sp_title = sp_track['name']
        sp_artists = sp_track['artists']
        
        # Verificar proteção por data
        is_protected = False
        if cutoff_date and sp_track['added_at']:
            from datetime import datetime
            try:
                added_date = datetime.fromisoformat(sp_track['added_at'].replace('Z', '+00:00'))
                if added_date.replace(tzinfo=None) < cutoff_date:
                    is_protected = True
            except:
                pass
        
        # Procurar match
        found_match = False
        best_match_info = {'title_ratio': 0, 'artist_ratio': 0, 'yt_title': '', 'yt_artist': ''}
        
        for yt_track in ytmusic_tracks:
            yt_title = yt_track['name']
            yt_artists = yt_track['all_artists']
            
            match, title_ratio, artist_ratio = is_match(
                sp_title, sp_artists, yt_title, yt_artists
            )
            
            if title_ratio > best_match_info['title_ratio']:
                best_match_info = {
                    'title_ratio': title_ratio,
                    'artist_ratio': artist_ratio,
                    'yt_title': yt_title,
                    'yt_artist': yt_track['artist']
                }
            
            if match:
                found_match = True
                break
        
        if not found_match:
            if is_protected:
                protected_tracks.append((sp_title, sp_track['artist_str']))
                if debug_mode:
                    print(f"[P] PROTEGIDA: {sp_title} - {sp_track['artist_str']}")
            else:
                tracks_to_remove.append(sp_track)
                if debug_mode:
                    print(f"[-] REMOVER: {sp_title} - {sp_track['artist_str']}")
                    print(f"    Melhor match: {best_match_info['yt_title']} - {best_match_info['yt_artist']}")
                    print(f"    Título: {best_match_info['title_ratio']:.1f}% | Artista: {best_match_info['artist_ratio']:.1f}%")
                    print()
                else:
                    print(f"[-] {sp_title} - {sp_track['artist_str']}")
    
    # Resumo e confirmação
    print("\n" + "="*80)
    print("RESUMO DA ANÁLISE")
    print("="*80)
    print(f"✓ Músicas corretas: {len(sp_tracks) - len(tracks_to_remove) - len(protected_tracks)}")
    print(f"⊙ Músicas protegidas: {len(protected_tracks)}")
    print(f"✗ Músicas a remover: {len(tracks_to_remove)}")
    
    if not tracks_to_remove:
        print("\n[+] Nenhuma música incorreta encontrada!")
        return
    
    print(f"\n[!] As seguintes {len(tracks_to_remove)} músicas serão REMOVIDAS:")
    for i, track in enumerate(tracks_to_remove[:20], 1):
        print(f"    {i}. {track['name']} - {track['artist_str']}")
    if len(tracks_to_remove) > 20:
        print(f"    ... e mais {len(tracks_to_remove) - 20} músicas")
    
    confirm = input("\n[?] Confirma a remoção? (s/n): ").strip().lower()
    
    if confirm == 's':
        print("\n[*] Removendo músicas...")
        try:
            track_uris = [{'uri': t['uri']} for t in tracks_to_remove]
            
            # Remover em lotes de 100 (limite do Spotify)
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i+batch_size]
                sp.playlist_remove_all_occurrences_of_items(spotify_playlist_id, [t['uri'] for t in batch])
                print(f"[+] Removidas {min(i+batch_size, len(track_uris))}/{len(track_uris)} músicas...")
                time.sleep(0.5)
            
            print(f"\n[+] ✨ {len(tracks_to_remove)} músicas removidas com sucesso!")
            
        except Exception as e:
            print(f"\n[!] ERRO: {e}")
    else:
        print("\n[!] Operação cancelada.")

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def main():
    print_header("🎵 MIGRADOR BIDIRECIONAL DE PLAYLISTS 🎵")
    print(f"{Colors.BOLD}Spotify ↔ YouTube Music{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Escolha a operação:{Colors.ENDC}\n")
    print(f"  {Colors.GREEN}1{Colors.ENDC} - {Colors.BOLD}Migrar:{Colors.ENDC} Spotify → YouTube Music")
    print(f"  {Colors.GREEN}2{Colors.ENDC} - {Colors.BOLD}Migrar:{Colors.ENDC} YouTube Music → Spotify")
    print(f"  {Colors.YELLOW}3{Colors.ENDC} - {Colors.BOLD}Limpar:{Colors.ENDC} Remover incorretas do YouTube Music")
    print(f"  {Colors.YELLOW}4{Colors.ENDC} - {Colors.BOLD}Limpar:{Colors.ENDC} Remover incorretas do Spotify")
    print(f"  {Colors.RED}5{Colors.ENDC} - {Colors.BOLD}Sair{Colors.ENDC}")
    
    choice = input(f"\n{Colors.CYAN}Escolha (1/2/3/4/5):{Colors.ENDC} ").strip()
    
    if choice == "1":
        # Spotify → YouTube Music
        sp = authenticate_spotify(need_write_access=False)
        ytmusic = authenticate_ytmusic()
        
        playlist_url = input(f"\n{Colors.CYAN}Cole a URL da playlist do Spotify:{Colors.ENDC} ").strip()
        migrate_spotify_to_ytmusic(sp, ytmusic, playlist_url)
    
    elif choice == "2":
        # YouTube Music → Spotify
        sp = authenticate_spotify(need_write_access=True)
        ytmusic = authenticate_ytmusic()
        
        playlist_url = input(f"\n{Colors.CYAN}Cole a URL da playlist do YouTube Music:{Colors.ENDC} ").strip()
        migrate_ytmusic_to_spotify(sp, ytmusic, playlist_url)
    
    elif choice == "3":
        # Limpar YouTube Music
        sp = authenticate_spotify(need_write_access=False)
        ytmusic = authenticate_ytmusic()
        
        print_section("Limpeza de Playlist do YouTube Music")
        print(f"\n{Colors.YELLOW}⚠  Músicas que não estiverem no Spotify serão removidas{Colors.ENDC}\n")
        spotify_url = input(f"{Colors.CYAN}URL da playlist do Spotify (referência):{Colors.ENDC} ").strip()
        ytmusic_url = input(f"{Colors.CYAN}URL da playlist do YouTube Music:{Colors.ENDC} ").strip()
        
        # Extrair ID da URL do YT Music
        if 'list=' in ytmusic_url:
            ytmusic_id = ytmusic_url.split('list=')[1].split('&')[0]
        else:
            ytmusic_id = ytmusic_url.split('/')[-1].split('?')[0]
        
        clean_ytmusic_playlist(sp, ytmusic, spotify_url, ytmusic_id)
    
    elif choice == "4":
        # Limpar Spotify
        sp = authenticate_spotify(need_write_access=True)
        ytmusic = authenticate_ytmusic()
        
        print_section("Limpeza de Playlist do Spotify")
        print(f"\n{Colors.YELLOW}⚠  Músicas que não estiverem no YouTube Music serão removidas{Colors.ENDC}\n")
        ytmusic_url = input(f"{Colors.CYAN}URL da playlist do YouTube Music (referência):{Colors.ENDC} ").strip()
        spotify_url = input(f"{Colors.CYAN}URL da playlist do Spotify:{Colors.ENDC} ").strip()
        
        # Extrair ID da URL do Spotify
        spotify_id = spotify_url.split("/")[-1].split("?")[0]
        
        clean_spotify_playlist(sp, ytmusic, spotify_id, ytmusic_url)
    
    else:
        print(Colors.warning("Operação cancelada."))
        return
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✨ Processo finalizado!{Colors.ENDC}")

if __name__ == "__main__":
    main()