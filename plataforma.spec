# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: gera dist/plataforma.exe, um arquivo só, que abre com janela e sem console.
# Para gerar: pyinstaller plataforma.spec
from pathlib import Path

SRC = Path(SPECPATH) / "src"

# Todo .sql de src/plataforma vai junto, no mesmo caminho dentro do pacote. Assim o
# banco.PASTA_MIGRACOES encontra as migrações também dentro do .exe, e uma migração
# nova entra sem mexer neste arquivo.
migracoes = [
    (str(sql), str(sql.parent.relative_to(SRC)))
    for sql in (SRC / "plataforma").rglob("*.sql")
]

a = Analysis(
    [str(SRC / "plataforma" / "__main__.py")],
    pathex=[str(SRC)],
    datas=migracoes,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="plataforma",
    console=False,  # app de janela: não abre o prompt de comando junto
    upx=False,  # o UPX às vezes quebra DLLs do Qt e aumenta os alarmes falsos de antivírus
)
