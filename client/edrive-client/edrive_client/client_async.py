import asyncio

async def socket_client(message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 33007)

    print(f'Sending: {message}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(1024)
    print(f'Received: {data.decode()}')

    print('Closing the connection')
    writer.close()
    await writer.wait_closed()

async def main():
    messages = ['Hello, world!', 'How are you?', 'Goodbye!']
    
    for message in messages:
        await socket_client(message)
        await asyncio.sleep(1) 

if __name__ == '__main__':
    asyncio.run(main())
