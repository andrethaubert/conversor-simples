from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
from docxtpl import DocxTemplate
import os
import json
import re
from werkzeug.utils import secure_filename
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import certifi
import ssl

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['ALLOWED_EXTENSIONS'] = {'docx'}
app.secret_key = os.getenv('SECRET_KEY', 'chave_secreta_padrao')

# Configuração do MongoDB
mongo_uri = os.getenv('MONGODB_URI')
if not mongo_uri:
    raise ValueError("A variável de ambiente MONGODB_URI não está definida. Por favor, configure-a no seu ambiente de deploy (Render, Heroku, etc.).")

# Criar um contexto SSL que usa os certificados do certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

client = MongoClient(mongo_uri, tls=True, tlsContext=ssl_context)
db = client['orcamentos_db']
orcamentos_collection = db['orcamentos']

for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/novo-orcamento')
def novo_orcamento():
    # Limpar qualquer sessão anterior
    session.pop('orcamento_id', None)
    return render_template('index.html')

@app.route('/historico')
def historico():
    # Buscar todos os orçamentos salvos no MongoDB
    orcamentos = list(orcamentos_collection.find().sort('data_criacao', -1))
    
    # Formatar a data para exibição
    for orcamento in orcamentos:
        if 'data_criacao' in orcamento:
            orcamento['data_criacao'] = orcamento['data_criacao'].strftime('%d/%m/%Y %H:%M')
    
    return render_template('historico.html', orcamentos=orcamentos)

def organizar_campos_por_secao(campos):
    """Organiza os campos em seções e subseções com base em prefixos ou padrões, preservando a ordem original."""
    secoes = {}
    secoes_ordem = []  # Lista para manter a ordem das seções
    
    # Imprimir campos para debug
    print("Campos recebidos:", campos)
    
    for campo in campos:
        # Garantir que o campo não tenha espaços extras
        campo_limpo = campo.strip()
        print(f"Processando campo: '{campo_limpo}'")
        
        # Dividir o campo em partes usando underscore
        partes = campo_limpo.split('_')
        print(f"Partes do campo: {partes}")
        
        if len(partes) >= 3:
            # Se temos pelo menos 3 partes (secao_subsecao_campo)
            secao_principal = partes[0]
            subsecao = partes[1]
            nome_campo = '_'.join(partes[2:])  # Juntar o resto como nome do campo
            
            print(f"Partes encontradas: secao='{secao_principal}', subsecao='{subsecao}', campo='{nome_campo}'")
            
            # Verificar se a seção já existe
            if secao_principal not in secoes:
                secoes[secao_principal] = {
                    'campos': [],
                    'subsecoes': {}
                }
                secoes_ordem.append(secao_principal)  # Registra a ordem em que a seção apareceu pela primeira vez
                print(f"Nova seção criada: '{secao_principal}'")
            
            # Adicionar à subseção apropriada
            if subsecao not in secoes[secao_principal]['subsecoes']:
                secoes[secao_principal]['subsecoes'][subsecao] = []
                print(f"Nova subseção criada: '{subsecao}' na seção '{secao_principal}'")
            
            # Adicionar o campo à subseção
            campo_info = {
                'id': campo_limpo,
                'nome': nome_campo.replace('_', ' ').title()
            }
            secoes[secao_principal]['subsecoes'][subsecao].append(campo_info)
            print(f"Campo '{campo_limpo}' adicionado à seção '{secao_principal}', subseção '{subsecao}'")
        else:
            print(f"Formato inválido para: '{campo_limpo}', adicionando a 'Outros'")
            # Se não tem o formato esperado, colocar em "Outros"
            if "Outros" not in secoes:
                secoes["Outros"] = {
                    'campos': [],
                    'subsecoes': {}
                }
                secoes_ordem.append("Outros")  # Adiciona "Outros" à lista de ordem
                print("Seção 'Outros' criada")
            
            # Adicionar o campo à seção "Outros"
            campo_info = {
                'id': campo_limpo,
                'nome': campo_limpo.replace('_', ' ').title()
            }
            secoes["Outros"]['campos'].append(campo_info)
            print(f"Campo '{campo_limpo}' adicionado à seção 'Outros'")
    
    # Formatar nomes das seções para exibição, preservando a ordem
    secoes_formatadas = {}
    for secao in secoes_ordem:  # Usa a lista de ordem em vez de iterar pelo dicionário
        # Função auxiliar para formatar nomes mantendo números
        def formatar_nome(nome):
            # Primeiro, separar letras e números (ex: 'tanque1' -> 'tanque 1')
            nome_formatado = ''
            for i, char in enumerate(nome):
                if i > 0 and char.isdigit() and nome[i-1].isalpha():
                    nome_formatado += ' ' + char
                else:
                    nome_formatado += char
            # Depois, substituir underscores por espaços e capitalizar
            return nome_formatado.replace('_', ' ').title()
        
        # Formatar o nome da seção para exibição
        nome_secao = formatar_nome(secao)
        print(f"Formatando seção '{secao}' como '{nome_secao}'")
        
        # Formatar nomes das subseções
        subsecoes_formatadas = {}
        for subsecao, campos in secoes[secao]['subsecoes'].items():
            # Formatar o nome da subseção para exibição
            nome_subsecao = formatar_nome(subsecao)
            subsecoes_formatadas[nome_subsecao] = campos
            print(f"  Formatando subseção '{subsecao}' como '{nome_subsecao}' com {len(campos)} campos")
        
        secoes_formatadas[nome_secao] = {
            'campos': secoes[secao]['campos'],
            'subsecoes': subsecoes_formatadas
        }
    
    # Imprimir estrutura final para debug
    print("\nEstrutura final das seções:")
    for secao, info in secoes_formatadas.items():
        print(f"Seção: '{secao}' com {len(info['campos'])} campos principais e {len(info['subsecoes'])} subseções")
        for subsecao, campos in info['subsecoes'].items():
            print(f"  Subseção: '{subsecao}' com {len(campos)} campos")
            for campo in campos:
                print(f"    Campo: id='{campo['id']}', nome='{campo['nome']}'")
    
    return secoes_formatadas
    
    # Formatar nomes das seções para exibição, preservando a ordem
    secoes_formatadas = {}
    for secao in secoes_ordem:  # Usa a lista de ordem em vez de iterar pelo dicionário
        # Formatar o nome da seção para exibição, mantendo números
        # Exemplo: 'tanque1' -> 'Tanque 1'
        nome_secao = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', secao)
        nome_secao = nome_secao.replace('_', ' ').title()
        
        # Formatar nomes das subseções
        subsecoes_formatadas = {}
        for subsecao, campos in secoes[secao]['subsecoes'].items():
            # Formatar o nome da subseção para exibição, mantendo números
            # Exemplo: 'processo1' -> 'Processo 1'
            nome_subsecao = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', subsecao)
            nome_subsecao = nome_subsecao.replace('_', ' ').title()
            subsecoes_formatadas[nome_subsecao] = campos
        
        secoes_formatadas[nome_secao] = {
            'campos': secoes[secao]['campos'],
            'subsecoes': subsecoes_formatadas
        }
    
    return secoes_formatadas

def extrair_campos_em_ordem(docx_path):
    """Extrai campos do template na ordem em que aparecem no documento."""
    campos_ordenados = []
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    
    # Abrir o arquivo .docx como um arquivo zip
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        # Extrair o conteúdo do documento principal
        content = zip_ref.read('word/document.xml')
        
        # Analisar o XML
        root = ET.fromstring(content)
        
        # Procurar por todos os elementos de texto no documento
        for paragraph in root.findall('.//w:p', namespace):
            text = ''
            for run in paragraph.findall('.//w:r', namespace):
                for t in run.findall('.//w:t', namespace):
                    text += t.text if t.text else ''
            
            # Procurar por marcadores Jinja2 no texto
            start_idx = 0
            while True:
                start_idx = text.find('{{', start_idx)
                if start_idx == -1:
                    break
                    
                end_idx = text.find('}}', start_idx)
                if end_idx == -1:
                    break
                    
                # Extrair o nome do campo e remover apenas espaços no início e fim
                campo = text[start_idx+2:end_idx].strip()
                # Remover espaços extras que possam estar dentro do campo, mas preservar a estrutura
                campo = re.sub(r'\s+', '', campo)
                
                # Imprimir para debug
                print(f"Campo extraído: '{campo}'")
                
                if campo and campo not in campos_ordenados:
                    campos_ordenados.append(campo)
                    
                start_idx = end_idx + 2
    
    # Imprimir todos os campos encontrados para debug
    print("Todos os campos encontrados:", campos_ordenados)
    return campos_ordenados

# Modifique a função upload_template para usar a nova função
@app.route('/upload', methods=['POST'])
def upload_template():
    if 'template' not in request.files:
        return redirect(request.url)
    
    file = request.files['template']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extrair campos do template na ordem em que aparecem
        campos = extrair_campos_em_ordem(filepath)
        
        # Como backup, caso a extração falhe, use o método padrão
        if not campos:
            doc = DocxTemplate(filepath)
            campos = list(doc.get_undeclared_template_variables())
        
        # Organizar campos em seções
        secoes = organizar_campos_por_secao(campos)
        
        return render_template('index.html', 
                              template_name=filename, 
                              secoes=secoes)
    
    return redirect(request.url)

@app.route('/selecionar_secoes', methods=['GET', 'POST'])
def selecionar_secoes():
    if request.method == 'POST':
        template_name = request.form.get('template_name')
        secoes_selecionadas = request.form.getlist('secoes_selecionadas')
        
        # Obter as seções e campos do template na ordem correta
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
        campos = extrair_campos_em_ordem(template_path)
        
        # Como backup, caso a extração falhe
        if not campos:
            doc = DocxTemplate(template_path)
            campos = list(doc.get_undeclared_template_variables())
            
        secoes = organizar_campos_por_secao(campos)
        
        # Salvar as seções selecionadas no MongoDB mesmo sem preencher os campos
        if secoes_selecionadas:
            # Verificar se já existe um orçamento em andamento
            orcamento_id = session.get('orcamento_id')
            
            # Inicializar um contexto vazio para os campos
            context = {}
            
            # Inicializar uma lista vazia para campos dinâmicos
            campos_dinamicos = []
            
            # Preparar dados para salvar
            orcamento_data = {
                'nome': 'Orçamento em andamento',  # Nome temporário
                'numero': 'Temporário',  # Número temporário
                'template_name': template_name,
                'secoes_selecionadas': secoes_selecionadas,
                'context': context,  # Adicionar contexto vazio
                'campos_dinamicos': campos_dinamicos,  # Adicionar campos dinâmicos vazios
                'data_criacao': datetime.now()
            }
            
            # Se estamos atualizando um orçamento existente
            if orcamento_id:
                # Buscar o orçamento existente para preservar dados já preenchidos
                orcamento_existente = orcamentos_collection.find_one({'_id': ObjectId(orcamento_id)})
                if orcamento_existente:
                    # Manter o contexto existente
                    if 'context' in orcamento_existente:
                        orcamento_data['context'] = orcamento_existente.get('context', {})
                    
                    # Manter os campos dinâmicos existentes
                    if 'campos_dinamicos' in orcamento_existente:
                        orcamento_data['campos_dinamicos'] = orcamento_existente.get('campos_dinamicos', [])
                
                # Atualizar o orçamento
                orcamentos_collection.update_one(
                    {'_id': ObjectId(orcamento_id)},
                    {'$set': orcamento_data}
                )
            else:
                # Inserir novo orçamento
                result = orcamentos_collection.insert_one(orcamento_data)
                orcamento_id = str(result.inserted_id)
                session['orcamento_id'] = orcamento_id
            
            print(f"Seções selecionadas salvas no MongoDB: {secoes_selecionadas}")
            print(f"Orçamento salvo com ID: {orcamento_id}")
        
        return render_template('index.html', 
                              template_name=template_name,
                              secoes=secoes,
                              secoes_selecionadas=secoes_selecionadas)
    else:
        template_name = request.args.get('template_name')
        if not template_name:
            return redirect(url_for('index'))
        
        # Obter as seções e campos do template na ordem correta
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
        campos = extrair_campos_em_ordem(template_path)
        
        # Como backup, caso a extração falhe
        if not campos:
            doc = DocxTemplate(template_path)
            campos = list(doc.get_undeclared_template_variables())
            
        secoes = organizar_campos_por_secao(campos)
        
        return render_template('index.html', 
                              template_name=template_name,
                              secoes=secoes)

# Rota para salvar orçamento na etapa de seleção de seções
@app.route('/salvar_orcamento_secoes', methods=['POST'])
def salvar_orcamento_secoes():
    try:
        template_name = request.form.get('template_name')
        secoes_selecionadas = request.form.getlist('secoes_selecionadas')
        
        if not template_name or not secoes_selecionadas:
            return jsonify({'success': False, 'error': 'Template ou seções não fornecidos'})
        
        # Verificar se já existe um orçamento em andamento
        orcamento_id = session.get('orcamento_id')
        
        # Inicializar um contexto vazio para os campos
        context = {}
        
        # Inicializar uma lista vazia para campos dinâmicos
        campos_dinamicos = []
        
        # Preparar dados para salvar
        orcamento_data = {
            'nome': 'Orçamento salvo',  # Nome temporário
            'numero': 'Temporário',  # Número temporário
            'template_name': template_name,
            'secoes_selecionadas': secoes_selecionadas,
            'context': context,  # Adicionar contexto vazio
            'campos_dinamicos': campos_dinamicos,  # Adicionar campos dinâmicos vazios
            'data_criacao': datetime.now()
        }
        
        # Se estamos atualizando um orçamento existente
        if orcamento_id:
            # Buscar o orçamento existente para preservar dados já preenchidos
            orcamento_existente = orcamentos_collection.find_one({'_id': ObjectId(orcamento_id)})
            if orcamento_existente:
                # Manter o contexto existente
                if 'context' in orcamento_existente:
                    orcamento_data['context'] = orcamento_existente.get('context', {})
                
                # Manter os campos dinâmicos existentes
                if 'campos_dinamicos' in orcamento_existente:
                    orcamento_data['campos_dinamicos'] = orcamento_existente.get('campos_dinamicos', [])
            
            # Atualizar o orçamento
            orcamentos_collection.update_one(
                {'_id': ObjectId(orcamento_id)},
                {'$set': orcamento_data}
            )
            print(f"Orçamento atualizado com ID: {orcamento_id}")
        else:
            # Inserir novo orçamento
            result = orcamentos_collection.insert_one(orcamento_data)
            orcamento_id = str(result.inserted_id)
            session['orcamento_id'] = orcamento_id
            print(f"Novo orçamento salvo com ID: {orcamento_id}")
        
        return jsonify({'success': True, 'orcamento_id': orcamento_id})
    except Exception as e:
        print(f"Erro ao salvar orçamento: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Adicionar esta função antes de generate_document
def sanitizar_valor(valor):
    """Sanitiza valores para evitar erros de sintaxe Jinja2"""
    if valor is None:
        return ""
    return str(valor).strip()

# Modificar a parte de processamento de campos em generate_document
@app.route('/generate', methods=['POST'])
def generate_document():
    template_name = request.form.get('template_name')
    if not template_name:
        return redirect(url_for('index'))
    
    # Verificar se estamos continuando um orçamento existente
    orcamento_id = session.get('orcamento_id')
    
    # Obter todos os campos do formulário
    context = {}
    campos_dinamicos_dict = []  # Lista para campos dinâmicos
    campos_dinamicos = request.form.getlist('campos_dinamicos[]')
    secoes_selecionadas = request.form.getlist('secoes_selecionadas')
    
    # Obter nome e número do orçamento, se fornecidos
    nome_orcamento = request.form.get('nome_orcamento', '')
    numero_orcamento = request.form.get('numero_orcamento', '')
    
    # Determinar se devemos salvar o orçamento
    salvar_orcamento = request.form.get('salvar_orcamento') == 'true'
    
    for key, value in request.form.items():
        if key not in ['template_name', 'campos_dinamicos[]', 'salvar_orcamento', 'nome_orcamento', 'numero_orcamento']:
            # Processar nomes de campos dinâmicos
            if key.startswith('dinamico_nome_'):
                continue  # Pular, processaremos junto com os valores
                
            # Sanitizar o valor
            value = sanitizar_valor(value)
            
            # Tente converter valores numéricos para float
            if value.replace('.', '', 1).isdigit():
                try:
                    context[key] = float(value)
                except ValueError:
                    context[key] = value
            else:
                context[key] = value
    
    # Processar campos dinâmicos
    for campo_id in campos_dinamicos:
        nome_campo_key = f'dinamico_nome_{campo_id}'
        if nome_campo_key in request.form and campo_id in request.form:
            nome_campo = sanitizar_valor(request.form[nome_campo_key])
            valor_campo = sanitizar_valor(request.form[campo_id])
            
            if nome_campo:  # Só adicionar se o nome não estiver vazio
                # Criar item para o campo dinâmico
                campo_item = {
                    'nome': nome_campo,
                    'valor': valor_campo
                }
                
                # Converter valor numérico se aplicável
                if valor_campo.replace('.', '', 1).isdigit():
                    try:
                        campo_item['valor'] = float(valor_campo)
                    except ValueError:
                        pass
                
                # Adicionar à lista de campos dinâmicos
                campos_dinamicos_dict.append(campo_item)
                
                # Também adicionar ao contexto principal (para compatibilidade)
                nome_campo_formatado = nome_campo.lower().replace(' ', '_')
                context[nome_campo_formatado] = campo_item['valor']
    
    # Adicionar a lista de campos dinâmicos ao contexto
    context['campos_dinamicos'] = campos_dinamicos_dict
    
    # Gerar documento
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
    doc = DocxTemplate(template_path)
    
    try:
        doc.render(context)
    except AttributeError as e:
        if "'Section' object has no attribute 'part'" in str(e):
            print(f"Erro de seção no documento: {str(e)}")
            return render_template('error.html', 
                                  error="O documento contém seções complexas que não podem ser processadas. "
                                        "Por favor, simplifique o documento removendo seções, cabeçalhos ou "
                                        "rodapés complexos.", 
                                  filename="")
        else:
            print(f"Erro ao renderizar: {str(e)}")
            return render_template('error.html', error=str(e), filename="")
    except Exception as e:
        print(f"Erro ao renderizar: {str(e)}")
        return render_template('error.html', error=str(e), filename="")
    
    output_filename = f"preenchido_{template_name}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    doc.save(output_path)
    
    # Se for para salvar o orçamento, salvar no MongoDB
    if salvar_orcamento and nome_orcamento and numero_orcamento:
        # Preparar dados para salvar
        orcamento_data = {
            'nome': nome_orcamento,
            'numero': numero_orcamento,
            'template_name': template_name,
            'context': context,
            'secoes_selecionadas': secoes_selecionadas,
            'data_criacao': datetime.now()
        }
        
        # Se estamos atualizando um orçamento existente
        if orcamento_id:
            orcamentos_collection.update_one(
                {'_id': ObjectId(orcamento_id)},
                {'$set': orcamento_data}
            )
        else:
            # Inserir novo orçamento
            result = orcamentos_collection.insert_one(orcamento_data)
            orcamento_id = str(result.inserted_id)
            session['orcamento_id'] = orcamento_id
    else:
        # Mesmo que o usuário não tenha escolhido salvar o orçamento completo,
        # vamos salvar as seções selecionadas para que possam ser recuperadas depois
        if orcamento_id:
            # Atualizar apenas as seções selecionadas no orçamento existente
            orcamentos_collection.update_one(
                {'_id': ObjectId(orcamento_id)},
                {'$set': {
                    'secoes_selecionadas': secoes_selecionadas,
                    'context': context
                }}
            )
            print(f"Seções selecionadas atualizadas no MongoDB: {secoes_selecionadas}")
        
    return render_template('success.html', 
                          filename=output_filename,
                          orcamento_salvo=salvar_orcamento,
                          orcamento_id=orcamento_id)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/download-redigido')
def download_redigido():
    # Caminho para o arquivo redigido.docx na pasta certo
    return send_from_directory('certo', 'redigido.docx', as_attachment=True)

@app.route('/continuar-orcamento/<orcamento_id>')
def continuar_orcamento(orcamento_id):
    # Buscar o orçamento no MongoDB
    orcamento = orcamentos_collection.find_one({'_id': ObjectId(orcamento_id)})
    
    if not orcamento:
        return redirect(url_for('historico'))
    
    # Salvar o ID do orçamento na sessão
    session['orcamento_id'] = orcamento_id
    
    # Obter o template e os campos
    template_name = orcamento.get('template_name')
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
    
    # Verificar se o template existe
    if not os.path.exists(template_path):
        return render_template('error.html', 
                              error=f"O template '{template_name}' não foi encontrado. "
                                    "Por favor, faça upload do template novamente.", 
                              filename="")
    
    # Extrair campos do template
    campos = extrair_campos_em_ordem(template_path)
    if not campos:
        doc = DocxTemplate(template_path)
        campos = list(doc.get_undeclared_template_variables())
    
    # Organizar campos em seções
    secoes = organizar_campos_por_secao(campos)
    
    # Obter as seções selecionadas do orçamento salvo
    secoes_selecionadas = orcamento.get('secoes_selecionadas', [])
    
    # Garantir que secoes_selecionadas não seja None
    if secoes_selecionadas is None:
        secoes_selecionadas = []
        print("AVISO: secoes_selecionadas era None, inicializado como lista vazia")
    
    # Obter o contexto (valores dos campos)
    context = orcamento.get('context', {})
    
    # Garantir que context não seja None
    if context is None:
        context = {}
        print("AVISO: context era None, inicializado como dicionário vazio")
    
    # Imprimir informações para debug
    print(f"Continuando orçamento: {orcamento_id}")
    print(f"Template: {template_name}")
    print(f"Seções selecionadas: {secoes_selecionadas}")
    print(f"Contexto: {context}")
    print(f"Seções disponíveis: {list(secoes.keys())}")
    
    # Verificar se as seções selecionadas estão nas seções disponíveis
    # Se não estiverem, pode ser um problema de formatação
    secoes_disponiveis = list(secoes.keys())
    secoes_selecionadas_encontradas = []
    
    # Criar um mapeamento case-insensitive para as seções disponíveis
    mapa_secoes_case_insensitive = {secao.lower(): secao for secao in secoes_disponiveis}
    print(f"Mapa de seções case-insensitive: {mapa_secoes_case_insensitive}")
    
    for secao_selecionada in secoes_selecionadas:
        if secao_selecionada in secoes_disponiveis:
            # Seção encontrada diretamente
            secoes_selecionadas_encontradas.append(secao_selecionada)
            print(f"Seção '{secao_selecionada}' encontrada diretamente")
        elif secao_selecionada.lower() in mapa_secoes_case_insensitive:
            # Seção encontrada por case-insensitive
            secao_correta = mapa_secoes_case_insensitive[secao_selecionada.lower()]
            secoes_selecionadas_encontradas.append(secao_correta)
            print(f"Seção '{secao_selecionada}' encontrada por case-insensitive como '{secao_correta}'")
        else:
            # Seção não encontrada
            print(f"AVISO: Seção '{secao_selecionada}' não encontrada em nenhuma forma")
    
    # MODIFICAÇÃO: Usar todas as seções disponíveis em vez de apenas as selecionadas
    # Isso permitirá que o usuário veja todas as seções do documento, incluindo as não preenchidas
    secoes_selecionadas = secoes_disponiveis
    print(f"Mostrando todas as seções disponíveis: {secoes_selecionadas}")
    
    # Atualizar o orçamento no MongoDB com todas as seções
    orcamentos_collection.update_one(
        {'_id': ObjectId(orcamento_id)},
            {'$set': {'secoes_selecionadas': secoes_selecionadas}}
        )
    print(f"Seções selecionadas atualizadas no MongoDB: {secoes_selecionadas}")
        
    # Extrair campos dinâmicos do contexto ou diretamente do orçamento
    campos_dinamicos = []
    
    # Verificar se há campos dinâmicos no contexto
    if context and 'campos_dinamicos' in context and context['campos_dinamicos'] is not None:
        print(f"Campos dinâmicos encontrados no contexto: {context['campos_dinamicos']}")
        campos_dinamicos = context['campos_dinamicos']
    # Verificar se há campos dinâmicos diretamente no orçamento
    elif 'campos_dinamicos' in orcamento and orcamento['campos_dinamicos'] is not None:
        print(f"Campos dinâmicos encontrados diretamente no orçamento: {orcamento['campos_dinamicos']}")
        campos_dinamicos = orcamento['campos_dinamicos']
    else:
        print("Nenhum campo dinâmico encontrado, inicializando como lista vazia")
    
    # Garantir que campos_dinamicos não seja None
    if campos_dinamicos is None:
        campos_dinamicos = []
        print("AVISO: campos_dinamicos era None, inicializado como lista vazia")
    
    return render_template('index.html', 
                          template_name=template_name,
                          secoes=secoes,
                          secoes_selecionadas=secoes_selecionadas,
                          context=context,
                          orcamento=orcamento,
                          orcamento_id=orcamento_id,
                          campos_dinamicos=campos_dinamicos)

@app.route('/download-orcamento/<orcamento_id>')
def download_orcamento(orcamento_id):
    # Buscar o orçamento no MongoDB
    orcamento = orcamentos_collection.find_one({'_id': ObjectId(orcamento_id)})
    
    if not orcamento:
        return redirect(url_for('historico'))
    
    # Obter o template e o contexto
    template_name = orcamento.get('template_name')
    context = orcamento.get('context', {})
    
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
        
    # Verificar se o template existe
    if not os.path.exists(template_path):
        # Verificar se existe um arquivo com nome similar na pasta de uploads
        uploads_dir = app.config['UPLOAD_FOLDER']
        arquivos_disponiveis = os.listdir(uploads_dir)
        
        # Tentar encontrar um arquivo com nome similar
        for arquivo in arquivos_disponiveis:
            if arquivo.endswith('.docx'):
                template_path = os.path.join(uploads_dir, arquivo)
                print(f"Template original não encontrado. Usando template alternativo: {arquivo}")
                break
        else:
            # Se não encontrar nenhum template alternativo
            return render_template('error.html', 
                                  error=f"O template '{template_name}' não foi encontrado e nenhum template alternativo está disponível. "
                                    "Por favor, faça upload do template novamente.", 
                              filename="")
    
    # Gerar o documento
    doc = DocxTemplate(template_path)
    
    try:
        doc.render(context)
    except Exception as e:
        return render_template('error.html', error=str(e), filename="")
    
    # Nome do arquivo de saída
    output_filename = f"preenchido_{orcamento.get('nome')}_{orcamento.get('numero')}.docx"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    doc.save(output_path)
    
    return send_from_directory(app.config['OUTPUT_FOLDER'], output_filename, as_attachment=True)

@app.route('/excluir-orcamento/<orcamento_id>', methods=['GET', 'POST'])
def excluir_orcamento(orcamento_id):
    try:
        # Imprimir informações para debug
        print(f"Tentando excluir orçamento com ID: {orcamento_id}")
        
        # Excluir o orçamento do MongoDB
        resultado = orcamentos_collection.delete_one({'_id': ObjectId(orcamento_id)})
        print(f"Resultado da exclusão: {resultado.deleted_count} documento(s) excluído(s)")
        
        # Se o orçamento excluído for o que está na sessão, limpar a sessão
        if session.get('orcamento_id') == orcamento_id:
            session.pop('orcamento_id', None)
            print("Sessão limpa após exclusão do orçamento ativo")
        
        # Verificar se a solicitação é AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
            
        return redirect(url_for('historico'))
    except Exception as e:
        print(f"Erro ao excluir orçamento: {str(e)}")
        # Verificar se a solicitação é AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)})
            
        return render_template('error.html', error=f"Erro ao excluir orçamento: {str(e)}", filename="")

# Modificar a parte final do arquivo
if __name__ == '__main__':
    # Usar variáveis de ambiente para configuração em produção
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)