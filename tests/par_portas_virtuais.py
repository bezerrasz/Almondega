"""
Cria um par de portas seriais virtuais interligadas (Linux/macOS), equivalente a
`socat -d -d pty,raw,echo=0 pty,raw,echo=0`. No Windows use o com0com.

    python tests/par_portas_virtuais.py
    -> imprime dois caminhos /dev/pts/X; um vai para o app, o outro para o simulador.

Também pode ser importado pelos testes: `abrir_par()` devolve (caminho_a, caminho_b, parar).
"""
import os
import select
import threading
import time
import tty


def abrir_par():
    m1, s1 = os.openpty()
    m2, s2 = os.openpty()
    for fd in (s1, s2):
        tty.setraw(fd)
    a, b = os.ttyname(s1), os.ttyname(s2)
    parar = threading.Event()

    def relay():
        while not parar.is_set():
            prontos, _, _ = select.select([m1, m2], [], [], 0.1)
            for fd in prontos:
                try:
                    dados = os.read(fd, 4096)
                except OSError:
                    continue
                destino = m2 if fd == m1 else m1
                try:
                    os.write(destino, dados)
                except OSError:
                    pass

    threading.Thread(target=relay, daemon=True).start()
    # mantém os escravos abertos para o par não ser destruído
    return a, b, parar


if __name__ == "__main__":
    a, b, parar = abrir_par()
    print(f"Porta do APP:        {a}")
    print(f"Porta do SIMULADOR:  {b}")
    print("Ctrl+C para encerrar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        parar.set()
