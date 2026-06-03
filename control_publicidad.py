import os
import sys
import time
import json
import random
import subprocess

# Configuración de codificación para evitar errores de caracteres en consolas Windows (CMD/PowerShell)
if sys.platform.startswith('win'):
    import ctypes
    # Forzar consola a UTF-8 para que los caracteres como "ó", "í" se muestren bien
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)

# Helper para obtener rutas cortas en Windows (evita problemas con espacios y caracteres especiales en la API de Windows)
def get_short_path(long_path):
    if os.name != 'nt':
        return long_path
    try:
        from ctypes import wintypes
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(260)
        GetShortPathNameW(long_path, buf, 260)
        return buf.value if buf.value else long_path
    except Exception:
        return long_path

# =====================================================================
# SECCIÓN WINDOWS (PowerShell para SMTC + MCI winmm.dll para Audio)
# =====================================================================

def get_media_status_windows():
    # Retorna: 'PLAYING', 'PAUSED', 'NO_SESSION' o 'ERROR'
    ps_script = """
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null
    $Task = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
    $Task.AsTask().Wait()
    $SessionManager = $Task.GetResults()
    $CurrentSession = $SessionManager.GetCurrentSession()
    if ($CurrentSession) {
        $PlaybackInfo = $CurrentSession.GetPlaybackInfo()
        if ($PlaybackInfo.PlaybackStatus -eq 4) {
            Write-Output "PLAYING"
        } else {
            Write-Output "PAUSED"
        }
    } else {
        Write-Output "NO_SESSION"
    }
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=0x08000000  # CREATE_NO_WINDOW: evita parpadeos de consola
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def pause_media_windows():
    ps_script = """
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null
    $Task = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
    $Task.AsTask().Wait()
    $SessionManager = $Task.GetResults()
    $CurrentSession = $SessionManager.GetCurrentSession()
    if ($CurrentSession) {
        $CurrentSession.TryPauseAsync() | Out-Null
        Write-Output "PAUSED"
    } else {
        Write-Output "NO_SESSION"
    }
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=0x08000000
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def play_media_windows():
    ps_script = """
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime] | Out-Null
    $Task = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
    $Task.AsTask().Wait()
    $SessionManager = $Task.GetResults()
    $CurrentSession = $SessionManager.GetCurrentSession()
    if ($CurrentSession) {
        $CurrentSession.TryPlayAsync() | Out-Null
        Write-Output "PLAYING"
    } else {
        Write-Output "NO_SESSION"
    }
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=0x08000000
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def play_audio_windows(file_path):
    short_path = get_short_path(file_path)
    ctypes.windll.winmm.mciSendStringW('close ad_alias', None, 0, 0)
    
    open_cmd = f'open "{short_path}" type mpegvideo alias ad_alias'
    res = ctypes.windll.winmm.mciSendStringW(open_cmd, None, 0, 0)
    if res != 0:
        # Fallback sin especificar tipo (para algunos WAV)
        open_cmd = f'open "{short_path}" alias ad_alias'
        ctypes.windll.winmm.mciSendStringW(open_cmd, None, 0, 0)

    # El comando 'wait' detiene la ejecución del hilo hasta que el audio termine
    ctypes.windll.winmm.mciSendStringW('play ad_alias wait', None, 0, 0)
    ctypes.windll.winmm.mciSendStringW('close ad_alias', None, 0, 0)

# =====================================================================
# SECCIÓN MACOS (AppleScript para Navegador + afplay para Audio)
# =====================================================================

def get_media_status_mac():
    script = """
    tell application "System Events"
        set chromeRunning to exists (processes where name is "Google Chrome")
        set safariRunning to exists (processes where name is "Safari")
    end tell
    
    if chromeRunning then
        tell application "Google Chrome"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            set status to execute t javascript "var v = document.querySelector('video'); if (v) { v.paused ? 'PAUSED' : 'PLAYING'; } else { 'NO_VIDEO'; }"
                            if status is "PLAYING" then return "PLAYING"
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    
    if safariRunning then
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            set status to do JavaScript "var v = document.querySelector('video'); if (v) { v.paused ? 'PAUSED' : 'PLAYING'; } else { 'NO_VIDEO'; }" in t
                            if status is "PLAYING" then return "PLAYING"
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    
    return "NO_SESSION"
    """
    try:
        res = subprocess.run(["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = res.stdout.strip()
        return out if out else "NO_SESSION"
    except:
        return "NO_SESSION"

def pause_media_mac():
    script = """
    tell application "System Events"
        set chromeRunning to exists (processes where name is "Google Chrome")
        set safariRunning to exists (processes where name is "Safari")
    end tell
    
    set pausedAny to false
    if chromeRunning then
        tell application "Google Chrome"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            set res to execute t javascript "var v = document.querySelector('video'); if (v && !v.paused) { v.pause(); 'PAUSED'; } else { 'ALREADY_PAUSED'; }"
                            if res is "PAUSED" then set pausedAny to true
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    
    if safariRunning then
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            set res to do JavaScript "var v = document.querySelector('video'); if (v && !v.paused) { v.pause(); 'PAUSED'; } else { 'ALREADY_PAUSED'; }" in t
                            if res is "PAUSED" then set pausedAny to true
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    
    if pausedAny then
        return "PAUSED"
    else
        return "NO_SESSION"
    end if
    """
    try:
        res = subprocess.run(["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout.strip()
    except:
        return "NO_SESSION"

def play_media_mac():
    script = """
    tell application "System Events"
        set chromeRunning to exists (processes where name is "Google Chrome")
        set safariRunning to exists (processes where name is "Safari")
    end tell
    
    if chromeRunning then
        tell application "Google Chrome"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            execute t javascript "var v = document.querySelector('video'); if (v && v.paused) { v.play(); }"
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    
    if safariRunning then
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" then
                        try
                            do JavaScript "var v = document.querySelector('video'); if (v && v.paused) { v.play(); }" in t
                        end try
                    end if
                end repeat
            end repeat
        end tell
    end if
    """
    try:
        subprocess.run(["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except:
        pass

def play_audio_mac(file_path):
    subprocess.run(["afplay", file_path])

# =====================================================================
# WRAPPERS MULTIPLATAFORMA
# =====================================================================

def get_media_status():
    if os.name == 'nt':
        return get_media_status_windows()
    elif sys.platform == 'darwin':
        return get_media_status_mac()
    return "UNSUPPORTED"

def pause_media():
    if os.name == 'nt':
        return pause_media_windows()
    elif sys.platform == 'darwin':
        return pause_media_mac()
    return "UNSUPPORTED"

def play_media():
    if os.name == 'nt':
        return play_media_windows()
    elif sys.platform == 'darwin':
        return play_media_mac()
    return "UNSUPPORTED"

def play_audio(file_path):
    if os.name == 'nt':
        play_audio_windows(file_path)
    elif sys.platform == 'darwin':
        play_audio_mac(file_path)

# =====================================================================
# PROGRAMA PRINCIPAL Y MONITOREO
# =====================================================================

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_config():
    default_config = {
        "intervalo_minutos": 15,
        "reproducir_si_no_hay_musica": False
    }
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default_config.update(data)
        except Exception as e:
            print(f"Error cargando config.json, usando valores por defecto. Detalle: {e}")
    return default_config

def main():
    config = load_config()
    intervalo_segundos = max(10, int(config["intervalo_minutos"] * 60))
    reproducir_si_vacio = config["reproducir_si_no_hay_musica"]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ads_dir = os.path.join(script_dir, 'publicidad')

    # Asegurar que la carpeta de publicidad existe
    if not os.path.exists(ads_dir):
        os.makedirs(ads_dir)

    tiempo_restante = intervalo_segundos
    ultimo_anuncio = "Ninguno"
    ultimo_estado_reproductor = "Consultando..."
    segundos_desde_ultimo_check = 0
    pila_anuncios = []

    while True:
        try:
            # Consultar el estado del reproductor del navegador cada 10 segundos
            if segundos_desde_ultimo_check >= 10 or ultimo_estado_reproductor == "Consultando...":
                status = get_media_status()
                if status == "PLAYING":
                    ultimo_estado_reproductor = "Sonando música (YouTube)"
                elif status == "PAUSED":
                    ultimo_estado_reproductor = "Música pausada"
                elif status == "NO_SESSION":
                    ultimo_estado_reproductor = "Sin reproducción activa en navegador"
                else:
                    ultimo_estado_reproductor = f"Desconocido / {status}"
                segundos_desde_ultimo_check = 0

            # Dibujar la interfaz en la consola
            clear_console()
            print("=================================================================")
            print("         GESTOR DE PUBLICIDAD AUTOMÁTICA PARA MÚSICA             ")
            print("=================================================================")
            print(f" Sistema Operativo:   {sys.platform.upper()} (Soportado)")
            print(f" Ruta de anuncios:    {ads_dir}")
            print(f" Estado de la música: {ultimo_estado_reproductor}")
            print(f" Último anuncio:      {ultimo_anuncio}")
            print("-----------------------------------------------------------------")
            
            minutos = tiempo_restante // 60
            segundos = tiempo_restante % 60
            print(f" >> Siguiente anuncio en: {minutos:02d}:{segundos:02d}")
            print("=================================================================")
            print(" (Presiona CTRL + C para cerrar este programa)")

            time.sleep(1)
            tiempo_restante -= 1
            segundos_desde_ultimo_check += 1

            if tiempo_restante <= 0:
                # 1. Comprobar anuncios en la pila (verificar que sigan existiendo físicamente)
                pila_anuncios = [f for f in pila_anuncios if os.path.exists(os.path.join(ads_dir, f))]

                # Si la pila está vacía, recargar todos los anuncios disponibles y barajarlos
                if not pila_anuncios:
                    anuncios_disponibles = [f for f in os.listdir(ads_dir) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
                    if anuncios_disponibles:
                        random.shuffle(anuncios_disponibles)
                        pila_anuncios = anuncios_disponibles

                if not pila_anuncios:
                    clear_console()
                    print("\n[ADVERTENCIA] No hay archivos de audio (.mp3, .wav) en la carpeta 'publicidad'.")
                    print("Por favor, copia tus anuncios ahí para que puedan reproducirse.")
                    time.sleep(5)
                    tiempo_restante = 10  # Volver a intentar pronto
                    continue

                # 2. Consultar el estado justo antes de actuar
                status_actual = get_media_status()
                musica_activa = (status_actual == "PLAYING")

                if musica_activa or reproducir_si_vacio:
                    # Extraer el siguiente anuncio de la pila rotativa
                    ad_file = pila_anuncios.pop(0)
                    ad_path = os.path.join(ads_dir, ad_file)
                    ultimo_anuncio = ad_file

                    # Pausar si estaba reproduciendo
                    if musica_activa:
                        clear_console()
                        print("\n[INFO] Pausando música de YouTube...")
                        pause_media()
                        time.sleep(1)  # Pequeña pausa de transición

                    # Reproducir anuncio
                    clear_console()
                    print(f"\n[ALTAVOZ] Reproduciendo anuncio: {ad_file}")
                    play_audio(ad_path)
                    time.sleep(0.5)

                    # Reanudar si estaba reproduciendo
                    if musica_activa:
                        clear_console()
                        print("\n[INFO] Reanudando música de YouTube...")
                        play_media()
                        time.sleep(1)

                else:
                    clear_console()
                    print("\n[INFO] Omitiendo publicidad: YouTube no está reproduciendo música.")
                    time.sleep(3)

                # Resetear el cronómetro
                tiempo_restante = intervalo_segundos
                ultimo_estado_reproductor = "Consultando..."

        except KeyboardInterrupt:
            print("\nPrograma cerrado por el usuario.")
            break
        except Exception as e:
            print(f"\nOcurrió un error en el bucle principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
