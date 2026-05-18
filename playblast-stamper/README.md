# 🎬 Maya Tools — César Animación Pipeline

> Scripts de Python para Maya 2024+ que automatizan tareas de producción de animación.  
> Desarrollados durante la producción de **"Underground Garage"** (cortometraje de animación 3D).

---

## 🛠 Scripts disponibles

### 1. Playblast Stamper Pro
Genera playblasts `.mp4` con barra inferior de información quemada en el video — sin perder el audio del timeline de Maya.

**Qué incluye la barra:**
- Nombre del shot / escena
- Frame counter grande (centrado)
- Cámara activa
- Fecha y hora

**Controles de visibilidad:**
Desde la UI puedes elegir qué mostrar antes de renderizar el playblast:
- Modo limpio (solo polígonos, sin controles ni rigs)
- Toggle individual: joints, locators, cámaras, luces, grid, etc.
- El viewport se restaura automáticamente al terminar

**Dependencias:**
- Maya 2024+ (Python 3)
- `Pillow` — `pip install Pillow --break-system-packages`
- `ffmpeg` — incluido en Maya 2024+ o descargable en [ffmpeg.org](https://ffmpeg.org)

**Uso:**
```python
# En el Script Editor de Maya (Python):
# 1. Pega el contenido de playblast_stamper.py
# 2. Ejecuta — aparece la ventana UI
```

![UI Preview](preview.png)

---

## 🚀 En desarrollo

| Script | Estado |
|---|---|
| Scene Health Checker | 🔜 Próximo |
| Video Reference Loader + Speed Control | 🔜 Próximo |
| Batch Material Assigner (rigs referenciados) | 🔜 Próximo |
| Maya → Unreal Engine FBX Exporter | 🔜 Próximo |
| Animation Curve Cleaner | 🔜 Próximo |

---

## ⚙️ Requisitos generales

- **Maya 2024 / 2025 / 2026**
- **Python 3** (incluido en Maya 2022+)
- **Arnold** (para scripts relacionados con shading)
- **ffmpeg** (para scripts de video)

---

## 👤 Autor

**César** — Animator & Technical Director  
Antofagasta, Chile  

> *Scripts desarrollados en producción real. Cada herramienta resuelve un problema concreto encontrado durante el desarrollo de proyectos de animación 3D.*

---

## 📄 Licencia

MIT — libre para usar y modificar. Si lo usas en tu pipeline, un crédito es bienvenido.
