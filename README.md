

````markdown
# 📡 PortalDrop

![PortalDrop Icon](https://github.com/danitxu79/PortalDrop/blob/main/portaldrop-512.png)

**El "AirDrop" Universal para Linux.**
Transfiere archivos entre tu PC y cualquier dispositivo móvil (iOS/Android) sin instalar nada en el teléfono.

---

## 🚀 ¿Qué es PortalDrop?

PortalDrop es una herramienta de escritorio minimalista construida con **Python** y **Qt6 (PySide6)**.

Resuelve un problema común: **Pasar una foto o documento del móvil al PC (o viceversa) rápidamente**, sin cables, sin subir cosas a la nube, y sin comprimir la calidad (como hace WhatsApp).

### ✨ Características
* **Sin instalación en el móvil:** Solo escaneas un QR y listo. Usa el navegador web.
* **Arrastrar y Soltar:** Arrastra un archivo a la ventana para generar un enlace de descarga instantáneo.
* **Bidireccional:** ¿Quieres pasar una foto del móvil al PC? Pulsa "Recibir" y súbela desde el navegador.
* **Privacidad Local:** Los archivos nunca salen de tu red WiFi. La transferencia es directa (P2P local).
* **Interfaz Moderna:** Modo oscuro nativo y diseño limpio.

---

## 🛠️ Instalación y Uso

### Prerrequisitos
* Python 3.10 o superior.
* Estar conectado a la misma red WiFi/LAN en ambos dispositivos.

### 1. Clonar y preparar entorno
```bash
# Crear carpeta y entorno virtual
mkdir PortalDrop
cd PortalDrop
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
````

### 2\. Ejecutar

Asegúrate de tener el archivo `portaldrop-512.png` en la carpeta para ver el icono.

```bash
python PortalDrop.py
```

-----

## 🔧 Solución de Problemas (Troubleshooting)

**El móvil no carga la página / "Connection Refused"**
Esto suele ser culpa del cortafuegos (Firewall) de Linux.

  * **Solución rápida:** Asegúrate de permitir el tráfico en el puerto **8000**.
    ```bash
    sudo ufw allow 8000/tcp
    ```
  * **Nota:** Si tu IP local cambia, reinicia la aplicación.

-----

## 🧠 Cómo funciona (Tech Stack)

  * **Frontend:** PySide6 (Qt6).
  * **Backend:** Servidor HTTP nativo de Python (`http.server` y `socketserver`) ejecutado en hilos separados (`QThread`) para no congelar la interfaz.
  * **Red:** Detecta automáticamente la IP de la LAN abriendo un socket UDP efímero.
  * **Protocolo:** HTTP estándar. Los archivos se envían tal cual (binario) mediante `Multipart/Form-Data` para subidas.

-----

## 📄 Licencia

Este proyecto es Open Source bajo la licencia **MIT**. Siéntete libre de modificarlo, romperlo y mejorarlo.

```

---

### Siguiente Nivel: Crear un Ejecutable (.exe / binario)

Ahora que tienes el código, los iconos y los requisitos, ¿sabes qué sería genial? **Que no necesites abrir la terminal para usarlo.**

Podemos empaquetarlo todo en un solo archivo ejecutable (como un `.exe` o un binario de Linux) que puedas poner en tu escritorio y hacer doble clic.

¿Te gustaría que te enseñe a compilarlo con **PyInstaller**? (Es solo un comando).
```
