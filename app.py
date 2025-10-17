from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
# Importa db.func para podermos usar funções de soma do SQL
from sqlalchemy import func

# --- 1. CONFIGURAÇÃO INICIAL DA APLICAÇÃO ---
app = Flask(__name__)

# ### CORREÇÃO AQUI ###
# A linha 'basedir' DEVE vir antes de ser usada.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ciaei.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'minha-chave-secreta-muito-dificil'  # O 'flash' precisa disso

# Inicializa o Banco de Dados
db = SQLAlchemy(app)

# --- 2. CONFIGURAÇÃO DO ADMIN ---
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

admin = Admin(app, name='Painel do Teatro', template_mode='bootstrap4')


# --- 3. MODELOS DO BANCO DE DADOS ---

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    horarios = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(50), nullable=False, default='wip.jpg')
    # Adiciona a coluna de capacidade máxima de ingressos
    capacidade = db.Column(db.Integer, nullable=False, default=100)  # Valor padrão de 100

    reservas = db.relationship('Reserva', backref='evento', lazy=True)

    def __str__(self):
        return self.titulo


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    email_cliente = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)

    def __str__(self):
        return self.nome_cliente


# --- 4. ADICIONA OS MODELOS AO PAINEL DE ADMIN ---
admin.add_view(ModelView(Evento, db.session, name='Eventos'))
admin.add_view(ModelView(Reserva, db.session, name='Reservas'))


# --- 5. ROTAS (PÁGINAS) DO SITE ---

@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/eventos')
def eventos():
    todos_eventos = Evento.query.all()
    return render_template('eventos.html', eventos=todos_eventos)


@app.route('/informacoes')
def informacoes():
    return render_template('informacoes.html')


@app.route('/bilheteria')
def bilheteria():
    todos_eventos = Evento.query.all()
    return render_template('bilheteria.html', eventos=todos_eventos)


@app.route('/evento/<int:evento_id>')
def detalhe_evento(evento_id):
    evento_encontrado = Evento.query.get_or_404(evento_id)
    return render_template('evento_detalhe.html', evento=evento_encontrado)


@app.route('/reservar', methods=['POST'])
def processar_reserva():
    # 1. Pega os dados do formulário
    nome = request.form['nome']
    email = request.form['email']
    quantidade = int(request.form['quantidade'])
    evento_id = int(request.form['evento_id'])

    # 2. Busca o evento no banco de dados
    evento_reservado = Evento.query.get_or_404(evento_id)

    # 3. Calcula quantos ingressos já foram vendidos
    ingressos_vendidos_query = db.session.query(
        func.sum(Reserva.quantidade)
    ).filter(
        Reserva.evento_id == evento_id
    )
    ingressos_ja_vendidos = ingressos_vendidos_query.scalar() or 0  # 'or 0' caso não haja nenhuma reserva (None)

    # 4. Verifica se há capacidade
    if ingressos_ja_vendidos + quantidade > evento_reservado.capacidade:
        lugares_restantes = evento_reservado.capacidade - ingressos_ja_vendidos

        if lugares_restantes <= 0:
            flash(f'Desculpe, os ingressos para "{evento_reservado.titulo}" estão esgotados.', 'error')
        else:
            flash(f'Desculpe, não há ingressos suficientes. Restam apenas {lugares_restantes} lugares.', 'error')

        return redirect(url_for('detalhe_evento', evento_id=evento_id))

    # 5. Se houver lugar, processa a reserva normalmente
    nova_reserva = Reserva(
        nome_cliente=nome,
        email_cliente=email,
        quantidade=quantidade,
        evento_id=evento_id
    )
    db.session.add(nova_reserva)
    db.session.commit()

    return render_template('reserva_confirmada.html',
                           nome=nome,
                           email=email,
                           quantidade=quantidade,
                           titulo_evento=evento_reservado.titulo)


# Rota para criação do banco
@app.route('/criar_banco_de_dados_agora')
def criar_banco_de_dados_agora():
    try:
        with app.app_context():
            db.create_all()
            if Evento.query.count() == 0:
                # Adiciona eventos com uma capacidade específica
                evento1 = Evento(titulo="Concerto Sinfônico — Noite das Estrelas", horarios="19:00 • 21:30",
                                 capacidade=150)
                evento2 = Evento(titulo="Peça: A Janela", horarios="Horário: 18:00", capacidade=80)
                evento3 = Evento(titulo="Stand-up Comédia: Rir é Arte", horarios="Horários: 20:00 • 22:00",
                                 capacidade=200)
                db.session.add(evento1)
                db.session.add(evento2)
                db.session.add(evento3)
                db.session.commit()
                return "<h1>Sucesso!</h1><p>O banco de dados (v2 com capacidade) foi criado.</p><a href='/admin'>Ir para o Admin</a>"
            else:
                return "<h1>Aviso</h1><p>O banco de dados já existe.</p><a href='/admin'>Ir para o Admin</a>"
    except Exception as e:
        return f"<h1>Erro ao criar banco de dados:</h1><p>{e}</p>"


# --- 6. INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)
