from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from docxtpl import DocxTemplate
import os
import json
import re
from werkzeug.utils import secure_filename
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['ALLOWED_EXTENSIONS'] = {'docx'}


for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

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
    
    # Obter todos os campos do formulário
    context = {}
    campos_dinamicos_dict = []  # Lista para campos dinâmicos
    campos_dinamicos = request.form.getlist('campos_dinamicos[]')
    
    for key, value in request.form.items():
        if key != 'template_name' and key != 'campos_dinamicos[]':
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
    
    return render_template('success.html', 
                          filename=output_filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/download-redigido')
def download_redigido():
    # Caminho para o arquivo redigido.docx na pasta certo
    return send_from_directory('certo', 'redigido.docx', as_attachment=True)

# Modificar a parte final do arquivo
if __name__ == '__main__':
    # Usar variáveis de ambiente para configuração em produção
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)