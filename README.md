## eDrive

Projeto desenvolvido para disciplina de Sistemas Distribuidos


#### Regra para escolha do servidor primário e secundário

O gerenciador ordena os servidores baseado nos que tem menor uso de disco. Ou seja, pega os servidores com mais espaço livre disponível

#### Funcionamento

- Cliente chama o gerenciador;
- Gerenciador devolve o endereço dos servidores primário e secundário;
- Client envia imagem para o servidor primário;
- Servidor primário recebe a imagem e salva. Então envia a imagem para o servidor secundário;
- O banco de dados é atualizado com a lista de arquivos, quais arquivos estão em quais servidores e o total de disco usado por cada servidor;

#### Extras implementados

- Quando um worker "morre" o manager automaticamente detecta e começa a redistribuir as imagens daquele servidor em outros servidores;
- Interface gráfica para acompanhar os servidores e arquivos da rede


#### como subir?

A maneira mais simples é tendo docker instalado. Precisa ser uma versão mais recente que já possua o subcomando "compose" para usar o "docker-compose.yaml"

Com docker instalado, entre na pasta `application` e execute:
```bash
docker compose down && docker compose up --build
```

Aguarde subir. Em outro terminar, volte para a raíz do projeto e entre na pasta `client`. Nesse pasta existem algumas imagens para testar a aplicação.

Você poderá enviar 1 imagem:
```bash
python client.py caneca-cebolinha.jpg
```

Ou várias de uma vez (cada upload será feito por uma thread separada das demais):
```bash
python client.py caneca-cebolinha.jpg sonic.png firewatch.jpg
```

Para acessar a interface "admin" basta acessar http://localhost:5000/


### Github

Link: https://github.com/ericsouza/edrive

