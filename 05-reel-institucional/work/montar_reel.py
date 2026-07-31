"""Monta o reel institucional a partir dos brutos, com corte de silêncio,
tratamento de áudio/cor, transições suaves e abertura/fechamento de marca.
"""
import subprocess
from pathlib import Path

FFMPEG = (
    r"C:\Users\prosy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)
SRC = Path(r"C:\Users\prosy\Downloads\videos Leticia")
WORK = Path(r"C:\tmp\videos-reels\05-reel-institucional\work")
OUT_FINAL = Path(r"C:\tmp\videos-reels\05-reel-institucional\reel_v1.mp4")

# (arquivo, inicio, fim) em segundos - cortando silencio de abertura/fechamento
CLIPES = [
    ("1.mp4", 1.20, 6.35),
    ("2.mp4", 0.60, 6.30),
    ("3.mp4", 0.70, 5.30),
    ("4.mp4", 1.70, 7.05),
    ("5.mp4", 1.00, 9.85),
    ("6.mp4", 0.00, 7.20),
    ("7.mp4", 1.15, 5.55),
]

XFADE = 0.35  # transicao suave e sutil, em segundos
INTRO_DUR = 1.6
OUTRO_DUR = 2.2

# eq leve: um pouco mais de contraste e saturacao, tom levemente mais quente
VIDEO_FILTER = "scale=1080:1920,eq=contrast=1.06:saturation=1.08:brightness=0.01"
# audio: corta grave abaixo de 90Hz, remove ruido de fundo, normaliza volume
AUDIO_FILTER = "highpass=f=90,afftdn=nr=12:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11"


def processar_clipe(nome: str, inicio: float, fim: float, indice: int) -> Path:
    origem = SRC / nome
    destino = WORK / f"proc_{indice}.mp4"
    duracao = fim - inicio
    cmd = [
        FFMPEG, "-y",
        "-ss", str(inicio), "-i", str(origem), "-t", str(duracao),
        "-vf", VIDEO_FILTER,
        "-af", AUDIO_FILTER,
        "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(destino),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return destino


def imagem_para_clipe(imagem: Path, duracao: float, destino: Path) -> Path:
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", str(imagem),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", str(duracao),
        "-vf", "scale=1080:1920",
        "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(destino),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return destino


def concatenar_com_transicoes(clipes: list[Path], durs: list[float]) -> None:
    inputs = []
    for c in clipes:
        inputs += ["-i", str(c)]

    n = len(clipes)
    filtro = []
    acumulado = durs[0]
    v_prev, a_prev = "0:v", "0:a"

    for i in range(1, n):
        offset = acumulado - XFADE
        v_out = f"v{i}"
        a_out = f"a{i}"
        filtro.append(
            f"[{v_prev}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={offset:.3f}[{v_out}]"
        )
        filtro.append(
            f"[{a_prev}][{i}:a]acrossfade=d={XFADE}[{a_out}]"
        )
        v_prev, a_prev = v_out, a_out
        acumulado += durs[i] - XFADE

    filtro_str = ";".join(filtro)
    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filtro_str,
        "-map", f"[{v_prev}]", "-map", f"[{a_prev}]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(OUT_FINAL),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)

    intro_clip = imagem_para_clipe(WORK / "intro.png", INTRO_DUR, WORK / "intro_clip.mp4")
    outro_clip = imagem_para_clipe(WORK / "outro.png", OUTRO_DUR, WORK / "outro_clip.mp4")

    processados = [intro_clip]
    duracoes = [INTRO_DUR]
    for i, (nome, ini, fim) in enumerate(CLIPES, start=1):
        p = processar_clipe(nome, ini, fim, i)
        processados.append(p)
        duracoes.append(fim - ini)
        print(f"processado {nome}: {fim - ini:.2f}s")

    processados.append(outro_clip)
    duracoes.append(OUTRO_DUR)

    concatenar_com_transicoes(processados, duracoes)
    print("Reel final em", OUT_FINAL)


if __name__ == "__main__":
    main()
