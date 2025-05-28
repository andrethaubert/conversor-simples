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
    """Organiza os campos em seções com base em prefixos ou padrões, preservando a ordem original."""
    secoes = {}
    secoes_ordem = []  # Lista para manter a ordem das seções
    
    # Padrão para identificar seções nos nomes dos campos
    # Exemplo: dados_projeto_nome, dados_cliente_email, etc.
    padrao = r'^([a-zA-Z]+)_([a-zA-Z]+)_(.+)$'
    
    for campo in campos:
        match = re.match(padrao, campo)
        if match:
            # Se o campo segue o padrão, extrair a seção
            secao = f"{match.group(1)}_{match.group(2)}"
            nome_campo = match.group(3)
            
            if secao not in secoes:
                secoes[secao] = []
                secoes_ordem.append(secao)  # Registra a ordem em que a seção apareceu pela primeira vez
            
            secoes[secao].append({
                'id': campo,
                'nome': nome_campo.replace('_', ' ').title()
            })
        else:
            # Se não segue o padrão, colocar em "Outros"
            if "Outros" not in secoes:
                secoes["Outros"] = []
                secoes_ordem.append("Outros")  # Adiciona "Outros" à lista de ordem
            
            secoes["Outros"].append({
                'id': campo,
                'nome': campo.replace('_', ' ').title()
            })
    
    # Formatar nomes das seções para exibição, preservando a ordem
    secoes_formatadas = {}
    for secao in secoes_ordem:  # Usa a lista de ordem em vez de iterar pelo dicionário
        nome_secao = secao.replace('_', ' ').title()
        secoes_formatadas[nome_secao] = secoes[secao]
    
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
                    
                # Extrair o nome do campo
                campo = text[start_idx+2:end_idx].strip()
                if campo and campo not in campos_ordenados:
                    campos_ordenados.append(campo)
                    
                start_idx = end_idx + 2
    
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

# Modificar a parte final do arquivo
if __name__ == '__main__':
    # Usar variáveis de ambiente para configuração em produção
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)