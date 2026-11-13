/*
 * PIM II - Sabor & Cia Bistro
 * Simulador em console do Cardapio Digital
 *
 * Funcionalidades:
 * - Cliente: visualizar o cardapio ativo de uma filial
 * - Gerente: ativar/desativar produtos somente da propria filial
 * - Administrador: cadastrar produtos, listar todos e ver relatorios
 *    (indisponibilidade atual e frequencia de esgotamento)
 *
 * Estruturas usadas: vetor de structs (produtos e usuarios),
 * matriz (disponibilidade produto x filial) e arquivos texto
 * (cardapio.txt para os dados, historico.txt para o log de alteracoes).
 * Cada alteracao e "tudo ou nada": se o cardapio ou o historico nao puder
 * ser gravado, a alteracao e desfeita (como a transacao do banco). Antes de
 * gravar, o programa cria o arquivo pendencia.txt com a operacao e so o
 * apaga quando os dois arquivos estao de acordo; se nem desfazer for
 * possivel, ele fica no disco e a proxima execucao pede a conferencia.
 *
 * Obs.: os textos do programa estao sem acento para evitar problemas
 * de exibicao no console do Windows.
 *
 * AVISO DE SEGURANCA - SIMULACAO ACADEMICA
 * Por simplificacao didatica, os usuarios de teste estao fixos no codigo,
 * as senhas ficam em texto puro, os arquivos .txt nao tem controle de
 * acesso e o limite de 3 tentativas vale apenas por execucao. Isso NAO
 * representa o sistema real: em producao as senhas ficam somente como
 * hash bcrypt no banco (coluna usuario.senha_hash, RNF04), conforme a
 * secao 6.7 do relatorio e o script database/modelo_fisico_mysql.sql.
 */

#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L /* fsync, fileno e stat tambem com -std=c99 */
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>
#include <errno.h>
#include <sys/stat.h> /* stat: o arquivo existe e e um arquivo comum? */
#ifdef _WIN32
#include <windows.h> /* MoveFileExA: troca do arquivo (salvarDados) */
#include <io.h>      /* _commit: forca a gravacao no disco */
#else
#include <unistd.h>  /* fsync: forca a gravacao no disco */
#endif
 
#define MAX_PRODUTOS  100
#define NUM_FILIAIS   3
#define NUM_USUARIOS  4
#define TAM_NOME      60
#define TAM_CATEGORIA 30
#define TAM_ALERGENOS 80
#define ARQ_DADOS     "cardapio.txt"
#define ARQ_DADOS_TMP "cardapio.tmp" /* gravacao segura (ver salvarDados) */
#define ARQ_HISTORICO "historico.txt"
#define ARQ_PENDENCIA "pendencia.txt" /* alteracao em andamento (ver abrirPendencia) */

#define PERFIL_ADMIN   1
#define PERFIL_GERENTE 2
 
/* ---------- Estruturas ---------- */
 
typedef struct {
    int id;
    char nome[TAM_NOME];
    char categoria[TAM_CATEGORIA];
    int preco_cent; /* preco em centavos; evita erro de arredondamento do float */
    char alergenos[TAM_ALERGENOS]; /* lista separada por virgula; "nenhum" se vazio */
} Produto;
 
typedef struct {
    char login[20];
    char senha[20];
    int perfil; /* PERFIL_ADMIN ou PERFIL_GERENTE */
    int filial; /* indice da filial do gerente; -1 para admin */
} Usuario;
 
/* ---------- Dados globais ---------- */
 
const char *FILIAIS[NUM_FILIAIS] = {"Jardins", "Itaim Bibi", "Pinheiros"};
 
Produto produtos[MAX_PRODUTOS]; /* vetor de produtos */
 
int disponibilidade[MAX_PRODUTOS][NUM_FILIAIS]; /* matriz: 1 = ativo, 0 = inativo */
int qtdProdutos = 0;
 
/* Credenciais de TESTE, fixas no codigo e em texto puro, APENAS para a
   simulacao. No sistema real os usuarios ficam na tabela usuario do banco,
   a senha e guardada so como hash bcrypt e conferida pela funcao de
   verificacao da biblioteca (RNF04); nenhuma senha fica no codigo-fonte. */
Usuario usuarios[NUM_USUARIOS] = {{"admin", "admin123", PERFIL_ADMIN, -1},
                                  {"jardins", "1234", PERFIL_GERENTE, 0},
                                  {"itaim", "1234", PERFIL_GERENTE, 1},
                                  {"pinheiros", "1234", PERFIL_GERENTE, 2}};
 
/* ---------- Funcoes de entrada ---------- */
 
/* Le uma linha de texto e remove o '\n' do final */
void lerTexto(const char *mensagem, char *destino, int tamanho) {
    printf("%s", mensagem);
    if (fgets(destino, tamanho, stdin) == NULL) { /* fim da entrada */
        printf("\nEntrada encerrada.\n");
        exit(0);
    }
    if (strchr(destino, '\n') == NULL) { /* linha maior que o buffer */
        int c;
        while ((c = getchar()) != '\n' && c != EOF) {}
    }
    destino[strcspn(destino, "\n")] = '\0';
}
 
/* Le um numero inteiro, repetindo ate o usuario digitar um valor valido */
int lerInteiro(const char *mensagem) {
    char linha[50];
    int valor;
    while (1) {
        lerTexto(mensagem, linha, sizeof(linha));
        if (sscanf(linha, "%d", &valor) == 1) {
            return valor;
        }
        printf("Valor invalido. Digite um numero inteiro.\n");
    }
}
 
/* Le um preco positivo e o devolve em centavos (inteiro), evitando erros de
   arredondamento do float. Aceita virgula ou ponto como separador decimal. */
int lerPreco(const char *mensagem) {
    char linha[50];
    float valor;
    int i;
    while (1) {
        lerTexto(mensagem, linha, sizeof(linha));
        for (i = 0; linha[i] != '\0'; i++) {
            if (linha[i] == ',')
                linha[i] = '.';
        }
        if (sscanf(linha, "%f", &valor) == 1 && valor > 0) {
            return (int)(valor * 100.0 + 0.5); /* reais -> centavos, arredondado */
        }
        printf("Preco invalido. Digite um valor maior que zero.\n");
    }
}
 
/* ---------- Arquivos ---------- */

/* Esvazia o buffer da biblioteca C e pede ao sistema que grave o arquivo no
   disco (e nao so na memoria cache). Retorna 1 se conseguiu. */
int gravarNoDisco(FILE *arq) {
    if (fflush(arq) != 0) {
        return 0;
    }
#ifdef _WIN32
    return _commit(_fileno(arq)) == 0;
#else
    return fsync(fileno(arq)) == 0;
#endif
}

/* Retorna 1 se o nome existe e e um arquivo comum (uma pasta com o mesmo
   nome nao conta). Usa stat, que nao abre o arquivo: um arquivo bloqueado
   por outro programa tambem conta como existente. */
int arquivoComum(const char *nome) {
    struct stat info;
    return stat(nome, &info) == 0 && (info.st_mode & S_IFMT) == S_IFREG;
}

/* RF11: acrescenta uma linha no historico: data/hora;acao;produto;filial;usuario.
   Retorna:
    1 se a linha foi gravada;
    0 se nada foi gravado (o arquivo nem abriu);
   -1 se o arquivo abriu mas a gravacao falhou: a linha pode ter ficado no
      disco, inteira ou pela metade, e nao da para saber qual. */
int registrarHistorico(const char *acao, int idProduto, int filial,
                       const char *login) {
    FILE *arq = fopen(ARQ_HISTORICO, "a");
    time_t agora = time(NULL);
    char dataHora[20];
    int ok;

    if (arq == NULL) {
        printf("Erro: nao foi possivel gravar o historico.\n");
        return 0;
    }
    strftime(dataHora, sizeof(dataHora), "%d/%m/%Y %H:%M", localtime(&agora));
    ok = fprintf(arq, "%s;%s;%d;%s;%s\n", dataHora, acao, idProduto,
                 (filial >= 0) ? FILIAIS[filial] : "Todas", login) >= 0
         && gravarNoDisco(arq); /* como o cardapio: a linha vai para o disco */
    if (fclose(arq) != 0) { /* o fclose descarrega o buffer: pode falhar aqui */
        ok = 0;
    }
    if (!ok) {
        printf("Erro: nao foi possivel gravar o historico "
               "(a linha pode ter ficado no arquivo, inteira ou incompleta).\n");
        return -1;
    }
    return 1;
}

/* Marca no disco que uma alteracao comecou: grava acao;produto;filial;usuario
   em pendencia.txt ANTES de mexer no cardapio e no historico. O arquivo so e
   apagado (fecharPendencia) quando os dois estao de acordo; se o programa
   parar no meio, a proxima execucao o encontra (carregarDados).
   Retorna 1 se gravou e 0 em caso de falha (nada fica no disco). */
int abrirPendencia(const char *acao, int idProduto, int filial, const char *login) {
    FILE *arq = fopen(ARQ_PENDENCIA, "w");
    int ok;

    if (arq == NULL) {
        printf("Erro: nao foi possivel gravar o arquivo %s.\n", ARQ_PENDENCIA);
        return 0;
    }
    ok = fprintf(arq, "%s;%d;%s;%s\n", acao, idProduto,
                 (filial >= 0) ? FILIAIS[filial] : "Todas", login) >= 0
         && gravarNoDisco(arq);
    if (fclose(arq) != 0) {
        ok = 0;
    }
    if (!ok) {
        remove(ARQ_PENDENCIA);
        printf("Erro: nao foi possivel gravar o arquivo %s.\n", ARQ_PENDENCIA);
    }
    return ok;
}

/* A alteracao terminou (gravada ou desfeita) e os arquivos estao de acordo. */
void fecharPendencia(void) {
    if (remove(ARQ_PENDENCIA) != 0) {
        /* lado seguro: a proxima execucao pede uma conferencia desnecessaria */
        printf("Aviso: nao foi possivel apagar o arquivo %s.\n", ARQ_PENDENCIA);
    }
}

/* Nem gravar nem desfazer deu certo: o cardapio e o historico podem nao estar
   de acordo. O pendencia.txt fica no disco e o programa encerra, para que
   nenhuma alteracao seguinte o apague antes da conferencia. */
void encerrarComPendencia(void) {
    printf("Erro: nao foi possivel desfazer a alteracao. Os arquivos %s e %s "
           "podem nao estar de acordo; confira-os e depois apague o arquivo %s.\n"
           "O programa sera encerrado.\n", ARQ_DADOS, ARQ_HISTORICO, ARQ_PENDENCIA);
    exit(1);
}

/* Mostra a operacao gravada no pendencia.txt (acao;produto;filial;usuario). */
void mostrarPendencia(void) {
    char linha[200];
    FILE *arq = fopen(ARQ_PENDENCIA, "r");

    if (arq == NULL) {
        return;
    }
    if (fgets(linha, sizeof(linha), arq) != NULL) {
        linha[strcspn(linha, "\n")] = '\0';
        printf("Alteracao interrompida: %s\n", linha);
    }
    fclose(arq);
}
 
/* Troca o arquivo destino pelo origem numa so chamada do sistema, sem
   apagar o destino antes. Num disco local NTFS (MoveFileEx) ou com o rename
   do POSIX, quem abre o destino ve o conteudo antigo inteiro ou o novo
   inteiro; se a troca falhar, o destino fica intacto. No Windows usa
   MoveFileEx porque o rename da biblioteca C nao substitui um arquivo
   existente; com MOVEFILE_WRITE_THROUGH, a troca ja esta no disco quando a
   funcao retorna. No POSIX isso exigiria tambem um fsync da pasta, que a
   simulacao (feita para o Windows) nao faz. Retorna 1 se trocou. */
int substituirArquivo(const char *origem, const char *destino) {
#ifdef _WIN32
    return MoveFileExA(origem, destino,
                       MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    return rename(origem, destino) == 0;
#endif
}
 
/* Grava produtos e matriz de disponibilidade no arquivo texto.
   Formato de cada linha: id;categoria;nome;preco;alergenos;disp1;disp2;disp3
   Gravacao segura: escreve primeiro em cardapio.tmp, forca o conteudo para
   o disco e so entao troca o cardapio.txt. Assim, uma falha no meio nunca
   deixa o cardapio.txt pela metade e, no Windows, nem uma queda de energia
   logo apos a troca (ver substituirArquivo).
   Retorna 1 se gravou e 0 em caso de falha (o cardapio.txt fica como estava,
   com o estado anterior, e o cardapio.tmp e apagado). */
int salvarDados(void) {
    FILE *arq = fopen(ARQ_DADOS_TMP, "w");
    int i, j, ok;
 
    if (arq == NULL) {
        printf("Erro: nao foi possivel gravar o arquivo %s.\n", ARQ_DADOS);
        return 0;
    }
    fprintf(arq, "%d\n", qtdProdutos);
    for (i = 0; i < qtdProdutos; i++) {
        fprintf(arq, "%d;%s;%s;%d;%s", produtos[i].id, produtos[i].categoria,
                produtos[i].nome, produtos[i].preco_cent, produtos[i].alergenos);
        for (j = 0; j < NUM_FILIAIS; j++) {
            fprintf(arq, ";%d", disponibilidade[i][j]);
        }
        fprintf(arq, "\n");
    }
    ok = !ferror(arq) /* algum fprintf falhou? */
         && gravarNoDisco(arq); /* conteudo no disco ANTES da troca */
    if (fclose(arq) != 0) {
        ok = 0;
    }
    if (!ok) {
        remove(ARQ_DADOS_TMP); /* descarta o arquivo incompleto */
        printf("Erro: nao foi possivel gravar o arquivo %s.\n", ARQ_DADOS);
        return 0;
    }
    if (!substituirArquivo(ARQ_DADOS_TMP, ARQ_DADOS)) {
        remove(ARQ_DADOS_TMP); /* troca recusada: o cardapio.txt segue intacto */
        printf("Erro: nao foi possivel gravar o arquivo %s.\n", ARQ_DADOS);
        return 0;
    }
    return 1;
}
 
/* Le os dados do arquivo. Retorna:
    1 se conseguiu;
    0 se o arquivo nao existe (primeira execucao);
   -1 se o arquivo existe mas e invalido ou nao pode ser lido (bloqueado);
   -2 se so existe o cardapio.tmp de uma gravacao interrompida;
   -3 se existe o pendencia.txt de uma alteracao que nao terminou.
   Nos casos negativos o programa encerra sem gravar nada, para nao apagar
   os dados existentes com os dados de exemplo. O cardapio.tmp nunca e lido
   automaticamente, porque pode conter uma alteracao nao confirmada. */
int carregarDados(void) {
    FILE *arq;
    int i, j, total;

    if (arquivoComum(ARQ_PENDENCIA)) {
        return -3;
    }
    arq = fopen(ARQ_DADOS, "r");
    if (arq == NULL) {
        if (errno != ENOENT) {
            return -1; /* existe, mas nao abriu (permissao, bloqueio...) */
        }
        /* existe um .tmp (legivel ou bloqueado)? entao nao e primeira execucao */
        if (arquivoComum(ARQ_DADOS_TMP)) {
            return -2;
        }
        return 0;
    }
    if (fscanf(arq, "%d\n", &total) != 1 || total < 0 || total > MAX_PRODUTOS) {
        fclose(arq);
        return -1;
    }
    for (i = 0; i < total; i++) {
        if (fscanf(arq, "%d;%29[^;];%59[^;];%d;%79[^;]",
                   &produtos[i].id, produtos[i].categoria, produtos[i].nome,
                   &produtos[i].preco_cent, produtos[i].alergenos) != 5) {
            fclose(arq);
            return -1; /* linha fora do formato */
        }
 
        for (j = 0; j < NUM_FILIAIS; j++) {
            if (fscanf(arq, ";%d", &disponibilidade[i][j]) != 1 ||
                (disponibilidade[i][j] != 0 && disponibilidade[i][j] != 1)) {
                fclose(arq);
                return -1; /* disponibilidade ausente ou diferente de 0/1 */
            }
        }
        fscanf(arq, "\n");
    }
    qtdProdutos = total;
    fclose(arq);
    return 1;
}
 
/* ---------- Produtos ---------- */
 
/* Busca linear: retorna a posicao do produto no vetor ou -1 */
int buscarProdutoPorId(int id) {
    int i;
    for (i = 0; i < qtdProdutos; i++) {
        if (produtos[i].id == id) {
            return i;
        }
    }
    return -1;
}
 
/* Adiciona um produto no vetor, ativo em todas as filiais */
int adicionarProduto(const char *nome, const char *categoria, int precoCent,
                     const char *alergenos) {
    int j;
    if (qtdProdutos >= MAX_PRODUTOS) {
        return -1;
    }
    produtos[qtdProdutos].id =
        (qtdProdutos == 0) ? 1 : produtos[qtdProdutos - 1].id + 1;
    strncpy(produtos[qtdProdutos].nome, nome, TAM_NOME - 1);
    produtos[qtdProdutos].nome[TAM_NOME - 1] = '\0';
    strncpy(produtos[qtdProdutos].categoria, categoria, TAM_CATEGORIA - 1);
    produtos[qtdProdutos].categoria[TAM_CATEGORIA - 1] = '\0';
    produtos[qtdProdutos].preco_cent = precoCent;
    /* lista vazia vira "nenhum" para nao gerar campo em branco no arquivo */
    if (alergenos == NULL || alergenos[0] == '\0') {
        strcpy(produtos[qtdProdutos].alergenos, "nenhum");
    } else {
        strncpy(produtos[qtdProdutos].alergenos, alergenos, TAM_ALERGENOS - 1);
        produtos[qtdProdutos].alergenos[TAM_ALERGENOS - 1] = '\0';
    }
    for (j = 0; j < NUM_FILIAIS; j++) {
        disponibilidade[qtdProdutos][j] = 1;
    }
    qtdProdutos++;
    return produtos[qtdProdutos - 1].id;
}
 
/* Dados de exemplo usados na primeira execucao */
void carregarExemplo(void) {
    adicionarProduto("Burrata com tomates confitados", "Entradas", 6800, "Leite");
    adicionarProduto("Risoto de cogumelos", "Pratos principais", 9800, "Leite");
    adicionarProduto("Salmao em crosta de castanhas",
        "Pratos principais", 11200, "Peixe,Castanha-de-caju");
    adicionarProduto("Petit gateau", "Sobremesas", 4200, "Leite,Ovos,Trigo");
    adicionarProduto("Chardonnay (taca)", "Vinhos", 4500, "");
    if (!salvarDados()) {
        printf("Aviso: os dados de exemplo nao foram gravados; "
               "as alteracoes nao serao salvas.\n");
    }
}
 
/* RF05 (simplificado): cadastro de produto pelo administrador */
void cadastrarProduto(const char *login) {
    char nome[TAM_NOME], categoria[TAM_CATEGORIA], alergenos[TAM_ALERGENOS];
    int preco; /* em centavos (retorno de lerPreco) */
    int id, resultado;
 
    printf("\n--- Cadastrar produto ---\n");
    lerTexto("Nome: ", nome, sizeof(nome));
    lerTexto("Categoria: ", categoria, sizeof(categoria));
    if (strlen(nome) == 0 || strlen(categoria) == 0) {
        printf("Nome e categoria sao obrigatorios.\n");
        return;
    }
    lerTexto("Alergenos (separe por virgula, enter para nenhum): ", alergenos,
             sizeof(alergenos));
    if (strchr(nome, ';') != NULL || strchr(categoria, ';') != NULL ||
        strchr(alergenos, ';') != NULL) {
        printf("O caractere ';' nao e permitido.\n");
        return;
    }
    preco = lerPreco("Preco (R$): ");
 
    id = adicionarProduto(nome, categoria, preco, alergenos);
    if (id == -1) {
        printf("Limite de %d produtos atingido.\n", MAX_PRODUTOS);
        return;
    }
    /* tudo ou nada: se o cardapio ou o historico nao puder ser gravado,
       o produto sai do vetor e o arquivo volta ao estado anterior */
    if (!abrirPendencia("CADASTRAR", id, -1, login)) {
        qtdProdutos--;
        printf("O cadastro foi desfeito.\n");
        return;
    }
    if (!salvarDados()) {
        qtdProdutos--;
        fecharPendencia(); /* o cardapio.txt ficou como estava */
        printf("O cadastro foi desfeito.\n");
        return;
    }
    resultado = registrarHistorico("CADASTRAR", id, -1, login);
    if (resultado != 1) {
        qtdProdutos--;
        /* so fica tudo de acordo se o historico nao recebeu nada (0) e o
           cardapio voltou ao estado anterior */
        if (resultado == 0 && salvarDados()) {
            fecharPendencia();
            printf("O cadastro foi desfeito.\n");
            return;
        }
        encerrarComPendencia();
    }
    fecharPendencia();
    printf("Produto %d cadastrado e ativo em todas as filiais.\n", id);
}
 
/* Retorna 1 se a lista de alergenos contem o termo informado (ignora
   maiusculas/minusculas). Comparacao por substring, suficiente para a
   simulacao. Lista "nenhum" nunca casa com um filtro valido. */
int contemAlergeno(const char *lista, const char *termo) {
    char l[TAM_ALERGENOS], t[TAM_ALERGENOS];
    int i;
    if (termo == NULL || termo[0] == '\0') {
        return 0;
    }
    for (i = 0; lista[i] != '\0' && i < TAM_ALERGENOS - 1; i++) {
        l[i] = (char)tolower((unsigned char)lista[i]);
    }
    l[i] = '\0';
    for (i = 0; termo[i] != '\0' && i < TAM_ALERGENOS - 1; i++) {
        t[i] = (char)tolower((unsigned char)termo[i]);
    }
    t[i] = '\0';
    return strstr(l, t) != NULL;
}
 
/* RF07/RF13: mostra o cardapio de uma filial com os alergenos de cada item.
   somenteAtivos = 1 -> visao do cliente; 0 -> visao do gerente (com status).
   filtroAlergeno (se nao vazio) oculta, na visao do cliente, os pratos que
   contem o alergeno informado. */
void exibirCardapio(int filial, int somenteAtivos, const char *filtroAlergeno) {
    int i, exibidos = 0, ocultados = 0;
 
    printf("\n=== Sabor & Cia Bistro - %s ===\n", FILIAIS[filial]);
    for (i = 0; i < qtdProdutos; i++) {
        if (somenteAtivos && disponibilidade[i][filial] == 0) {
            continue; /* cliente nao ve itens esgotados */
        }
        if (somenteAtivos && contemAlergeno(produtos[i].alergenos, filtroAlergeno)) {
            ocultados++; /* cliente filtrou este alergeno */
            continue;
        }
        printf("[%3d] %-20s %-35s R$ %5d,%02d", produtos[i].id, produtos[i].categoria,
               produtos[i].nome, produtos[i].preco_cent / 100, produtos[i].preco_cent % 100);
        if (!somenteAtivos) {
            printf(" %s", disponibilidade[i][filial] ? "ATIVO" : "INATIVO");
        }
        printf(" | Alergenos: %s\n", produtos[i].alergenos);
        exibidos++;
    }
    if (exibidos == 0) {
        printf("Nenhum produto disponivel no momento.\n");
    }
    if (somenteAtivos && ocultados > 0) {
        printf("(%d item(ns) oculto(s) pelo filtro de alergeno \"%s\".)\n",
               ocultados, filtroAlergeno);
    }
    if (somenteAtivos) {
        /* RF13: aviso sobre alergenos */
        printf("\nAVISO: informacoes sobre alergenos sao de referencia.\n");
        printf("Em caso de alergia grave, confirme com o garcom.\n");
    }
}
 
/* Lista todos os produtos com a matriz de disponibilidade completa */
void listarTodos(void) {
    int i, j;
 
    printf("\n%-5s %-35s", "ID", "Produto");
    for (j = 0; j < NUM_FILIAIS; j++) {
        printf(" %-11s", FILIAIS[j]);
    }
    printf("\n");
    for (i = 0; i < qtdProdutos; i++) {
        printf("%-5d %-35s", produtos[i].id, produtos[i].nome);
        for (j = 0; j < NUM_FILIAIS; j++) {
            printf(" %-11s", disponibilidade[i][j] ? "ativo" : "INATIVO");
        }
        printf("\n");
    }
}
 
/* RF06: gerente ativa ou desativa um produto. A filial vem do login,
   entao o gerente nunca altera outra unidade. O novo estado e informado
   de forma explicita (1 = ativar, 2 = desativar), em vez de inverter o
   estado atual: repetir a mesma operacao nao desfaz a alteracao. */
void alterarDisponibilidade(int filial, const char *login) {
    int id, pos, opcao, novoEstado, resultado;
    const char *acao;
 
    exibirCardapio(filial, 0, "");
    id = lerInteiro("\nID do produto (0 para voltar): ");
    if (id == 0) {
        return;
    }
    pos = buscarProdutoPorId(id);
    if (pos == -1) {
        printf("Produto nao encontrado.\n");
        return;
    }
 
    do {
        opcao = lerInteiro("1 - Ativar 2 - Desativar: ");
    } while (opcao != 1 && opcao != 2);
    novoEstado = (opcao == 1) ? 1 : 0;
 
    if (disponibilidade[pos][filial] == novoEstado) {
        printf("'%s' ja estava %s. Nada foi alterado.\n", produtos[pos].nome,
               novoEstado ? "ATIVO" : "INATIVO");
        return;
    }
 
    /* tudo ou nada, como a transacao do banco (RF06 + RF11): se o cardapio
       ou o historico nao puder ser gravado, volta ao estado anterior */
    acao = novoEstado ? "ATIVAR" : "DESATIVAR";
    disponibilidade[pos][filial] = novoEstado;
    if (!abrirPendencia(acao, id, filial, login)) {
        disponibilidade[pos][filial] = !novoEstado;
        printf("A alteracao foi desfeita.\n");
        return;
    }
    if (!salvarDados()) {
        disponibilidade[pos][filial] = !novoEstado;
        fecharPendencia(); /* o cardapio.txt ficou como estava */
        printf("A alteracao foi desfeita.\n");
        return;
    }
    resultado = registrarHistorico(acao, id, filial, login);
    if (resultado != 1) {
        disponibilidade[pos][filial] = !novoEstado;
        /* so fica tudo de acordo se o historico nao recebeu nada (0) e o
           cardapio voltou ao estado anterior */
        if (resultado == 0 && salvarDados()) {
            fecharPendencia();
            printf("A alteracao foi desfeita.\n");
            return;
        }
        encerrarComPendencia();
    }
    fecharPendencia();
    printf("'%s' agora esta %s na filial %s.\n", produtos[pos].nome,
           novoEstado ? "ATIVO" : "INATIVO", FILIAIS[filial]);
}
 
/* RF12: quantos itens estao indisponiveis agora em cada filial */
void relatorioIndisponibilidade(void) {
    int i, j, contador;
 
    printf("\n--- Itens indisponiveis por filial ---\n");
    for (j = 0; j < NUM_FILIAIS; j++) {
        contador = 0;
        for (i = 0; i < qtdProdutos; i++) {
            if (disponibilidade[i][j] == 0) {
                contador++;
            }
        }
        printf("%-12s: %d de %d itens\n", FILIAIS[j], contador, qtdProdutos);
    }
}
 
/* Retorna o indice da filial pelo nome, ou -1 se nao existir */
int buscarFilialPorNome(const char *nome) {
    int j;
    for (j = 0; j < NUM_FILIAIS; j++) {
        if (strcmp(FILIAIS[j], nome) == 0) {
            return j;
        }
    }
    return -1;
}
 
/* RF12: frequencia de esgotamento. Le o historico.txt e conta, numa
   matriz produto x filial, quantas vezes cada item foi desativado. */
void relatorioFrequencia(void) {
    int frequencia[MAX_PRODUTOS][NUM_FILIAIS] = {{0}};
    char linha[200], acao[20], nomeFilial[30], login[20];
    int idProduto, pos, filial, i, j, total = 0;
    FILE *arq = fopen(ARQ_HISTORICO, "r");
 
    if (arq == NULL) {
        printf("Ainda nao ha historico de alteracoes.\n");
        return;
    }
    /* formato: data hora;acao;id;filial;login */
    while (fgets(linha, sizeof(linha), arq) != NULL) {
        if (sscanf(linha, "%*[^;];%19[^;];%d;%29[^;];%19s", acao, &idProduto,
                   nomeFilial, login) != 4) {
            continue; /* linha fora do formato: ignora */
        }
        if (strcmp(acao, "DESATIVAR") != 0) {
            continue;
        }
        pos = buscarProdutoPorId(idProduto);
        filial = buscarFilialPorNome(nomeFilial);
        if (pos != -1 && filial != -1) {
            frequencia[pos][filial]++;
            total++;
        }
    }
    fclose(arq);
 
    printf("\n--- Vezes que cada item esgotou, por filial ---\n");
    printf("%-35s", "Produto");
    for (j = 0; j < NUM_FILIAIS; j++) {
        printf(" %11s", FILIAIS[j]);
    }
    printf("\n");
    for (i = 0; i < qtdProdutos; i++) {
        printf("%-35.35s", produtos[i].nome);
        for (j = 0; j < NUM_FILIAIS; j++) {
            printf(" %11d", frequencia[i][j]);
        }
        printf("\n");
    }
    printf("Total de desativacoes registradas: %d\n", total);
}
 
/* ---------- Login e menus ---------- */
 
/* RF01: retorna o indice do usuario autenticado ou -1 apos 3 tentativas */
int autenticar(void) {
    char login[20], senha[20];
    int tentativa, i;
 
    printf("[SIMULACAO ACADEMICA] Usuarios de teste fixos no codigo; "
           "nao representa a seguranca do sistema real.\n");
    for (tentativa = 1; tentativa <= 3; tentativa++) {
        lerTexto("Login: ", login, sizeof(login));
        lerTexto("Senha: ", senha, sizeof(senha));
        for (i = 0; i < NUM_USUARIOS; i++) {
            if (strcmp(usuarios[i].login, login) == 0 &&
                strcmp(usuarios[i].senha, senha) == 0) {
                return i;
            }
        }
        printf("Login ou senha incorretos (%d/3).\n", tentativa);
    }
    return -1;
}
 
int escolherFilial(void) {
    int j, opcao;
    printf("\nFiliais:\n");
    for (j = 0; j < NUM_FILIAIS; j++) {
        printf("%d - %s\n", j + 1, FILIAIS[j]);
    }
    do {
        opcao = lerInteiro("Escolha a filial: ");
    } while (opcao < 1 || opcao > NUM_FILIAIS);
    return opcao - 1;
}
 
void menuAdmin(const char *login) {
    int opcao;
    do {
        printf("\n--- Painel do Administrador (matriz) ---\n");
        printf("1 - Cadastrar produto\n");
        printf("2 - Listar produtos e disponibilidade\n");
        printf("3 - Relatorio de indisponibilidade (agora)\n");
        printf("4 - Relatorio de frequencia de esgotamento\n");
        printf("0 - Sair\n");
        opcao = lerInteiro("Opcao: ");
        switch (opcao) {
        case 1:
            cadastrarProduto(login);
            break;
        case 2:
            listarTodos();
            break;
        case 3:
            relatorioIndisponibilidade();
            break;
        case 4:
            relatorioFrequencia();
            break;
        case 0:
            break;
        default:
            printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}
 
void menuGerente(int filial, const char *login) {
    int opcao;
    do {
        printf("\n--- Painel do Gerente - %s ---\n", FILIAIS[filial]);
        printf("1 - Ver cardapio da filial\n");
        printf("2 - Ativar/desativar produto\n");
        printf("0 - Sair\n");
        opcao = lerInteiro("Opcao: ");
        switch (opcao) {
        case 1:
            exibirCardapio(filial, 0, "");
            break;
        case 2:
            alterarDisponibilidade(filial, login);
            break;
        case 0:
            break;
        default:
            printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}
 
int main(void) {
    int opcao, indice, filialCliente, carga;
    char filtro[TAM_ALERGENOS];
 
    carga = carregarDados();
    if (carga == -1) {
        printf("Erro: nao foi possivel ler %s (invalido ou bloqueado). "
               "Corrija ou apague o arquivo.\n", ARQ_DADOS);
        return 1;
    }
    if (carga == -2) {
        printf("Aviso: %s ausente e %s encontrado (gravacao interrompida, "
               "pode estar incompleto). Confira o arquivo antes de renomea-lo "
               "para %s, ou apague-o para comecar do zero.\n",
               ARQ_DADOS, ARQ_DADOS_TMP, ARQ_DADOS);
        return 1;
    }
    if (carga == -3) {
        printf("Aviso: arquivo %s encontrado: a ultima alteracao nao terminou.\n"
               "Os arquivos %s e %s podem nao estar de acordo.\n",
               ARQ_PENDENCIA, ARQ_DADOS, ARQ_HISTORICO);
        mostrarPendencia();
        printf("Confira os dois arquivos (a ultima linha do historico) e depois "
               "apague o arquivo %s.\n", ARQ_PENDENCIA);
        return 1;
    }
    if (carga == 0) {
        carregarExemplo(); /* primeira execucao */
    }
 
    do {
        printf("\n===== SABOR & CIA - CARDAPIO DIGITAL =====\n");
        printf("1 - Sou cliente (ver cardapio)\n");
        printf("2 - Acesso interno (login)\n");
        printf("0 - Encerrar\n");
        opcao = lerInteiro("Opcao: ");
 
        if (opcao == 1) {
            filialCliente = escolherFilial();
            lerTexto("Filtrar por alergeno (enter para ver tudo): ", filtro,
                     sizeof(filtro));
            exibirCardapio(filialCliente, 1, filtro);
        } else if (opcao == 2) {
            indice = autenticar();
            if (indice == -1) {
                printf("Acesso negado.\n");
            } else if (usuarios[indice].perfil == PERFIL_ADMIN) {
                menuAdmin(usuarios[indice].login);
            } else {
                menuGerente(usuarios[indice].filial, usuarios[indice].login);
            }
        } else if (opcao != 0) {
            printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
 
    printf("Sistema encerrado.\n");
    return 0;
}
