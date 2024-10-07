# League of Legends Match Analyzer Version 1.0

Este projeto realiza a análise de partidas de League of Legends com base nos dados de invocadores (jogadores). Utilizando a API do jogo, é possível buscar informações detalhadas de partidas e realizar análises comparativas entre jogadores e seus oponentes.

## Funcionalidades

- Busca de informações sobre o invocador utilizando a TAG e o nick do invocador.
- Filtragem de partidas por tipo: normais, ranked ou de torneio.
- Geração de arquivos JSON com os dados das partidas.
- Análise comparativa entre o desempenho do jogador e seu oponente, considerando métricas como KDA, visão, CS e gold.

## Saída do Programa

- Há consideração de métricas diferentes para as **roles** próprias do jogo (TOP, MID, BOTTOM, SUPPORT e JUNGLE).
- No geral, as métricas são:

### Estatísticas Gerais

- **Número de partidas analisadas**: Exibe o total de partidas válidas usadas para calcular as médias.
- **Partidas vencidas**: Contagem de partidas vencidas pelo jogador(a).
- **KDA Médio (Kill/Death/Assist)**: Média de eliminações, mortes e assistências por partida.
- **Média de Kill Participation (KP)**: Percentual de participação do jogador(a) nos abates da equipe.
- **Média de CS (Creep Score)**: Quantidade média de tropas eliminadas por partida.
- **Média de Dano por Gold**: Relaciona o dano causado em relação ao ouro ganho.
- **Dano Percentual da Equipe**: Percentual de dano total do time que foi causado pelo jogador(a).
- **Média de Gold da Equipe**: Média de ouro ganho pelo time em cada partida.
- **Média de Score de Visão**: Ponto de visão acumulado por colocar wards ou destruir wards inimigas.
- **Média de Visão Comparada ao Oponente**: Diferença de visão entre o jogador(a) e o adversário.
- **Média de Visão por Minuto**: Média de wards colocadas e wards destruídas por minuto.
- **Diferenças de Gold, CS e Nível**: Diferença média de ouro, CS e nível do jogador(a) em relação ao oponente.
- **Média de Diferença de KDA**: Diferença do KDA do jogador(a) comparado ao KDA do oponente.


## Para rodar:

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
2. Instale as dependências necessárias:
    pip install -r requirements.txt
3. Rode "executavel_lol.py"



Esse **README.md** explica rapidamente as funcionalidades e os passos para rodar o projeto. 
