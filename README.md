# 📊 Portal de Relatórios MUMIX

Bem-vindo ao **Portal de Relatórios MUMIX**! Este sistema foi desenvolvido para consolidar, analisar e apresentar de forma clara e visual as principais informações financeiras, operacionais e de recursos humanos das empresas do grupo.

O portal é dividido em seções estratégicas, permitindo que a diretoria e os departamentos tomem decisões baseadas em dados atualizados.

<!-- --- -->
<!-- 
## 🔑 Como Acessar o Portal

Para garantir a segurança dos dados corporativos, o acesso é restrito:

1. **Tela de Login**: Ao abrir o sistema, insira seu **E-mail** e **Senha** cadastrados para acessar.
2. **Navegação**: Após o login, você verá o menu de relatórios na barra lateral ou no topo (dependendo do dispositivo), dividido de acordo com a sua área de permissão.
3. **Encerrar Sessão**: Para sair do sistema com segurança, clique no botão **"Sair do Sistema"** na barra lateral. -->

---

## 📈 Funcionalidades e Painéis Disponíveis

O sistema está estruturado em duas grandes áreas de negócio:

### 💼 1. Diretoria (Painéis Financeiros e Operacionais)

Esta seção concentra os relatórios mais importantes para a análise de desempenho do grupo:

#### 💵 Faturamento
* **Consolidação de Dados**: Permite carregar um ou mais arquivos de relatório (formatos de planilha Excel) para processamento conjunto.
* **Validação Automática**:
  * **Empresa Única/Dupla**: O sistema valida se os arquivos enviados pertencem a no máximo duas empresas distintas. Caso contrário, exibe um erro de segurança para evitar misturar dados incorretos.
  * **Filtro de Notas**: Identifica e avisa sobre lojas que não pertencem aos códigos padrões (como `010` ou `031`) e filtra notas fiscais pendentes para garantir a precisão dos cálculos.
* **Indicadores de Desempenho**: Apresenta gráficos interativos de faturamento diário, progresso em relação à meta mensal e cálculos de dias úteis específicos para cada empresa.

#### 📊 CMV (Custo de Mercadorias Vendidas)
* Apresenta relatórios detalhados sobre a relação entre o custo de aquisição de mercadorias e a receita gerada pelas vendas, ajudando a monitorar a margem bruta de lucro de cada filial.

#### 📉 Apresentação de Resultados (AR)
* Visualização completa do desempenho financeiro das unidades.
* Mapeia os dados brutos de filiais para seus nomes conhecidos (como *Abilio Machado*, *Eldorado*, *Lagoa Santa*, *Venda Nova*, entre outras).
* Analisa diferentes tipos de movimentações financeiras e operacionais (Compras, Vendas, Entradas, Saídas, Avarias, Inventários).

#### 🔄 Devoluções Detalhado
* Painel gráfico focado na análise de mercadorias devolvidas, permitindo identificar padrões, motivos de devoluções frequentes e seu impacto financeiro nas lojas.

---

### 👥 2. RH / DP (Recursos Humanos e Departamento Pessoal)

Área dedicada à gestão interna de pessoas:

#### 🧑‍🤝‍🧑 Gestão Colaboradores
* Interface exclusiva para acompanhamento de dados dos funcionários, controle de equipe e suporte a processos internos de Departamento Pessoal.

---

## 💡 Dicas de Uso

* **Filtros Dinâmicos**: A maioria dos gráficos e tabelas permite passar o cursor do mouse por cima para visualizar valores detalhados (Dicas de Ferramenta/Tooltips).
* **Download de Dados**: Onde houver tabelas de dados visíveis na tela, você pode exportar as informações clicando no ícone do canto superior direito da tabela (opção de baixar como planilha).
* **Atualizações**: Sempre que carregar novas planilhas, aguarde a barra de progresso ("Processando arquivos...") finalizar para que todos os indicadores sejam atualizados simultaneamente.