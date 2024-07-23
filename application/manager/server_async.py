import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'Conectado por {addr}')

    while True:
        data = await reader.read(1024)
        if not data:
            break
        print(f'Recebido {data.decode()} de {addr}')
        writer.write(data)
        await writer.drain()

    print(f'Conexão fechada por {addr}')
    writer.close()
    await writer.wait_closed()

async def periodic_print():
    while True:
        await asyncio.sleep(5)
        print("executando")

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 33007)
    addr = server.sockets[0].getsockname()
    print(f'Servidor escutando em {addr}')

    # Inicia a tarefa de impressão periódica
    asyncio.create_task(periodic_print())

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
