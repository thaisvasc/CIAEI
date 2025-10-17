from flask import Flask, render_template, request
# Importa o SQLAlchemy para interagir com o banco de dados
from flask_sqlalchemy import SQLAlchemy
import os

# --- 1. CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
app = Flask(__name__)

# Configuração do Banco de Dados SQLite
# Pega o caminho absoluto do diretório onde o app.py está
basedir = os.path.abspath(os.path.dirname(__file__))
# Define o local do arquivo do banco de dados (será criado na mesma pasta do projeto)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ciaei.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa warnings desnecessários

# Inicializa a extensão do banco de dados com as configurações do nosso app
db = SQLAlchemy(app)


# --- 2. MODELOS DO BANCO DE DADOS ---
# Cada classe aqui representa uma tabela no nosso banco de dados.

class Evento(db.Model):
    """Modelo para a tabela 'evento'."""
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    horarios = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(50), nullable=False, default='wip.jpg')

    # Este campo cria uma relação com a tabela Reserva.
    # Ele permite acessar todas as reservas de um evento facilmente (ex: evento.reservas).
    reservas = db.relationship('Reserva', backref='evento', lazy=True)

class Reserva(db.Model):
    """Modelo para a tabela 'reserva'."""
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    email_cliente = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    
    # Chave Estrangeira: Este campo liga cada reserva a um evento específico.
    # O valor aqui deve ser um 'id' que existe na tabela 'evento'.
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)


# --- 3. ROTAS (PÁGINAS) DO SITE ---
# As funções abaixo são executadas quando um usuário acessa uma URL.

@app.route('/')
def inicio():
    """Rota para a página inicial."""
    return render_template('index.html')

@app.route('/eventos')
def eventos():
    """Rota para a página de eventos."""
    # Busca TODOS os eventos da tabela Evento no banco de dados.
    todos_eventos = Evento.query.all()
    # Envia a lista de eventos para o template renderizar.
    return render_template('eventos.html', eventos=todos_eventos)

@app.route('/informacoes')
def informacoes():
    """Rota para a página de informações."""
    return render_template('informacoes.html')

@app.route('/bilheteria')
def bilheteria():
    """Rota para a página da bilheteria."""
    todos_eventos = Evento.query.all()
    return render_template('bilheteria.html', eventos=todos_eventos)

@app.route('/evento/<int:evento_id>')
def detalhe_evento(evento_id):
    """Rota para a página de detalhes de um evento específico."""
    # Busca um único evento pelo seu 'id'. Se não encontrar, retorna um erro 404 (Not Found).
    evento_encontrado = Evento.query.get_or_404(evento_id)
    return render_template('evento_detalhe.html', evento=evento_encontrado)

@app.route('/reservar', methods=['POST'])
def processar_reserva():
    """Rota que processa os dados do formulário de reserva."""
    # Pega os dados enviados pelo formulário HTML via método POST.
    nome = request.form['nome']
    email = request.form['email']
    quantidade = int(request.form['quantidade'])
    evento_id = int(request.form['evento_id'])

    # Busca o evento correspondente para obter o título.
    evento_reservado = Evento.query.get_or_404(evento_id)
    
    # Cria um novo objeto Reserva com os dados do formulário.
    nova_reserva = Reserva(
        nome_cliente=nome, 
        email_cliente=email, 
        quantidade=quantidade, 
        evento_id=evento_id
    )

    # Adiciona a nova reserva à sessão (área de preparação).
    db.session.add(nova_reserva)
    # Confirma e salva a reserva no banco de dados.
    db.session.commit()

    # Renderiza a página de confirmação, enviando os dados para exibição.
    return render_template('reserva_confirmada.html', 
                           nome=nome, 
                           email=email, 
                           quantidade=quantidade, 
                           titulo_evento=evento_reservado.titulo)


# --- ROTA TEMPORÁRIA PARA CRIAR O BANCO DE DADOS ---
# Visite esta rota no navegador UMA VEZ para criar tudo.
@app.route('/criar_banco_de_dados_agora')
def criar_banco_de_dados_agora():
    """
    Esta é uma rota secreta para inicializar o banco de dados.
    Visite /criar_banco_de_dados_agora no seu navegador UMA VEZ.
    """
    try:
        # Entra no contexto do app para poder mexer no db
        with app.app_context():
            # 1. Cria todas as tabelas (Evento e Reserva)
            db.create_all()

            # 2. Verifica se a tabela de eventos está vazia
            if Evento.query.count() == 0:
                # 3. Cria os eventos iniciais
                evento1 = Evento(titulo="Concerto Sinfônico — Noite das Estrelas", horarios="19:00 • 21:30")
                evento2 = Evento(titulo="Peça: A Janela", horarios="Horário: 18:00")
                evento3 = Evento(titulo="Stand-up Comédia: Rir é Arte", horarios="Horários: 20:00 • 22:00")

                # 4. Adiciona os eventos na "área de preparação"
                db.session.add(evento1)
                db.session.add(evento2)
                db.session.add(evento3)

                # 5. Salva tudo no banco de dados
                db.session.commit()
                return "<h1>Sucesso!</h1><p>O banco de dados e as tabelas foram criados e os eventos iniciais foram adicionados.</p><a href='/'>Voltar para o site</a>"
            else:
                return "<h1>Aviso</h1><p>O banco de dados já existe e contém dados. Nenhuma ação foi tomada.</p><a href='/'>Voltar para o site</a>"
    except Exception as e:
        return f"<h1>Erro ao criar banco de dados:</h1><p>{e}</p>"


# (Abaixo desta linha, deve estar seu código 'if __name__ == ...')
# --- 4. INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Roda a aplicação em modo de debug, que reinicia automaticamente após mudanças.
    app.run(debug=True)
