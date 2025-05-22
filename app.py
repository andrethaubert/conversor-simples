from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from docxtpl import DocxTemplate
import os
import json
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['ALLOWED_EXTENSIONS'] = {'docx'}

# Criar pastas se não existirem
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

def organizar_campos_por_secao(campos):
    """Organiza os campos em seções com base em prefixos ou padrões."""
    secoes = {}
    
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
            
            secoes[secao].append({
                'id': campo,
                'nome': nome_campo.replace('_', ' ').title()
            })
        else:
            # Se não segue o padrão, colocar em "Outros"
            if "Outros" not in secoes:
                secoes["Outros"] = []
            
            secoes["Outros"].append({
                'id': campo,
                'nome': campo.replace('_', ' ').title()
            })
    
    # Formatar nomes das seções para exibição
    secoes_formatadas = {}
    for secao, campos in secoes.items():
        nome_secao = secao.replace('_', ' ').title()
        secoes_formatadas[nome_secao] = campos
    
    return secoes_formatadas

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
        
        # Extrair campos do template
        doc = DocxTemplate(filepath)
        campos = doc.get_undeclared_template_variables()
        
        # Organizar campos em seções
        secoes = organizar_campos_por_secao(campos)
        
        return render_template('index.html', 
                              template_name=filename, 
                              secoes=secoes)
    
    return redirect(request.url)

@app.route('/generate', methods=['POST'])
def generate_document():
    template_name = request.form.get('template_name')
    if not template_name:
        return redirect(url_for('index'))
    
    # Obter todos os campos do formulário
    context = {}
    for key, value in request.form.items():
        if key != 'template_name':
            context[key] = value
    
    # Gerar documento
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)
    doc = DocxTemplate(template_path)
    doc.render(context)
    
    output_filename = f"preenchido_{template_name}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    doc.save(output_path)
    
    return render_template('success.html', 
                          filename=output_filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)