"""
╔══════════════════════════════════════════════════════════════╗
║           PLAYBLAST STAMPER PRO  — v1.0                      ║
║           César · Underground Garage Pipeline                ║
║                                                              ║
║  Genera un playblast .mp4 con barra inferior que muestra:    ║
║    · Nombre del shot / escena                                ║
║    · Frame actual (grande)                                   ║
║    · Cámara activa                                           ║
║    · Fecha y hora                                            ║
║                                                              ║
║  Cómo usar:                                                  ║
║    1. Abre Maya Script Editor (Python)                       ║
║    2. Copia y pega este script completo                      ║
║    3. Ejecuta — aparece la ventana UI                        ║
╚══════════════════════════════════════════════════════════════╝
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import subprocess
import tempfile
import shutil
from datetime import datetime

# ── UI principal ──────────────────────────────────────────────────────────────

def open_stamper_ui():
    win_id = "playblastStamperWin"
    if cmds.window(win_id, exists=True):
        cmds.deleteUI(win_id)

    cmds.window(win_id, title="Playblast Stamper Pro", widthHeight=(400, 320), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnOffset=("both", 16))

    cmds.separator(height=12, style="none")
    cmds.text(label="PLAYBLAST STAMPER PRO", font="boldLabelFont", align="center")
    cmds.text(label="v1.0 — César Pipeline", font="smallPlainLabelFont", align="center")
    cmds.separator(height=10)

    # ── Shot name ──
    cmds.text(label="Nombre del Shot  (deja vacío = usa nombre de escena)", align="left")
    shot_field = cmds.textField(placeholderText="ej: SHOT_010  o  UG_Garage_v03")

    # ── Output path ──
    cmds.text(label="Carpeta de salida", align="left")
    row = cmds.rowLayout(numberOfColumns=2, columnWidth2=(280, 80), adjustableColumn=1)
    out_field = cmds.textField(placeholderText="C:/Users/cesar/Desktop/playblasts")
    cmds.button(label="Browse", command=lambda *_: _browse(out_field))
    cmds.setParent("..")

    # ── Resolución ──
    cmds.text(label="Resolución", align="left")
    res_menu = cmds.optionMenu()
    for res in ["1280 x 720  (HD)", "1920 x 1080  (Full HD)", "960 x 540  (Half HD)"]:
        cmds.menuItem(label=res)

    # ── Frame range ──
    cmds.rowLayout(numberOfColumns=4, columnWidth4=(80, 60, 60, 60))
    cmds.text(label="Frame range:")
    start_field = cmds.intField(value=int(cmds.playbackOptions(q=True, min=True)))
    cmds.text(label=" — ")
    end_field   = cmds.intField(value=int(cmds.playbackOptions(q=True, max=True)))
    cmds.setParent("..")

    cmds.separator(height=6)

    # ── Botón principal ──
    cmds.button(
        label="▶  GENERAR PLAYBLAST",
        height=40,
        backgroundColor=(0.18, 0.45, 0.18),
        command=lambda *_: run_stamper(
            shot_field, out_field, res_menu, start_field, end_field
        )
    )
    cmds.separator(height=8, style="none")
    cmds.showWindow(win_id)


def _browse(field):
    folder = cmds.fileDialog2(fileMode=3, caption="Selecciona carpeta de salida")
    if folder:
        cmds.textField(field, edit=True, text=folder[0])


# ── Core ──────────────────────────────────────────────────────────────────────

def run_stamper(shot_field, out_field, res_menu, start_field, end_field):
    """Orquesta todo el proceso."""

    # — Recoger parámetros desde la UI —
    shot_name = cmds.textField(shot_field, q=True, text=True).strip()
    if not shot_name:
        scene_path = cmds.file(q=True, sceneName=True)
        shot_name  = os.path.splitext(os.path.basename(scene_path))[0] if scene_path else "untitled"

    out_dir = cmds.textField(out_field, q=True, text=True).strip()
    if not out_dir:
        out_dir = os.path.join(tempfile.gettempdir(), "playblasts")
    os.makedirs(out_dir, exist_ok=True)

    res_label = cmds.optionMenu(res_menu, q=True, value=True)
    w, h = _parse_res(res_label)

    start = cmds.intField(start_field, q=True, value=True)
    end   = cmds.intField(end_field,   q=True, value=True)

    # — Cámara activa —
    active_cam = _get_active_camera()

    # — Carpeta temporal para frames raw —
    tmp_dir = tempfile.mkdtemp(prefix="pb_stamp_")

    try:
        cmds.progressWindow(title="Playblast Stamper", progress=0, status="Generando playblast raw...", isInterruptable=True)

        # 1 · Playblast raw (sin stamp) como secuencia de imágenes
        raw_path = os.path.join(tmp_dir, "raw").replace("\\", "/")
        _do_playblast_raw(raw_path, w, h, start, end)

        # 2 · Stamp cada frame con Pillow
        cmds.progressWindow(edit=True, progress=40, status="Aplicando stamps...")
        stamped_dir = os.path.join(tmp_dir, "stamped")
        os.makedirs(stamped_dir, exist_ok=True)
        _stamp_frames(tmp_dir, stamped_dir, shot_name, active_cam, start, w, h)

        # 3 · Ensamblar mp4 con ffmpeg
        cmds.progressWindow(edit=True, progress=75, status="Ensamblando .mp4...")
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_mp4 = os.path.join(out_dir, f"{shot_name}_{timestamp}.mp4")
        fps        = _get_fps()
        _assemble_mp4(stamped_dir, output_mp4, fps)

        cmds.progressWindow(edit=True, progress=100, status="¡Listo!")

    finally:
        cmds.progressWindow(endProgress=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # — Resultado —
    result = cmds.confirmDialog(
        title="Playblast Stamper",
        message=f"✅  Playblast generado:\n\n{output_mp4}",
        button=["Abrir carpeta", "Cerrar"],
        defaultButton="Abrir carpeta"
    )
    if result == "Abrir carpeta":
        _open_folder(out_dir)


# ── Playblast raw ─────────────────────────────────────────────────────────────

def _do_playblast_raw(out_prefix, w, h, start, end):
    """
    Ejecuta el playblast de Maya y guarda como secuencia de imágenes .png.
    out_prefix: ruta sin extensión, Maya añade el número de frame.
    """
    cmds.playblast(
        filename      = out_prefix,
        format        = "image",
        compression   = "png",
        width         = w,
        height        = h,
        startTime     = start,
        endTime       = end,
        sequenceTime  = 0,
        clearCache    = True,
        viewer        = False,
        showOrnaments = False,   # sin el HUD de Maya — nosotros lo dibujamos
        percent       = 100,
        forceOverwrite= True,
    )


# ── Stamp de frames ───────────────────────────────────────────────────────────

def _stamp_frames(src_dir, dst_dir, shot_name, cam_name, start_frame, w, h):
    """Lee cada frame PNG, dibuja la barra inferior y guarda en dst_dir."""
    from PIL import Image, ImageDraw, ImageFont

    # Buscar archivos generados por Maya (raw.####.png o raw.png.####.png)
    raw_files = sorted([
        f for f in os.listdir(src_dir)
        if f.startswith("raw") and f.endswith(".png")
    ])

    if not raw_files:
        cmds.warning("PlayblastStamper: no se encontraron frames PNG en " + src_dir)
        return

    bar_h    = max(32, h // 18)   # altura de la barra proporcional a resolución
    font_big = _get_font(bar_h - 6)
    font_sm  = _get_font(max(10, bar_h // 2 - 2))
    bar_color = (10, 10, 10, 200)  # negro semitransparente

    for idx, fname in enumerate(raw_files):
        frame_num = start_frame + idx
        src_path  = os.path.join(src_dir, fname)
        dst_path  = os.path.join(dst_dir, f"frame_{idx:04d}.png")

        img  = Image.open(src_path).convert("RGBA")
        draw = ImageDraw.Draw(img)

        # — Barra inferior —
        bar_y = h - bar_h
        draw.rectangle([0, bar_y, w, h], fill=bar_color)

        # — Frame number (grande, centrado) —
        frame_str = f"{frame_num:04d}"
        fw, fh    = _textsize(draw, frame_str, font_big)
        draw.text(((w - fw) / 2, bar_y + (bar_h - fh) / 2), frame_str, font=font_big, fill=(255, 220, 60))

        # — Shot name (izquierda) —
        draw.text((10, bar_y + (bar_h - fh) / 2 + 2), shot_name.upper(), font=font_sm, fill=(200, 200, 200))

        # — Cámara | Fecha (derecha) —
        now_str  = datetime.now().strftime("%Y-%m-%d  %H:%M")
        right_str = f"{cam_name}  |  {now_str}"
        rw, _    = _textsize(draw, right_str, font_sm)
        draw.text((w - rw - 10, bar_y + (bar_h - fh) / 2 + 2), right_str, font=font_sm, fill=(160, 160, 160))

        img.convert("RGB").save(dst_path)


def _get_font(size):
    """Intenta cargar una fuente del sistema; fallback a default de Pillow."""
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _textsize(draw, text, font):
    """Compatibilidad Pillow antiguo/nuevo para medir texto."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return draw.textsize(text, font=font)


# ── Ensamblado mp4 ────────────────────────────────────────────────────────────

def _get_maya_audio():
    """Devuelve (ruta_audio, offset_frames) del audio cargado en el timeline. None si no hay."""
    audio_nodes = cmds.ls(type="audio")
    if not audio_nodes:
        return None, 0
    node     = audio_nodes[0]
    filepath = cmds.getAttr(node + ".filename")
    offset   = cmds.getAttr(node + ".offset")
    return (filepath if filepath and os.path.exists(filepath) else None), offset


def _assemble_mp4(frames_dir, output_path, fps):
    """Ensambla frames en mp4. Si hay audio en el timeline de Maya lo mezcla automaticamente."""
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        cmds.warning("PlayblastStamper: ffmpeg no encontrado. Frames en: " + frames_dir)
        return

    audio_path, audio_offset = _get_maya_audio()
    input_pattern = os.path.join(frames_dir, "frame_%04d.png").replace("\\", "/")

    cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i", input_pattern]

    if audio_path:
        offset_sec = audio_offset / fps
        if offset_sec > 0:
            cmd += ["-ss", str(offset_sec)]
        cmd += ["-i", audio_path,
                "-map", "0:v", "-map", "1:a",
                "-shortest", "-acodec", "aac", "-ab", "192k"]

    cmd += ["-vcodec", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            output_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        cmds.warning("PlayblastStamper ffmpeg error: " + result.stderr[-500:])
    else:
        label = ("con audio: " + os.path.basename(audio_path)) if audio_path else "sin audio en timeline"
        print("PlayblastStamper OK - " + label)


def _find_ffmpeg():
    """Busca ffmpeg en PATH y en ubicaciones comunes de Maya."""
    # Primero en PATH
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    # Ubicaciones donde Maya 2024+ incluye ffmpeg
    candidates = [
        "C:/Program Files/Autodesk/Maya2026/bin/ffmpeg.exe",
        "C:/Program Files/Autodesk/Maya2025/bin/ffmpeg.exe",
        "C:/Program Files/Autodesk/Maya2024/bin/ffmpeg.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_fps():
    """Convierte el nombre de tiempo de Maya a FPS numérico."""
    fps_map = {
        "game": 15, "film": 24, "pal": 25, "ntsc": 30,
        "show": 48, "palf": 50, "ntscf": 60,
        "2fps": 2, "3fps": 3, "4fps": 4, "5fps": 5, "6fps": 6,
        "8fps": 8, "10fps": 10, "12fps": 12, "16fps": 16,
        "20fps": 20, "23.976fps": 24, "24fps": 24, "25fps": 25,
        "29.97fps": 30, "30fps": 30, "40fps": 40, "47.952fps": 48,
        "48fps": 48, "50fps": 50, "59.94fps": 60, "60fps": 60,
        "75fps": 75, "80fps": 80, "100fps": 100, "120fps": 120,
    }
    unit = cmds.currentUnit(q=True, time=True)
    return fps_map.get(unit, 24)


def _get_active_camera():
    """Devuelve el nombre de la cámara del panel activo."""
    try:
        panel = cmds.getPanel(withFocus=True)
        cam   = cmds.modelPanel(panel, q=True, camera=True)
        return cam if cam else "persp"
    except Exception:
        return "persp"


def _parse_res(label):
    """'1280 x 720  (HD)' → (1280, 720)"""
    parts = label.split("x")
    w = int(parts[0].strip())
    h = int(parts[1].strip().split()[0])
    return w, h


def _open_folder(path):
    """Abre el explorador de archivos en la carpeta indicada."""
    import platform
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


# ── Entry point ───────────────────────────────────────────────────────────────
open_stamper_ui()
