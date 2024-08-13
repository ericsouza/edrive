import struct

from processor import enqueue_image


def handle_client(connection):
    try:
        # Recebe o tamanho do nome do arquivo
        raw_msglen = connection.recv(4)
        if not raw_msglen:
            return
        msglen = struct.unpack(">I", raw_msglen)[0]

        # Recebe o nome do arquivo
        filename = connection.recv(msglen).decode().strip()

        # Abre um arquivo para escrita
        with open(f"files/{filename}", "wb") as f:
            while True:
                data = connection.recv(8192)  # Lê em blocos maiores
                if not data:
                    break
                f.write(data)

        print(f"Imagem salva como {filename}")

        # Envia o nome do arquivo para a fila
        enqueue_image(filename)

    # except Exception as e:
    #     print(f"Erro ao salvar o arquivo: {e}")

    finally:
        connection.close()
