# -*- coding: utf-8 -*-
"""
Orquestrador do video de apresentacao do PIM II - Sabor & Cia Bistro.

Etapas:
  1. Compila e roda o simulador em C (tcc) com uma sessao roteirizada,
     montando um transcript com as entradas digitadas interleaved.
  2. Gera a narracao de cada segmento com edge-tts (voz neural pt-BR),
     coletando os tempos por palavra para legendas sincronizadas.
     (fallback: voz offline Microsoft Maria via SAPI)
  3. Renderiza os slides (slides.py / Pillow).
  4. Monta um clipe de video por segmento (imagem + audio) com ffmpeg.
  5. Constroi um SRT global com offset acumulado.
  6. Concatena os clipes e queima as legendas -> MP4 final.

Uso:  python apresentacao/build.py
"""
import os
import sys
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
DIAGRAMAS = os.path.join(PROJ, "diagramas")
SRC_C = os.path.join(PROJ, "src", "simulacao_cardapio.c")
BUILD = os.path.join(HERE, "build")
DEMO_DIR = os.path.join(HERE, "demo")
DEMO_INPUT = os.path.join(DEMO_DIR, "demo_input.txt")
OUT_MP4 = os.path.join(HERE, "PIM_II_Sabor_e_Cia_apresentacao.mp4")

sys.path.insert(0, HERE)
import roteiro  # noqa: E402
import slides   # noqa: E402

BANNER = "===== SABOR & CIA - CARDAPIO DIGITAL ====="

# Prompt -> input digitado, na ordem exata da sessao (ver demo_input.txt)
PROMPTS = [
    ("Opcao: ", "1"),
    ("Escolha a filial: ", "1"),
    ("Filtrar por alergeno (enter para ver tudo): ", ""),
    ("Opcao: ", "1"),
    ("Escolha a filial: ", "1"),
    ("Filtrar por alergeno (enter para ver tudo): ", "Leite"),
    ("Opcao: ", "2"),
    ("Login: ", "itaim"),
    ("Senha: ", "1234"),
    ("Opcao: ", "2"),
    ("ID do produto (0 para voltar): ", "2"),
    ("1 - Ativar 2 - Desativar: ", "2"),
    ("Opcao: ", "1"),
    ("Opcao: ", "0"),
    ("Opcao: ", "2"),
    ("Login: ", "admin"),
    ("Senha: ", "admin123"),
    ("Opcao: ", "2"),
    ("Opcao: ", "3"),
    ("Opcao: ", "4"),
    ("Opcao: ", "0"),
    ("Opcao: ", "0"),
]

TCC_CANDIDATES = [
    r"C:\Users\Vitor Faustino\tools\tcc\tcc.exe",
    r"C:\Users\Vitor Faustino\tools\tcc\tcc",
    "tcc",
]


def run(cmd, **kw):
    print("  $", cmd if isinstance(cmd, str) else " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kw)


def ffprobe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


# ---------------------------------------------------------------- demo em C
def build_demo_parts():
    tcc = next((c for c in TCC_CANDIDATES if os.path.exists(c)), TCC_CANDIDATES[-1])
    run_dir = os.path.join(BUILD, "demo_run")
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    sim = os.path.join(run_dir, "sim.exe")

    print("[demo] compilando com tcc:", tcc)
    run([tcc, "-o", sim, SRC_C])

    with open(DEMO_INPUT, "r", encoding="utf-8") as f:
        entrada = f.read()
    print("[demo] executando sessao roteirizada")
    proc = subprocess.run([sim], input=entrada, cwd=run_dir,
                          capture_output=True, text=True, timeout=30,
                          encoding="utf-8", errors="replace")
    raw = proc.stdout.replace("\r\n", "\n")

    # interleave das entradas digitadas logo apos cada prompt
    pieces, cursor = [], 0
    for sub, tok in PROMPTS:
        i = raw.find(sub, cursor)
        if i == -1:
            break
        end = i + len(sub)
        pieces.append(raw[cursor:end])
        nextch = raw[end] if end < len(raw) else ""
        piece = tok + ("" if nextch == "\n" else "\n")
        pieces.append(piece)
        cursor = end
    pieces.append(raw[cursor:])
    transcript = "".join(pieces)

    with open(os.path.join(BUILD, "demo_output.txt"), "w", encoding="utf-8") as f:
        f.write(transcript)

    # divide em 3 partes pelas ocorrencias do banner do menu principal
    idx, start = [], 0
    while True:
        j = transcript.find(BANNER, start)
        if j == -1:
            break
        idx.append(j)
        start = j + len(BANNER)

    header = "C:\\SaborCia> sim.exe\n"
    if len(idx) >= 4:
        p0 = transcript[idx[0]:idx[2]]
        p1 = transcript[idx[2]:idx[3]]
        p2 = transcript[idx[3]:]
    else:  # fallback: 3 fatias aproximadas
        n = len(transcript)
        p0, p1, p2 = transcript[:n // 3], transcript[n // 3:2 * n // 3], transcript[2 * n // 3:]

    def tidy(s):
        return s.strip("\n")

    return [header + tidy(p0), tidy(p1), tidy(p2)]


# ---------------------------------------------------------------- narracao
def _srt_time(t):
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def narrate_edge(text, mp3_path):
    """Gera mp3 e devolve lista de (inicio_s, fim_s, palavra). Lanca excecao se falhar."""
    import asyncio
    import edge_tts

    words = []

    async def go():
        comm = edge_tts.Communicate(text, roteiro.VOZ, boundary="WordBoundary")
        with open(mp3_path, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    start = ch["offset"] / 1e7
                    dur = ch["duration"] / 1e7
                    words.append((start, start + dur, ch["text"]))

    asyncio.run(go())
    if os.path.getsize(mp3_path) == 0:
        raise RuntimeError("edge-tts retornou audio vazio")
    return words


def narrate_sapi(text, mp3_path):
    """Fallback offline (Microsoft Maria). Sem timing por palavra."""
    wav = mp3_path[:-4] + ".wav"
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "try { $s.SelectVoice('Microsoft Maria Desktop') } catch {}; "
        f"$s.SetOutputToWaveFile([string]@'\n{wav}\n'@); "
        f"$s.Speak([string]@'\n{text}\n'@); $s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, mp3_path])
    os.remove(wav)
    return None  # sem timings -> subs distribuidas depois


def group_cues(words, clip_start):
    """Agrupa palavras em legendas curtas. Devolve lista de (ini, fim, texto)."""
    cues = []
    buf, bstart, bend = [], None, None
    for (s, e, w) in words:
        if bstart is None:
            bstart = s
        buf.append(w)
        bend = e
        txt = " ".join(buf)
        flush = (len(buf) >= 8 or len(txt) >= 45
                 or w.endswith((".", "!", "?", ":", ";")))
        if flush:
            cues.append((clip_start + bstart, clip_start + bend, txt))
            buf, bstart, bend = [], None, None
    if buf:
        cues.append((clip_start + bstart, clip_start + bend, " ".join(buf)))
    return cues


def naive_cues(text, clip_start, dur):
    """Legendas distribuidas por tamanho quando nao ha timing (fallback SAPI)."""
    import re
    chunks, cur = [], ""
    for tok in text.split():
        cur = (cur + " " + tok).strip()
        if len(cur) >= 45 or tok.endswith((".", "!", "?")):
            chunks.append(cur)
            cur = ""
    if cur:
        chunks.append(cur)
    total = sum(len(c) for c in chunks) or 1
    cues, t = [], 0.0
    for c in chunks:
        d = dur * len(c) / total
        cues.append((clip_start + t, clip_start + t + d, c))
        t += d
    return cues


# ---------------------------------------------------------------- pipeline
def main():
    os.makedirs(BUILD, exist_ok=True)
    segs = roteiro.SEGMENTOS
    total = len(segs)

    print("== 1/6  demo em C ==")
    demo_parts = build_demo_parts()

    print("== 2/6  narracao (edge-tts) ==")
    fonts = slides.load_fonts()
    seg_words = {}   # id -> words ou None
    for k, seg in enumerate(segs, 1):
        mp3 = os.path.join(BUILD, f"seg_{k:02d}.mp3")
        print(f"[tts {k:02d}/{total}] {seg['id']}")
        try:
            seg_words[seg["id"]] = narrate_edge(seg["narracao"], mp3)
        except Exception as ex:  # noqa: BLE001
            print("   edge-tts falhou, usando SAPI:", ex)
            narrate_sapi(seg["narracao"], mp3)
            seg_words[seg["id"]] = None

    print("== 3/6  slides ==")
    seg_pages = {}
    for k, seg in enumerate(segs, 1):
        base = os.path.join(BUILD, f"slide_{k:02d}")
        seg_pages[seg["id"]] = slides.render_segment(seg, k, total, base,
                                                     DIAGRAMAS, demo_parts, fonts)

    print("== 4/6  clipes por segmento ==")
    clips = []
    for k, seg in enumerate(segs, 1):
        mp3 = os.path.join(BUILD, f"seg_{k:02d}.mp3")
        clip = os.path.join(BUILD, f"clip_{k:02d}.mp4")
        pages = seg_pages[seg["id"]]
        adur = ffprobe_dur(mp3)
        per = adur / len(pages)
        # arquivo de concat de imagens com duracao por pagina
        pfile = os.path.join(BUILD, f"pages_{k:02d}.txt")
        with open(pfile, "w", encoding="utf-8") as f:
            for pg in pages:
                f.write(f"file '{os.path.basename(pg)}'\n")
                f.write(f"duration {per:.3f}\n")
            f.write(f"file '{os.path.basename(pages[-1])}'\n")  # ultimo repetido (quirk concat)
        run(["ffmpeg", "-y", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", os.path.basename(pfile),
             "-i", os.path.basename(mp3),
             "-c:v", "libx264", "-tune", "stillimage", "-r", "30",
             "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
             "-fps_mode", "cfr", "-shortest", os.path.basename(clip)], cwd=BUILD)
        clips.append((seg, clip, mp3))

    print("== 5/6  legendas (SRT global) ==")
    all_cues, t0 = [], 0.0
    for seg, clip, mp3 in clips:
        dur = ffprobe_dur(clip)
        words = seg_words[seg["id"]]
        if words:
            all_cues.extend(group_cues(words, t0))
        else:
            all_cues.extend(naive_cues(seg["narracao"], t0, dur))
        t0 += dur
    srt = os.path.join(BUILD, "legendas.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, (ini, fim, txt) in enumerate(all_cues, 1):
            if fim <= ini:
                fim = ini + 0.4
            f.write(f"{i}\n{_srt_time(ini)} --> {_srt_time(fim)}\n{txt}\n\n")

    print("== 6/6  concat + queima de legenda ==")
    lista = os.path.join(BUILD, "lista.txt")
    with open(lista, "w", encoding="utf-8") as f:
        for _, clip, _ in clips:
            f.write(f"file '{os.path.basename(clip)}'\n")
    concat = os.path.join(BUILD, "sem_legenda.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", "lista.txt", "-c", "copy", "sem_legenda.mp4"], cwd=BUILD)

    style = ("FontName=Segoe UI,FontSize=22,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H90000000,BorderStyle=3,Outline=1,Shadow=0,"
             "Alignment=2,MarginV=46")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", "sem_legenda.mp4",
         "-vf", f"subtitles=legendas.srt:force_style='{style}'",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy",
         OUT_MP4], cwd=BUILD)

    dur = ffprobe_dur(OUT_MP4)
    print(f"\nOK -> {OUT_MP4}")
    print(f"Duracao: {int(dur // 60)}min {int(dur % 60)}s  |  {total} segmentos")


if __name__ == "__main__":
    main()
