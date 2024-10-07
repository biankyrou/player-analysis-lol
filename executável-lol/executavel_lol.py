import requests
import json
import os
import sys
import pandas as pd
from pandas import json_normalize
os.environ['RIOT_API_KEY'] = 'RGAPI-75a86f31-c500-49dc-9af4-769a65cabc7d'



def transform_nick_puuid(tag, nick):
    api_key = os.getenv('RIOT_API_KEY')
    url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{nick}/{tag}?api_key={api_key}'
    resposta = requests.get(url)
    dados = resposta.json()
    if 'puuid' in dados:
        return dados['puuid']
    else:
        print("Erro: Não foi possível encontrar o PUUID para o nick e tag fornecidos.")
        sys.exit(1)


def get_id_partidas(puuid, countMatch, typeMatch):
    api_key = os.getenv('RIOT_API_KEY')
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type={typeMatch}&start=0&count={countMatch}&api_key={api_key}'
    resposta = requests.get(url)
    idsPartidas = resposta.json()

    n_partidas_recentes = len(idsPartidas)
    if countMatch < n_partidas_recentes:
        print(f"Não há número de partidas recentes para serem analisadas. Tente: {n_partidas_recentes}")
    else:
        return idsPartidas


def salvar_json(dados, nome_arquivo, pasta):
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    caminho_completo = os.path.join(pasta, nome_arquivo)

    with open(caminho_completo, 'w') as arquivo_json:
        json.dump(dados, arquivo_json)

    print(f"Arquivo JSON '{nome_arquivo}' salvo com sucesso na pasta '{pasta}'!")


def check_json_values(data):
    errors = []

    def check_structure(d):
        if isinstance(d, dict):
            for key, value in d.items():
                if key is None:
                    errors.append("Chave encontrada sem valor.")
                if value is None:
                    errors.append(f"Valor corrompido encontrado para a chave: '{key}' (valor é None)")
                check_structure(value)  # Recursão para verificar dicionários aninhados
        elif isinstance(d, list):
            for item in d:
                check_structure(item)  # Verifica cada item na lista

    check_structure(data)
    
    return errors



def obter_detalhes_partida(id_partida):
    api_key = os.getenv('RIOT_API_KEY')
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{id_partida}?api_key={api_key}'
    resposta = requests.get(url)
    dados = resposta.json()
    return dados


def cria_dataset_partidas(pasta_json, chunk_size=10):
    dataframe_metadata = []
    dataframe_info = []

    arquivos_json = [arquivo for arquivo in os.listdir(pasta_json) if arquivo.endswith(".json")]

    for i in range(0, len(arquivos_json), chunk_size):
        chunk_files = arquivos_json[i:i + chunk_size]
        
        temp_metadata = []
        temp_info = []

        for arquivo_json in chunk_files:
            caminho_arquivo = os.path.join(pasta_json, arquivo_json)

            with open(caminho_arquivo, "r", encoding="utf-8") as file:
                data = json.load(file)

                # Verificação de valores corrompidos
                errors = check_json_values(data)
                if errors:
                    for error in errors:
                        print(error)  # Imprime erros encontrados

                metadata_df = pd.json_normalize(data['metadata'])
                info_df = pd.json_normalize(data['info'])

                temp_metadata.append(metadata_df)
                temp_info.append(info_df)

        df_chunk_metadata = pd.concat(temp_metadata, ignore_index=True)
        df_chunk_info = pd.concat(temp_info, ignore_index=True)

        dataframe_metadata.append(df_chunk_metadata)
        dataframe_info.append(df_chunk_info)

    df_concatenado_metadata = pd.concat(dataframe_metadata, ignore_index=True)
    df_concatenado_info = pd.concat(dataframe_info, ignore_index=True)

    return df_concatenado_info



def main():
  print('Olá, seja bem vindo/a')
  tag = input("Digite a TAG do invocador: ")
  gameName = input("Digite o nick do invocador: ")
  puuid = transform_nick_puuid(tag, gameName)

  while True:
    try:
        countMatch = int(input("Digite quantas partidas você deseja analisar: "))
        if countMatch > 0:
            break
        else:
            print("O número de partidas deve ser um valor positivo.")
    except ValueError:
        print("Entrada inválida! Por favor, insira um número inteiro positivo.")

  typeMatch = ""
  while True:
        try:
            optionTypeMatch = int(input("Deseja filtrar por partidas normais(1), partidas ranked(2) ou partidas de torneio (3)? "))
            if optionTypeMatch == 1:
                typeMatch = "normal"
                break
            elif optionTypeMatch == 2:
                typeMatch = "ranked"
                break
            elif optionTypeMatch == 3:
                typeMatch = "tourney"
                break
            else:
                print("Opção inválida! Por favor, escolha 1 (normal), 2 (ranked) ou 3 (tourney).")
        except ValueError:
            print("Entrada inválida! Por favor, insira um número inteiro (1, 2 ou 3).")

  ids_partidas = get_id_partidas(puuid, countMatch, typeMatch)

  op = input("Deseja criar um json com os dados das partidas? Sim(1) / Não(2) ")
  if op == "1":
    pasta = input("Digite o nome da pasta onde deseja salvar os arquivos: ")
    if ids_partidas:
        for id_partida in ids_partidas:
            dados_partida = obter_detalhes_partida(id_partida)
            if dados_partida:
                nome_arquivo_json = f'partida_{id_partida}.json'
                salvar_json(dados_partida, nome_arquivo_json, pasta)
    else:
        print("Não é possível criar o arquivo JSON porque os IDs das partidas não foram obtidos.")
        print("Possivelmente, não há partidas suficientes para serem analisadas")
        sys.exit(1)

    # normalizando datasets
    df_concatenado_info = cria_dataset_partidas(pasta)
    info_participants = df_concatenado_info['participants']
    info_participants_df = pd.json_normalize(info_participants)

    numero_de_partidas = len(info_participants_df)

    #basic
    kda_soma = 0
    cs_soma = 0
    kp_soma = 0
    dano_por_gold_soma = 0
    dano_percent_equipe_soma = 0
    gold_da_equipe_soma = 0
    score_vision_soma = 0
    visao_comparada_oponente_soma = 0
    visao_por_minuto_soma = 0

    #comparado ao oponente
    gold_diff_soma = 0
    cs_diff_soma = 0
    level_diff_soma = 0
    kda_diff_soma = 0

    # early game lane phase
    vantagem_grande_early_phase_soma =0 
    cs_early_game_soma = 0
    cs_early_game_compare_oponente_soma = 0
    laner_invade_jg_soma = 0

    # lane phase toda
    maxCs_comparado_com_oponente_soma = 0
    maxLevel_comparado_com_oponente_soma = 0
    vantagem_grande_lane_phase_soma = 0

    # early game jungle
    jungle_cs_before_10minutes_soma = 0
    jungler_kill_invade_early_soma = 0
    jg_ganks_kill_early_soma = 0

    # foco visão
    wards_colocadas_soma = 0
    wards_eliminadas_soma = 0
    control_wards_colocadas_soma = 0

    position_player_input = input("Qual posição você deseja filtrar? (1) TOP, (2) MID, (3) ADC/BOTTOM, (4) Jungler ou (5) Support. Se não deseja filtrar por nenhuma lane, digite (6): ")
    nome_player = gameName
    contagem_wins = 0
    numero_de_partidas_validas = 0

    for i in range(numero_de_partidas):
        primeira_partida_filtro = info_participants_df.iloc[i,:]
        primeira_partida = pd.json_normalize(primeira_partida_filtro)

        primeira_partida = primeira_partida.drop(columns=primeira_partida.filter(like='missions').columns)
        primeira_partida = primeira_partida.drop(columns=primeira_partida.filter(like='perks').columns)

        #----------
        # Lista de chaves que você deseja verificar
        chaves_para_verificar = [
            'challenges.kda',
            'challenges.killParticipation',
            'neutralMinionsKilled',
            'totalMinionsKilled',
            'totalDamageDealtToChampions',
            'goldEarned',
            'challenges.teamDamagePercentage',
            'visionScore',
            'challenges.visionScoreAdvantageLaneOpponent',
            'challenges.visionScorePerMinute',
            'challenges.earlyLaningPhaseGoldExpAdvantage',
            'challenges.laneMinionsFirst10Minutes',
            'challenges.getTakedownsInAllLanesEarlyJungleAsLaner',
            'challenges.maxCsAdvantageOnLaneOpponent',
            'challenges.maxLevelLeadLaneOpponent',
            'challenges.laningPhaseGoldExpAdvantage',
            'challenges.jungleCsBefore10Minutes',
            'challenges.junglerKillsEarlyJungle',
            'challenges.killsOnLanersEarlyJungleAsJungler',
            'wardsPlaced',
            'wardsKilled',
            'challenges.controlWardsPlaced'
        ]


        for chave in chaves_para_verificar:
            if chave not in primeira_partida.columns:  
                break  
        else:
            for index, name in enumerate(primeira_partida['summonerName']):
                if name == nome_player:
                    index_player = index
                    break
        
            dados_player = primeira_partida.iloc[[index_player]]
            position_player = dados_player['individualPosition'].values[0]

            index_opponent = None
            for index, (name, position) in enumerate(zip(primeira_partida['summonerName'], primeira_partida['individualPosition'])):
                if position == position_player and index != index_player:
                    index_opponent = index
                    break
            
            dados_oponente = primeira_partida.iloc[[index_opponent]]
            dados_player = primeira_partida.iloc[[index_player]]

            if index_player > 4:
                players_gold = primeira_partida.loc[5:9, ['goldEarned']]
                total_gold = players_gold['goldEarned'].sum()
            else:
                players_gold = primeira_partida.loc[0:4, ['goldEarned']]
                total_gold = players_gold['goldEarned'].sum()
            
            game_duration_minutes = dados_player['timePlayed'].values[0] / 60



            if position_player_input == '1':
                if position_player == 'TOP':
                    kda_soma += (dados_player['challenges.kda'].values[0])
                    kp_soma += (dados_player['challenges.killParticipation'].values[0] * 100)
                    cs_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) / game_duration_minutes)
                    dano_por_gold_soma += (dados_player['totalDamageDealtToChampions'].values[0] / dados_player['goldEarned'].values[0])
                    dano_percent_equipe_soma += (dados_player['challenges.teamDamagePercentage'].values[0] * 100)
                    gold_da_equipe_soma += ((dados_player['goldEarned'].values[0] / total_gold) * 100)
                    score_vision_soma += (dados_player['visionScore'].values[0])
                    visao_comparada_oponente_soma += (dados_player['challenges.visionScoreAdvantageLaneOpponent'].values[0])
                    visao_por_minuto_soma += (dados_player['challenges.visionScorePerMinute'].values[0])

                    gold_diff_soma += (dados_player['goldEarned'].iloc[0] - dados_oponente['goldEarned'].iloc[0])
                    cs_diff_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) - 
                                    (dados_oponente['neutralMinionsKilled'].values[0] + dados_oponente['totalMinionsKilled'].values[0]))
                    level_diff_soma += (dados_player['champLevel'].iloc[0] - dados_oponente['champLevel'].iloc[0])
                    kda_diff_soma += (dados_player['challenges.kda'].values[0] - dados_oponente['challenges.kda'].values[0])


                    # Early and Lane Phase para laners
                    vantagem_grande_early_phase_soma += (dados_player['challenges.earlyLaningPhaseGoldExpAdvantage'].values[0])
                    cs_early_game_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] / 10)
                    cs_early_game_compare_oponente_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] - 
                                                dados_oponente['challenges.laneMinionsFirst10Minutes'].values[0])
                    laner_invade_jg_soma += (dados_player['challenges.getTakedownsInAllLanesEarlyJungleAsLaner'].values[0])

                    maxCs_comparado_com_oponente_soma += (dados_player['challenges.maxCsAdvantageOnLaneOpponent'].values[0])
                    maxLevel_comparado_com_oponente_soma += (dados_player['challenges.maxLevelLeadLaneOpponent'].values[0])
                    vantagem_grande_lane_phase_soma += (dados_player['challenges.laningPhaseGoldExpAdvantage'].values[0])


                    if dados_player['win'].values[0] == True:
                        contagem_wins += 1
                        
                    numero_de_partidas_validas += 1

            elif position_player_input == '2':
                if position_player == 'MIDDLE':
                    kda_soma += (dados_player['challenges.kda'].values[0])
                    kp_soma += (dados_player['challenges.killParticipation'].values[0] * 100)
                    cs_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) / game_duration_minutes)
                    dano_por_gold_soma += (dados_player['totalDamageDealtToChampions'].values[0] / dados_player['goldEarned'].values[0])
                    dano_percent_equipe_soma += (dados_player['challenges.teamDamagePercentage'].values[0] * 100)
                    gold_da_equipe_soma += ((dados_player['goldEarned'].values[0] / total_gold) * 100)
                    score_vision_soma += (dados_player['visionScore'].values[0])
                    visao_comparada_oponente_soma += (dados_player['challenges.visionScoreAdvantageLaneOpponent'].values[0])
                    visao_por_minuto_soma += (dados_player['challenges.visionScorePerMinute'].values[0])

                    gold_diff_soma += (dados_player['goldEarned'].iloc[0] - dados_oponente['goldEarned'].iloc[0])
                    cs_diff_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) - 
                                    (dados_oponente['neutralMinionsKilled'].values[0] + dados_oponente['totalMinionsKilled'].values[0]))
                    level_diff_soma += (dados_player['champLevel'].iloc[0] - dados_oponente['champLevel'].iloc[0])
                    kda_diff_soma += (dados_player['challenges.kda'].values[0] - dados_oponente['challenges.kda'].values[0])


                    # Early and Lane Phase para laners
                    vantagem_grande_early_phase_soma += (dados_player['challenges.earlyLaningPhaseGoldExpAdvantage'].values[0])
                    cs_early_game_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] / 10)
                    cs_early_game_compare_oponente_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] - 
                                                dados_oponente['challenges.laneMinionsFirst10Minutes'].values[0])
                    laner_invade_jg_soma += (dados_player['challenges.getTakedownsInAllLanesEarlyJungleAsLaner'].values[0])

                    maxCs_comparado_com_oponente_soma += (dados_player['challenges.maxCsAdvantageOnLaneOpponent'].values[0])
                    maxLevel_comparado_com_oponente_soma += (dados_player['challenges.maxLevelLeadLaneOpponent'].values[0])
                    vantagem_grande_lane_phase_soma += (dados_player['challenges.laningPhaseGoldExpAdvantage'].values[0])


                    if dados_player['win'].values[0] == True:
                        contagem_wins += 1
                        
                    numero_de_partidas_validas += 1
            
            elif position_player_input == '3':
                if position_player == 'BOTTOM':
                    kda_soma += (dados_player['challenges.kda'].values[0])
                    kp_soma += (dados_player['challenges.killParticipation'].values[0] * 100)
                    cs_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) / game_duration_minutes)
                    dano_por_gold_soma += (dados_player['totalDamageDealtToChampions'].values[0] / dados_player['goldEarned'].values[0])
                    dano_percent_equipe_soma += (dados_player['challenges.teamDamagePercentage'].values[0] * 100)
                    gold_da_equipe_soma += ((dados_player['goldEarned'].values[0] / total_gold) * 100)
                    score_vision_soma += (dados_player['visionScore'].values[0])
                    visao_comparada_oponente_soma += (dados_player['challenges.visionScoreAdvantageLaneOpponent'].values[0])
                    visao_por_minuto_soma += (dados_player['challenges.visionScorePerMinute'].values[0])

                    gold_diff_soma += (dados_player['goldEarned'].iloc[0] - dados_oponente['goldEarned'].iloc[0])
                    cs_diff_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) - 
                                    (dados_oponente['neutralMinionsKilled'].values[0] + dados_oponente['totalMinionsKilled'].values[0]))
                    level_diff_soma += (dados_player['champLevel'].iloc[0] - dados_oponente['champLevel'].iloc[0])
                    kda_diff_soma += (dados_player['challenges.kda'].values[0] - dados_oponente['challenges.kda'].values[0])


                    # Early and Lane Phase para laners
                    vantagem_grande_early_phase_soma += (dados_player['challenges.earlyLaningPhaseGoldExpAdvantage'].values[0])
                    cs_early_game_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] / 10)
                    cs_early_game_compare_oponente_soma += (dados_player['challenges.laneMinionsFirst10Minutes'].values[0] - 
                                                dados_oponente['challenges.laneMinionsFirst10Minutes'].values[0])
                    laner_invade_jg_soma += (dados_player['challenges.getTakedownsInAllLanesEarlyJungleAsLaner'].values[0])

                    maxCs_comparado_com_oponente_soma += (dados_player['challenges.maxCsAdvantageOnLaneOpponent'].values[0])
                    maxLevel_comparado_com_oponente_soma += (dados_player['challenges.maxLevelLeadLaneOpponent'].values[0])
                    vantagem_grande_lane_phase_soma += (dados_player['challenges.laningPhaseGoldExpAdvantage'].values[0])


                    if dados_player['win'].values[0] == True:
                        contagem_wins += 1
                        
                    numero_de_partidas_validas += 1

            elif position_player_input == '4':
                if position_player == 'JUNGLE':
                    kda_soma += (dados_player['challenges.kda'].values[0])
                    kp_soma += (dados_player['challenges.killParticipation'].values[0] * 100)
                    cs_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) / game_duration_minutes)
                    dano_por_gold_soma += (dados_player['totalDamageDealtToChampions'].values[0] / dados_player['goldEarned'].values[0])
                    dano_percent_equipe_soma += (dados_player['challenges.teamDamagePercentage'].values[0] * 100)
                    gold_da_equipe_soma += ((dados_player['goldEarned'].values[0] / total_gold) * 100)
                    score_vision_soma += (dados_player['visionScore'].values[0])
                    visao_comparada_oponente_soma += (dados_player['challenges.visionScoreAdvantageLaneOpponent'].values[0])
                    visao_por_minuto_soma += (dados_player['challenges.visionScorePerMinute'].values[0])

                    gold_diff_soma += (dados_player['goldEarned'].iloc[0] - dados_oponente['goldEarned'].iloc[0])
                    cs_diff_soma += ((dados_player['neutralMinionsKilled'].values[0] + dados_player['totalMinionsKilled'].values[0]) - 
                                    (dados_oponente['neutralMinionsKilled'].values[0] + dados_oponente['totalMinionsKilled'].values[0]))
                    level_diff_soma += (dados_player['champLevel'].iloc[0] - dados_oponente['champLevel'].iloc[0])
                    kda_diff_soma += (dados_player['challenges.kda'].values[0] - dados_oponente['challenges.kda'].values[0])

                    jungle_cs_before_10minutes_soma += (dados_player['challenges.jungleCsBefore10Minutes'].values[0] - 
                                            dados_oponente['challenges.jungleCsBefore10Minutes'].values[0])
                    jungler_kill_invade_early_soma += (dados_player['challenges.junglerKillsEarlyJungle'].values[0])
                    jg_ganks_kill_early_soma += (dados_player['challenges.killsOnLanersEarlyJungleAsJungler'].values[0])

                    wards_colocadas_soma += (dados_player['wardsPlaced'].values[0])
                    wards_eliminadas_soma += (dados_player['wardsKilled'].values[0])
                    control_wards_colocadas_soma += (dados_player['challenges.controlWardsPlaced'].values[0])

                    if dados_player['win'].values[0] == True:
                        contagem_wins += 1

                    numero_de_partidas_validas += 1

            elif position_player_input == '5':
                if position_player == 'UTILITY':
                    kda_soma += (dados_player['challenges.kda'].values[0])
                    kp_soma += (dados_player['challenges.killParticipation'].values[0] * 100)
                    dano_por_gold_soma += (dados_player['totalDamageDealtToChampions'].values[0] / dados_player['goldEarned'].values[0])
                    dano_percent_equipe_soma += (dados_player['challenges.teamDamagePercentage'].values[0] * 100)
                    gold_da_equipe_soma += ((dados_player['goldEarned'].values[0] / total_gold) * 100)
                    score_vision_soma += (dados_player['visionScore'].values[0])
                    visao_comparada_oponente_soma += (dados_player['challenges.visionScoreAdvantageLaneOpponent'].values[0])
                    visao_por_minuto_soma += (dados_player['challenges.visionScorePerMinute'].values[0])

                    gold_diff_soma += (dados_player['goldEarned'].iloc[0] - dados_oponente['goldEarned'].iloc[0])
                    level_diff_soma += (dados_player['champLevel'].iloc[0] - dados_oponente['champLevel'].iloc[0])
                    kda_diff_soma += (dados_player['challenges.kda'].values[0] - dados_oponente['challenges.kda'].values[0])

                    wards_colocadas_soma += (dados_player['wardsPlaced'].values[0])
                    wards_eliminadas_soma += (dados_player['wardsKilled'].values[0])
                    control_wards_colocadas_soma += (dados_player['challenges.controlWardsPlaced'].values[0])


                    if dados_player['win'].values[0] == True:
                        contagem_wins += 1
                    
                    numero_de_partidas_validas += 1

            elif position_player_input == '6':
                print('Em Andamento!')
            else:
                print('Opção inválida')
    
    
    #hora dos prints
    if position_player_input == '1':
        if kda_soma == 0:
            print("Não foram encontradas partidas.")
        else:
            kda_media = kda_soma / numero_de_partidas_validas
            kp_media = kp_soma / numero_de_partidas_validas
            cs_media = cs_soma / numero_de_partidas_validas
            dano_por_gold_media = dano_por_gold_soma / numero_de_partidas_validas
            dano_percent_equipe_media = dano_percent_equipe_soma / numero_de_partidas_validas
            gold_da_equipe_media = gold_da_equipe_soma / numero_de_partidas_validas
            score_vision_media = score_vision_soma / numero_de_partidas_validas
            visao_comparada_oponente_media = visao_comparada_oponente_soma / numero_de_partidas_validas
            visao_por_minuto_media = visao_por_minuto_soma / numero_de_partidas_validas
            gold_diff_media = gold_diff_soma / numero_de_partidas_validas
            cs_diff_media = cs_diff_soma / numero_de_partidas_validas
            level_diff_media = level_diff_soma / numero_de_partidas_validas
            kda_diff_media = kda_diff_soma / numero_de_partidas_validas

            # Early and Lane Phase para laners
            vantagem_grande_early_phase_media = vantagem_grande_early_phase_soma / numero_de_partidas_validas
            cs_early_game_media = cs_early_game_soma / numero_de_partidas_validas
            cs_early_game_compare_oponente_media = cs_early_game_compare_oponente_soma / numero_de_partidas_validas
            laner_invade_jg_media = laner_invade_jg_soma / numero_de_partidas_validas
            maxCs_comparado_com_oponente_media = maxCs_comparado_com_oponente_soma / numero_de_partidas_validas
            maxLevel_comparado_com_oponente_media = maxLevel_comparado_com_oponente_soma / numero_de_partidas_validas
            vantagem_grande_lane_phase_media = vantagem_grande_lane_phase_soma / numero_de_partidas_validas

            # Print das médias calculadas
            print("------------------------------------")
            print(f"Médias do(a) jogador(a) {gameName}:")
            print("------------------------------------")
            print(f"Número de partidas analisadas: {numero_de_partidas_validas}")
            print("------------------------------------")
            print(f"Partidas vencidas: {contagem_wins}")
            print("------------------------------------")
            print(f"KDA Médio: {kda_media:.2f}")
            print(f"Média de Kill Participation (KP): {kp_media:.2f}")
            print(f"Média de CS: {cs_media:.2f}")
            print(f"Média de Dano por Gold: {dano_por_gold_media:.2f}")
            print(f"Dano Percentual da Equipe Médio: {dano_percent_equipe_media:.2f}")
            print(f"Média de Gold da Equipe: {gold_da_equipe_media:.2f}")
            print(f"Média de Score de Visão: {score_vision_media:.2f}")
            print(f"Média de Visão Comparada ao Oponente: {visao_comparada_oponente_media:.2f}")
            print(f"Média de Visão por Minuto: {visao_por_minuto_media:.2f}")
            print(f"Média de Diferença de Gold: {gold_diff_media:.2f}")
            print(f"Média de Diferença de CS: {cs_diff_media:.2f}")
            print(f"Média de Diferença de Nível: {level_diff_media:.2f}")
            print(f"Média de Diferença de KDA: {kda_diff_media:.2f}")
            print("-------------------------------------")
            # Early and Lane Phase para laners
            print("Análise early game: ")
            print(f"Média de Vantagem Grande Early Phase: {vantagem_grande_early_phase_media:.2f}")
            print(f"Média de CS Early Game: {cs_early_game_media:.2f}")
            print(f"Média de CS Early Game Comparado ao Oponente: {cs_early_game_compare_oponente_media:.2f}")
            print(f"Média de Invade de Jungle como Laner (Abates e Assistências): {laner_invade_jg_media:.2f}")
            print("-------------------------------------")
            print("Análise lane phase: ")
            print(f"Média de Máximo de CS Comparado com Oponente: {maxCs_comparado_com_oponente_media:.2f}")
            print(f"Média de Máximo de Nível Comparado com Oponente: {maxLevel_comparado_com_oponente_media:.2f}")
            print(f"Média de Vantagem Grande Lane Phase: {vantagem_grande_lane_phase_media:.2f}")

    elif position_player_input == '2':
        if kda_soma == 0:
            print("Não foram encontradas partidas.")
        else:
            kda_media = kda_soma / numero_de_partidas_validas
            kp_media = kp_soma / numero_de_partidas_validas
            cs_media = cs_soma / numero_de_partidas_validas
            dano_por_gold_media = dano_por_gold_soma / numero_de_partidas_validas
            dano_percent_equipe_media = dano_percent_equipe_soma / numero_de_partidas_validas
            gold_da_equipe_media = gold_da_equipe_soma / numero_de_partidas_validas
            score_vision_media = score_vision_soma / numero_de_partidas_validas
            visao_comparada_oponente_media = visao_comparada_oponente_soma / numero_de_partidas_validas
            visao_por_minuto_media = visao_por_minuto_soma / numero_de_partidas_validas
            gold_diff_media = gold_diff_soma / numero_de_partidas_validas
            cs_diff_media = cs_diff_soma / numero_de_partidas_validas
            level_diff_media = level_diff_soma / numero_de_partidas_validas
            kda_diff_media = kda_diff_soma / numero_de_partidas_validas

            # Early and Lane Phase para laners
            print("Análise early game: ")
            print(f"Média de Vantagem Grande Early Phase: {vantagem_grande_early_phase_media:.2f}")
            print(f"Média de CS Early Game: {cs_early_game_media:.2f}")
            print(f"Média de CS Early Game Comparado ao Oponente: {cs_early_game_compare_oponente_media:.2f}")
            print(f"Média de Invade de Jungle como Laner (Abates e Assistências): {laner_invade_jg_media:.2f}")
            print("-------------------------------------")
            print("Análise lane phase: ")
            print(f"Média de Máximo de CS Comparado com Oponente: {maxCs_comparado_com_oponente_media:.2f}")
            print(f"Média de Máximo de Nível Comparado com Oponente: {maxLevel_comparado_com_oponente_media:.2f}")
            print(f"Média de Vantagem Grande Lane Phase: {vantagem_grande_lane_phase_media:.2f}")

            # Print das médias calculadas
            print("------------------------------------")
            print(f"Médias do(a) jogador(a) {gameName}:")
            print("------------------------------------")
            print(f"Número de partidas analisadas: {numero_de_partidas_validas}")
            print("------------------------------------")
            print(f"Partidas vencidas: {contagem_wins}")
            print("------------------------------------")
            print(f"KDA Médio: {kda_media:.2f}")
            print(f"Média de Kill Participation (KP): {kp_media:.2f}")
            print(f"Média de CS: {cs_media:.2f}")
            print(f"Média de Dano por Gold: {dano_por_gold_media:.2f}")
            print(f"Dano Percentual da Equipe Médio: {dano_percent_equipe_media:.2f}")
            print(f"Média de Gold da Equipe: {gold_da_equipe_media:.2f}")
            print(f"Média de Score de Visão: {score_vision_media:.2f}")
            print(f"Média de Visão Comparada ao Oponente: {visao_comparada_oponente_media:.2f}")
            print(f"Média de Visão por Minuto: {visao_por_minuto_media:.2f}")
            print(f"Média de Diferença de Gold: {gold_diff_media:.2f}")
            print(f"Média de Diferença de CS: {cs_diff_media:.2f}")
            print(f"Média de Diferença de Nível: {level_diff_media:.2f}")
            print(f"Média de Diferença de KDA: {kda_diff_media:.2f}")
            print("-------------------------------------")
            # Early and Lane Phase para laners
            print("Análise early e lane phase: ")
            print(f"Média de Vantagem Grande Early Phase: {vantagem_grande_early_phase_media:.2f}")
            print(f"Média de CS Early Game: {cs_early_game_media:.2f}")
            print(f"Média de CS Early Game Comparado ao Oponente: {cs_early_game_compare_oponente_media:.2f}")
            print(f"Média de Invade de Jungle como Laner (Abates e Assistências): {laner_invade_jg_media:.2f}")
            print(f"Média de Máximo de CS Comparado com Oponente: {maxCs_comparado_com_oponente_media:.2f}")
            print(f"Média de Máximo de Nível Comparado com Oponente: {maxLevel_comparado_com_oponente_media:.2f}")
            print(f"Média de Vantagem Grande Lane Phase: {vantagem_grande_lane_phase_media:.2f}")        

    elif position_player_input == '3':
        if kda_soma == 0:
            print("Não foram encontradas partidas.")
        else:
            kda_media = kda_soma / numero_de_partidas_validas
            kp_media = kp_soma / numero_de_partidas_validas
            cs_media = cs_soma / numero_de_partidas_validas
            dano_por_gold_media = dano_por_gold_soma / numero_de_partidas_validas
            dano_percent_equipe_media = dano_percent_equipe_soma / numero_de_partidas_validas
            gold_da_equipe_media = gold_da_equipe_soma / numero_de_partidas_validas
            score_vision_media = score_vision_soma / numero_de_partidas_validas
            visao_comparada_oponente_media = visao_comparada_oponente_soma / numero_de_partidas_validas
            visao_por_minuto_media = visao_por_minuto_soma / numero_de_partidas_validas
            gold_diff_media = gold_diff_soma / numero_de_partidas_validas
            cs_diff_media = cs_diff_soma / numero_de_partidas_validas
            level_diff_media = level_diff_soma / numero_de_partidas_validas
            kda_diff_media = kda_diff_soma / numero_de_partidas_validas

            # Early and Lane Phase para laners
            vantagem_grande_early_phase_media = vantagem_grande_early_phase_soma / numero_de_partidas_validas
            cs_early_game_media = cs_early_game_soma / numero_de_partidas_validas
            cs_early_game_compare_oponente_media = cs_early_game_compare_oponente_soma / numero_de_partidas_validas
            laner_invade_jg_media = laner_invade_jg_soma / numero_de_partidas_validas
            maxCs_comparado_com_oponente_media = maxCs_comparado_com_oponente_soma / numero_de_partidas_validas
            maxLevel_comparado_com_oponente_media = maxLevel_comparado_com_oponente_soma / numero_de_partidas_validas
            vantagem_grande_lane_phase_media = vantagem_grande_lane_phase_soma / numero_de_partidas_validas

            # Print das médias calculadas
            print("------------------------------------")
            print(f"Médias do(a) jogador(a) {gameName}:")
            print("------------------------------------")
            print(f"Número de partidas analisadas: {numero_de_partidas_validas}")
            print("------------------------------------")
            print(f"Partidas vencidas: {contagem_wins}")
            print("------------------------------------")
            print(f"KDA Médio: {kda_media:.2f}")
            print(f"Média de Kill Participation (KP): {kp_media:.2f}")
            print(f"Média de CS: {cs_media:.2f}")
            print(f"Média de Dano por Gold: {dano_por_gold_media:.2f}")
            print(f"Dano Percentual da Equipe Médio: {dano_percent_equipe_media:.2f}")
            print(f"Média de Gold da Equipe: {gold_da_equipe_media:.2f}")
            print(f"Média de Score de Visão: {score_vision_media:.2f}")
            print(f"Média de Visão Comparada ao Oponente: {visao_comparada_oponente_media:.2f}")
            print(f"Média de Visão por Minuto: {visao_por_minuto_media:.2f}")
            print(f"Média de Diferença de Gold: {gold_diff_media:.2f}")
            print(f"Média de Diferença de CS: {cs_diff_media:.2f}")
            print(f"Média de Diferença de Nível: {level_diff_media:.2f}")
            print(f"Média de Diferença de KDA: {kda_diff_media:.2f}")
            print("-------------------------------------")
            # Early and Lane Phase para laners
            print("Análise early game: ")
            print(f"Média de Vantagem Grande Early Phase: {vantagem_grande_early_phase_media:.2f}")
            print(f"Média de CS Early Game: {cs_early_game_media:.2f}")
            print(f"Média de CS Early Game Comparado ao Oponente: {cs_early_game_compare_oponente_media:.2f}")
            print(f"Média de Invade de Jungle como Laner (Abates e Assistências): {laner_invade_jg_media:.2f}")
            print("-------------------------------------")
            print("Análise lane phase: ")
            print(f"Média de Máximo de CS Comparado com Oponente: {maxCs_comparado_com_oponente_media:.2f}")
            print(f"Média de Máximo de Nível Comparado com Oponente: {maxLevel_comparado_com_oponente_media:.2f}")
            print(f"Média de Vantagem Grande Lane Phase: {vantagem_grande_lane_phase_media:.2f}")

    elif position_player_input == '4':
        if kda_soma == 0:
            print("Não foram encontradas partidas.")
        else:
            kda_media = kda_soma / numero_de_partidas_validas
            kp_media = kp_soma / numero_de_partidas_validas
            cs_media = cs_soma / numero_de_partidas_validas
            dano_por_gold_media = dano_por_gold_soma / numero_de_partidas_validas
            dano_percent_equipe_media = dano_percent_equipe_soma / numero_de_partidas_validas
            gold_da_equipe_media = gold_da_equipe_soma / numero_de_partidas_validas
            score_vision_media = score_vision_soma / numero_de_partidas_validas
            visao_comparada_oponente_media = visao_comparada_oponente_soma / numero_de_partidas_validas
            visao_por_minuto_media = visao_por_minuto_soma / numero_de_partidas_validas
            gold_diff_media = gold_diff_soma / numero_de_partidas_validas
            cs_diff_media = cs_diff_soma / numero_de_partidas_validas
            level_diff_media = level_diff_soma / numero_de_partidas_validas
            kda_diff_media = kda_diff_soma / numero_de_partidas_validas

            jungle_cs_before_10minutes_media = jungle_cs_before_10minutes_soma / numero_de_partidas_validas
            jungler_kill_invade_early_media = jungler_kill_invade_early_soma / numero_de_partidas_validas
            jg_ganks_kill_early_media = jg_ganks_kill_early_soma / numero_de_partidas_validas
            wards_colocadas_media = wards_colocadas_soma / numero_de_partidas_validas
            wards_eliminadas_media = wards_eliminadas_soma / numero_de_partidas_validas
            control_wards_colocadas_media = control_wards_colocadas_soma / numero_de_partidas_validas

            print("------------------------------------")
            print(f"Médias do(a) jogador(a) {gameName}:")
            print("------------------------------------")
            print(f"Número de partidas analisadas: {numero_de_partidas_validas}")
            print("------------------------------------")
            print(f"Partidas vencidas: {contagem_wins}")
            print("------------------------------------")
            print(f"KDA Médio: {kda_media:.2f}")
            print(f"Médaia de Kill Participation (KP): {kp_media:.2f}")
            print(f"Média de CS: {cs_media:.2f}")
            print(f"Média de Dano por Gold: {dano_por_gold_media:.2f}")
            print(f"Dano Percentual da Equipe Médio: {dano_percent_equipe_media:.2f}")
            print(f"Média de Gold da Equipe: {gold_da_equipe_media:.2f}")
            print(f"Média de Score de Visão: {score_vision_media:.2f}")
            print(f"Média de Visão Comparada ao Oponente: {visao_comparada_oponente_media:.2f}")
            print(f"Média de Visão por Minuto: {visao_por_minuto_media:.2f}")
            print(f"Média de Diferença de Gold: {gold_diff_media:.2f}")
            print(f"Média de Diferença de CS: {cs_diff_media:.2f}")
            print(f"Média de Diferença de Nível: {level_diff_media:.2f}")
            print(f"Média de Diferença de KDA: {kda_diff_media:.2f}")
            print("------------------------------------")
            print("\nMédias das Métricas de Jungle no Early Game:")
            print(f"Média de CS na Jungle Antes dos 10 Minutos: {jungle_cs_before_10minutes_media:.2f}")
            print(f"Média de Kill Invade Early: {jungler_kill_invade_early_media:.2f}")
            print(f"Média de Ganks na Jungle (Early) com Kill: {jg_ganks_kill_early_media:.2f}")
            print("\nMédias das Métricas de Jungle em questão de Visão:")
            print(f"Média de Wards Colocadas: {wards_colocadas_media:.2f}")
            print(f"Média de Wards Eliminadas: {wards_eliminadas_media:.2f}")
            print(f"Média de Control Wards Colocadas: {control_wards_colocadas_media:.2f}")

    elif position_player_input == '5':
        if kda_soma == 0:
            print("Não foram encontradas partidas.")
        else:
            kda_media = kda_soma / numero_de_partidas_validas
            kp_media = kp_soma / numero_de_partidas_validas
            dano_por_gold_media = dano_por_gold_soma / numero_de_partidas_validas
            dano_percent_equipe_media = dano_percent_equipe_soma / numero_de_partidas_validas
            gold_da_equipe_media = gold_da_equipe_soma / numero_de_partidas_validas
            score_vision_media = score_vision_soma / numero_de_partidas_validas
            visao_comparada_oponente_media = visao_comparada_oponente_soma / numero_de_partidas_validas
            visao_por_minuto_media = visao_por_minuto_soma / numero_de_partidas_validas
            gold_diff_media = gold_diff_soma / numero_de_partidas_validas
            level_diff_media = level_diff_soma / numero_de_partidas_validas
            kda_diff_media = kda_diff_soma / numero_de_partidas_validas

            wards_colocadas_media = wards_colocadas_soma / numero_de_partidas_validas
            wards_eliminadas_media = wards_eliminadas_soma / numero_de_partidas_validas
            control_wards_colocadas_media = control_wards_colocadas_soma / numero_de_partidas_validas
            
            print("------------------------------------")
            print(f"Médias do(a) jogador(a) {gameName}:")
            print("------------------------------------")
            print(f"Número de partidas analisadas: {numero_de_partidas_validas}")
            print("------------------------------------")
            print(f"Partidas vencidas: {contagem_wins}")
            print("------------------------------------")
            print(f"KDA Médio: {kda_media:.2f}")
            print(f"Médaia de Kill Participation (KP): {kp_media:.2f}")
            print(f"Média de Dano por Gold: {dano_por_gold_media:.2f}")
            print(f"Dano Percentual da Equipe Médio: {dano_percent_equipe_media:.2f}")
            print(f"Média de Gold da Equipe: {gold_da_equipe_media:.2f}")
            print(f"Média de Score de Visão: {score_vision_media:.2f}")
            print(f"Média de Visão Comparada ao Oponente: {visao_comparada_oponente_media:.2f}")
            print(f"Média de Visão por Minuto: {visao_por_minuto_media:.2f}")
            print(f"Média de Diferença de Gold: {gold_diff_media:.2f}")
            print(f"Média de Diferença de Nível: {level_diff_media:.2f}")
            print(f"Média de Diferença de KDA: {kda_diff_media:.2f}")
            print("------------------------------------")
            print("\nMédias das Métricas de visão para Support - foco em visão:")
            print(f"Média de Wards Colocadas: {wards_colocadas_media:.2f}")
            print(f"Média de Wards Eliminadas: {wards_eliminadas_media:.2f}")
            print(f"Média de Control Wards Colocadas: {control_wards_colocadas_media:.2f}")

  print("Obrigado por usar o programa. Tchau!")

if __name__ == "__main__":
    main()