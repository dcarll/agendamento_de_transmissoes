# 🎙️ Sistema de Transmissões DTI/LAB

<p align="center">
  <img src="assets/transmissoes.png" width="150" alt="Logo do Projeto">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flet-0052FF?style=for-the-badge&logo=flet&logoColor=white" alt="Flet">
  <img src="https://img.shields.io/badge/Status-Desenvolvimento-green?style=for-the-badge" alt="Status">
</p>

---

## 📄 Sobre o Projeto

O **Sistema de Transmissões DTI/LAB** é uma aplicação desktop moderna desenvolvida em Python utilizando o framework **Flet**. Ele foi projetado para facilitar o agendamento, monitoramento e gestão de transmissões realizadas pelo Departamento de Tecnologia da Informação (DTI) em ambientes laboratoriais.

O sistema oferece uma interface intuitiva e fluida, com sincronização em tempo real entre diferentes instâncias, garantindo que toda a equipe esteja sempre atualizada.

---

## ✨ Funcionalidades Principais

*   **📊 Dashboard:** Visão geral das transmissões recentes e estatísticas rápidas.
*   **📅 Calendário Inteligente:** Visualização em lista ou grade com filtros avançados por status, período, modalidade e tipo.
*   **📝 Gerenciamento Completo:** Criação, edição e exclusão de transmissões com validação de dados.
*   **⏳ Histórico:** Acesso rápido a todos os eventos passados de forma organizada.
*   **📈 Relatórios:** Geração de relatórios detalhados para análise de produtividade e uso.
*   **🔄 Sincronização em Tempo Real:** Sistema de PubSub integrado que atualiza a interface automaticamente quando mudanças ocorrem.
*   **🌙 Modo Escuro:** Interface otimizada para conforto visual.

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/):** Linguagem base.
- **[Flet](https://flet.dev/):** Framework para interface rica baseada em Flutter.
- **SQLite:** Armazenamento local persistente e eficiente.
- **OpenPyXL:** Manipulação de arquivos Excel para geração de relatórios.

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10 ou superior.
- Git (opcional, para clonar o repositório).

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/dcarll/agendamento_de_transmissoes.git
cd agendamento_de_transmissoes
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python main.py
```

*Ou utilize o arquivo `iniciar.bat` no Windows para inicialização rápida.*

---

## 📁 Estrutura do Projeto

```text
├── assets/             # Ícones e recursos visuais
├── controllers/        # Lógica de negócio e intermediação
├── models/             # Definição das entidades de dados
├── views/              # Interface do usuário (Flet components)
├── services/           # Serviços auxiliares
├── utils/              # Funções utilitárias e helpers
├── main.py             # Ponto de entrada da aplicação
└── app.py              # Configuração principal do app
```

---

<p align="center">
  Desenvolvido por <strong>Dcarll</strong> 🚀
</p>
