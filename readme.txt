netflix app 
add funcionalidades

- dividir uma lista de filmes, series e animes.  

- remover filmes da lista 

- Concertar bug da barra lateral quando a barra lateral se expande e fecha , o layout principal se desalinha ficando mais espaçado, faça com que o layout volte ao normal após fechar a barra lateral. Além disso, quando uso o input de pesquisa na barra lateral o layout dos filmes também aparecem espaçados. 

- Infinite horizontal scroll animation (para o historico)

- se o programa estiver em tela cheia, remova a "barra de titulo do windows" da janela de "adicionar filme" e na janela de "informação", na janela de "informação" adicione uma botão de voltar com um "svg" no canto inferior esquerdo abaixo do botão "ver trailer", além disso arredonde as bordas das janelas para deixar mais suave.

- adicionar a logo na sidebar em cima do texto: "pesquisa de filmes".

- adicionar capas manualmente caso não encontre nenhum resultado de info

- borda das capas do filmes mais arredondada

- padronize o tamanho das capas 

- configurar para a janela de info abrir onde o programa esta e centralizado, exemplo: "monitor 1"

- historico de filmes assistidos, aparecerá na primeira fileira e se extenderá para fora da tela a direta, para ver o historico completo é só ir pressionando e arrastando o mouse para a esquerda.

- scanear os caminhos dos filmes quando iniciar o programa e verificar se esses caminhos ainda existem, caso não existam mais, remove o filme da lista automaticamente. 

- estilizar os botões de filtro da sidebar com UI/UX de acordo com o tema do restante do programa. 

- otimizar o codigo para evitar travamentos 

- adicionar a pasta raiz de onde estão os filmes, scanear todas as pastas e sub pastas em busca do arquivo de video do filme, compara o nome da pasta (caso esteja dentro de uma) com o nome do arquivo de video para ter certeza que aquele é o arquivo certo, filtrar o nome das pastas removendo:"datas ex: 2020,2021...", "dublado", "WEB-DEL", "DUAL","5.1","2.0",".","EAC3","AAC","NACIONAL","x264","DVDRip","Xvid","[]","dublagem","bks","by","gmv","SF","1080p","starckfilmes","x265","BlueRay","WWW","()","*","BLUEDV","5.1ch","WEB","LAPUMiAFiLMES","Áudio","coleção completa","720p","RICKSZ","THEPIRATEFILMES","LuaHarper". Após essas filtragens e verificações, busca as informações do filme no tmdb e atuliza automaticamente o catalogo com o novo filme, caso não encontre o filme, gera uma lista com os nomes das pastas para saber quais não conseguiram ser adicionados. 