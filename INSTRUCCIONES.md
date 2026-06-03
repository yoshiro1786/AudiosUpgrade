# Instrucciones: Gestor de Publicidad Automática (Windows)

Este sistema te permite pausar automáticamente la música que estás reproduciendo en tu navegador (YouTube u otros reproductores) cada cierto tiempo, reproducir un anuncio publicitario desde una carpeta local y reanudar la música en cuanto termine el anuncio.

---

## 📋 Requisitos Previos

1. **Python instalado:** Asegúrate de tener Python instalado en tu computadora con Windows.
   * *¿Cómo verificar?* Abre una consola de comandos (CMD) y escribe `python --version`. Si no está instalado, descárgalo gratis desde [python.org](https://www.python.org/downloads/).

---

## 🚀 Guía de Configuración y Uso

### Paso 1: Colocar los anuncios de publicidad
1. Abre la carpeta `publicidad` dentro del directorio del proyecto.
2. Copia y pega aquí tus archivos de anuncios (en formato `.mp3`, `.wav` o `.m4a`).
3. Puedes poner la cantidad de anuncios que desees; el sistema barajará y rotará los anuncios automáticamente. Asegura que todos suenen una vez antes de repetir cualquier anuncio.

### Paso 2: Personalizar la configuración
Abre el archivo `config.json` con cualquier editor de textos (como el Bloc de notas) para ajustar el comportamiento:
```json
{
  "intervalo_minutos": 15,
  "reproducir_si_no_hay_musica": false
}
```
* **`intervalo_minutos`:** Ajusta la cantidad de minutos entre anuncios (ej. `15` para cada cuarto de hora, `0.5` para hacer pruebas cada 30 segundos).
* **`reproducir_si_no_hay_musica`:** 
  * `false` (Recomendado): Si YouTube está pausado o no hay música sonando, el sistema se saltará el anuncio para no perturbar el silencio.
  * `true`: Reproducirá el anuncio estrictamente cada X minutos, incluso si la música está en silencio.

### Paso 3: Probar manualmente
1. Abre YouTube en tu navegador (Chrome, Edge, Brave o Firefox) y reproduce cualquier canción.
2. Haz doble clic en el archivo `iniciar_publicidad.bat`.
3. Verás una pantalla en la consola mostrando un conteo en vivo con el tiempo restante, el estado de la música y el último anuncio reproducido.
4. Para realizar una prueba rápida, puedes cambiar temporalmente `"intervalo_minutos"` a `0.2` (12 segundos) en `config.json` para comprobar que la pausa, reproducción del anuncio y reanudación funcionan a la perfección.

---

## ⚙️ Automatización: Iniciar automáticamente al encender la PC

Para hacer que el gestor se abra solo al encender tu computadora:

1. Busca el archivo `iniciar_publicidad.bat` en tu carpeta.
2. Haz clic derecho sobre él y selecciona **Mostrar más opciones** > **Crear acceso directo** (o *Enviar a* > *Escritorio (crear acceso directo)*).
3. Presiona la combinación de teclas `Win + R` en tu teclado.
4. En la ventana pequeña que aparece, escribe exactamente `shell:startup` y presiona **Enter**. Se abrirá la carpeta "Inicio" de Windows en el Explorador de archivos.
5. Corta el acceso directo que acabas de crear y pégalo dentro de esa carpeta "Inicio".

¡Listo! A partir de ese momento, cada vez que enciendas la PC y entres a Windows, el script se iniciará automáticamente y quedará activo monitoreando la música.
