# QuadroLocal — Gerenciador de Tarefas Kanban

Aplicação web de gerenciamento de tarefas para equipes em uma rede local (LAN), desenvolvida com Python, Flask, SQLite, HTML, CSS e JavaScript.

## Funcionalidades

- Quadro Kanban com as colunas **A Fazer**, **Em Andamento** e **Concluído**.
- Arrastar e soltar cartões entre colunas.
- Cadastro, edição e exclusão de tarefas.
- Prioridades: Baixa, Média, Alta e Urgente.
- Prazo e responsável por tarefa.
- Login individual e senha armazenada com hash.
- Perfil de administrador e usuário comum.
- Administrador pode cadastrar e desativar contas.
- Atualização automática do quadro a cada 15 segundos quando há alterações feitas por outros usuários.
- Banco SQLite compartilhado pelo servidor.

## Requisitos

- Windows 10/11, Linux ou macOS.
- Python 3.10 ou superior.
- Navegador atualizado.
- Computadores conectados à mesma rede local.

## 1. Baixar e extrair

Extraia a pasta do projeto em um local permanente no computador que será o servidor, por exemplo:

`C:\Projetos\kanban_rede_local`

O computador servidor deve permanecer ligado enquanto os demais usuários acessarem o sistema.

## 2. Criar ambiente virtual

Abra o terminal na pasta do projeto e execute:

```bash
python -m venv .venv
```

Ative o ambiente no Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

No Prompt de Comando:

```cmd
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

## 3. Instalar dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Iniciar o servidor

```bash
python app.py
```

O Flask ficará disponível na porta `5000`, escutando em `0.0.0.0` para aceitar conexões da rede local.

No próprio servidor, abra:

`http://127.0.0.1:5000`

### Primeiro acesso

A aplicação cria automaticamente a conta inicial:

| Campo | Valor inicial |
|---|---|
| Usuário | `admin` |
| Senha | `Admin123!` |
| Perfil | Administrador |

**Importante:** altere a senha inicial antes de colocar o sistema em uso real. A versão inicial oferece gerenciamento de usuários, mas não inclui tela de alteração de senha. Para o primeiro uso, altere a senha do administrador diretamente com o procedimento abaixo, com o servidor parado.

Abra um terminal com o ambiente virtual ativado e execute:

```bash
python -c "from app import app, db, User; from werkzeug.security import generate_password_hash; app.app_context().push(); u=User.query.filter_by(username='admin').first(); u.password_hash=generate_password_hash('SuaSenhaForteAqui'); db.session.commit(); print('Senha alterada')"
```

Substitua `SuaSenhaForteAqui` por uma senha forte. Não compartilhe a senha de administrador com os demais usuários.

## 5. Acessar de outros computadores

1. No computador servidor, abra o Prompt de Comando.
2. Execute `ipconfig`.
3. Localize o **Endereço IPv4** do adaptador conectado à rede local. Exemplo: `192.168.1.25`.
4. Nos outros computadores ou celulares conectados à mesma rede, abra:

`http://192.168.1.25:5000`

Troque o IP de exemplo pelo IPv4 real do computador servidor.

### Firewall do Windows

Na primeira execução, o Windows pode solicitar permissão de acesso ao Python. Permita o acesso em redes privadas.

Se necessário, crie uma regra de entrada no Firewall do Windows para TCP na porta `5000`, limitada ao perfil **Privado**. Não exponha essa porta diretamente à internet.

## 6. Cadastrar os usuários

1. Entre com a conta de administrador.
2. Clique em **Usuários** no menu superior.
3. Preencha nome completo, nome de usuário, senha inicial e perfil.
4. Clique em **Cadastrar usuário**.
5. Compartilhe as credenciais iniciais individualmente com cada integrante.

O perfil **Usuário** pode criar e editar tarefas e movimentá-las no quadro. Um usuário comum só pode excluir tarefas que ele próprio criou. O perfil **Administrador** pode excluir qualquer tarefa e administrar contas.

## 7. Como usar o Kanban

- **Nova tarefa:** clique no botão correspondente e preencha os campos.
- **Editar:** clique nos três pontos do cartão.
- **Mover:** arraste o cartão para outra coluna.
- **Buscar:** use o campo de busca acima do quadro.
- **Excluir:** use a opção Excluir no rodapé do cartão.

As tarefas são compartilhadas: todos os usuários autenticados consultam o mesmo banco de dados do servidor.

## Estrutura do projeto

```text
kanban_rede_local/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── kanban.db              # criado automaticamente na primeira execução
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── board.html
│   ├── users.html
│   └── error.html
└── static/
    ├── app.js
    └── style.css
```

## Arquitetura resumida

```text
Computador 1 ─┐
Computador 2 ─┼── Navegador ── Rede local ── Servidor Flask ── SQLite
Celular      ─┘
```

O Flask centraliza as requisições e o arquivo `kanban.db` fica no computador servidor. **Não coloque o arquivo SQLite em uma pasta de rede compartilhada para que cada computador abra diretamente**: todos devem acessar a aplicação pelo navegador, e somente o servidor deve acessar o banco.

## Backup

Para fazer backup:

1. Pare o servidor (`Ctrl + C` no terminal).
2. Copie o arquivo `kanban.db` para uma pasta segura.
3. Inicie o servidor novamente com `python app.py`.

Faça backups periódicos. O arquivo do banco contém contas e tarefas da equipe.

## Segurança e limitações

- Use uma senha forte para o administrador e para todos os usuários.
- Defina uma `SECRET_KEY` própria no ambiente antes de uso prolongado.
- Mantenha o servidor e as dependências atualizados.
- Restrinja a porta 5000 à rede privada.
- Esta versão é adequada para uso e aprendizado em rede local, mas não foi submetida a auditoria de segurança.
- A atualização entre usuários é feita por consulta periódica (15 segundos), não por WebSocket em tempo real.
- A aplicação usa SQLite; para equipes grandes ou alto volume de acessos simultâneos, considere PostgreSQL.
- Não há recuperação de senha, anexos, comentários ou histórico de auditoria nesta versão.

## Executar com chave secreta definida

PowerShell:

```powershell
$env:SECRET_KEY="coloque-uma-chave-aleatoria-longa"
python app.py
```

Para definir também a senha do administrador na primeira criação do banco:

```powershell
$env:ADMIN_PASSWORD="uma-senha-forte"
python app.py
```

A variável `ADMIN_PASSWORD` só é usada quando a conta inicial é criada pela primeira vez. Alterá-la depois não troca a senha de uma conta já existente.

## Licença

Projeto de estudo. Você pode adaptar e evoluir o código conforme as necessidades da equipe.
