fluxo feliz de backup de imagem

manager -> [x] controla tudo
        -> [x] recebe imagem, salva local e dispara msg para distribuir entre os workers
        -> [x] ele mesmo recebe a mensagem para processar
        -> [x] elege o primario e envia
        -> [x] pós salvar no primario elege secundario e envia
        -> [x] salvando no primario e secundario com sucesso é feito:
            -> [x] salvar na lista de objetos da rede e de cada worker utilizado
            -> [x] apaga arquivo do manager
        -> [ ] dispara métricas (sucesso, falha etc). Isso inclui salvar na tabela de object count, disk usage

worker  -> [x] recebe imagem
        -> [x] salva local

worker saiu da rede, precisamos rebalancear as imagens:

Rebalancamento: processo de encontrar um novo worker para as imagens salvar em um worker que saiu da rede

manager -> [x] percebe que o nó saiu
        -> [x] busca objetos que aquele nó possuia
        -> [x] elege um novo primario ou secundario para o objeto
        -> [x] envia comando para o worker que possui a imagem e ainda está de pé, passando host do novo worker que deve receber a imagem
        -> [ ] se falhar pq o worker elegido não conseguiu, tenta-se outro worker
        -> [x] ao dar sucesso, atualiza a tabela de objetos
        -> [ ] dispara todas as métricas


worker entrou na rede com imagens (ou seja, um worker que caiu e voltou)

#### Abordagem 1. 

1. Worker apaga todas as imagens que possuia nele por confiar que o sistema fez o rebalanceamento com sucesso e sem perda de objetos. Problema: E se não foi feito com sucesso? corremos o risco de ter apenas em um worker ou pior, perdido em todos os nós. Pro primeiro cenário poderiamos ter um processo que sai varrendo todos os objetos e vendo se estão em ao menos 2 nós, mas é uma operação custosa e complexa e cria um desbalanceamento na distribuição de arquivos na rede (mas isso nao é necessariamente um problema se o sistema for inteligente de ir alocando mais imagens no worker vazio)

#### Abordagem 2.

Quando worker entra na rede, ele envia pro manager todos os objetos que possui, desse modo o manager pode apagar da maquina que substitiu enquanto o worker estava fora e atualizar a tabela de objetos. Eu acho que é o ideal por garantir que o objeto não será perdido para sempre, mesmo que os servidores primario e secundario caiam juntos, basta que alguem vá em alguma dessas máquinas e recupere o SSD/HDD.

Entrada do worker na rede usando essa abordagem:

1. Ele mapeia todos os objetos que possui
2. Se conecta ao manager passando a lista de objetos
3. Se nao encontrar o manager, tenta por mais X tempos. Se ainda sim não subir, ele morre por nao achar manager na rede.
4. Ao conectar com sucesso ao manager, este irá realizar as seguintes ações
    1. Atualizar lista de nodes disponiveis
    2. Rebaleancer os arquivos: apagando em workers antigos aqueles objetos que o novo node diz possuir
    3. atualizar tabela de objetos


#### Opção escolhida

Para esse projeto foi escolhida a **abordagem 1** por ser mais simples dado o tempo curto para implementar o projeto. Mas, o projeto facilmente pode ser evoluido para usar a **abordagem 2**
