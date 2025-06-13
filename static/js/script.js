// Funções auxiliares para melhorar a experiência do usuário
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar validação visual aos campos do formulário
    const inputs = document.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() !== '') {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                // Remover ambas as classes para campos vazios
                this.classList.remove('is-invalid');
                this.classList.remove('is-valid');
            }
        });
        
        // Adicionar efeito de foco
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focus');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focus');
        });
    });
    
    // Adicionar animação ao abrir acordeões
    const accordionButtons = document.querySelectorAll('.accordion-button');
    accordionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const isCollapsed = this.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Animação ao abrir
                setTimeout(() => {
                    const accordionBody = this.parentElement.nextElementSibling;
                    accordionBody.style.animation = 'fadeIn 0.5s ease forwards';
                }, 300);
            }
        });
    });
    
    // Adicionar efeito de hover nos botões
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
    
    // Adicionar animação ao carregar a página
    document.querySelector('.card').classList.add('fade-in');
});

// Adicionar estilos CSS para animações
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    .input-focus {
        transform: translateY(-2px);
        transition: transform 0.3s ease;
    }
`;
document.head.appendChild(style);


// Adicionar interatividade aos cartões de seleção de seções
document.addEventListener('DOMContentLoaded', function() {
    // Tornar o cartão inteiro clicável para selecionar/desselecionar a seção
    const sectionCards = document.querySelectorAll('.section-card');
    sectionCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Evitar clique duplo se o usuário clicar diretamente no checkbox
            if (e.target.type !== 'checkbox') {
                const checkbox = this.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
                
                // Atualizar aparência do cartão
                if (checkbox.checked) {
                    this.classList.add('selected-section');
                } else {
                    this.classList.remove('selected-section');
                }
            }
        });
        
        // Verificar estado inicial
        const checkbox = card.querySelector('input[type="checkbox"]');
        if (checkbox.checked) {
            card.classList.add('selected-section');
        }
    });
    
    // Atualizar aparência quando o checkbox é alterado diretamente
    const checkboxes = document.querySelectorAll('.section-card input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const card = this.closest('.section-card');
            if (this.checked) {
                card.classList.add('selected-section');
            } else {
                card.classList.remove('selected-section');
            }
        });
    });
});

// Adicionar estilo para seções selecionadas
const styleSection = document.createElement('style');
styleSection.textContent = `
    .selected-section {
        border: 2px solid var(--primary-color);
        background-color: rgba(4, 112, 171, 0.05);
    }
    
    .section-card {
        position: relative;
    }
    
    .section-card .form-check {
        margin-bottom: 10px;
    }
`;
document.head.appendChild(styleSection);


// Adicionar ao final do arquivo script.js
// Adicionar ao final do arquivo script.js
document.addEventListener('DOMContentLoaded', function() {
    // Validar formulário antes do envio
    const form = document.querySelector('form[action="/generate"]');
    if (form) {
        form.addEventListener('submit', function(event) {
            // Impedir que a tecla Enter envie o formulário
            document.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }
});

// Gerenciamento de campos dinâmicos
document.addEventListener('DOMContentLoaded', function() {
    // Contador global para IDs únicos
    let campoCounter = 1;
    
    // Adicionar event listeners para os botões de adicionar campo
    const addCampoBtns = document.querySelectorAll('.add-campo-btn');
    addCampoBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const secao = this.getAttribute('data-secao');
            const secaoIndex = this.getAttribute('data-secao-index');
            const camposDinamicosContainer = document.getElementById(`campos-dinamicos-${secaoIndex}`);
            
            // Criar ID único para o campo
            const campoId = `${secao}_dinamico_${campoCounter}`;
            campoCounter++;
            
            // Criar elementos HTML para o novo campo
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6 mb-3 campo-dinamico';
            
            // Criar o HTML interno
            colDiv.innerHTML = `
                <div class="d-flex">
                    <div class="flex-grow-1">
                        <input type="text" class="form-control mb-2" 
                               placeholder="Nome do Campo" 
                               name="dinamico_nome_${campoId}">
                        <div class="input-group">
                            <span class="input-group-text"><i class="bi bi-pencil-fill"></i></span>
                            <input type="text" class="form-control" 
                                   placeholder="Valor" 
                                   id="${campoId}" 
                                   name="${campoId}">
                            <input type="hidden" name="campos_dinamicos[]" value="${campoId}">
                        </div>
                    </div>
                    <button type="button" class="btn btn-outline-danger ms-2 remove-campo-btn" 
                            style="height: 38px; align-self: flex-end;">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            
            // Adicionar o novo campo ao container
            camposDinamicosContainer.appendChild(colDiv);
            
            // Adicionar event listener para o botão de remover
            const removeBtn = colDiv.querySelector('.remove-campo-btn');
            removeBtn.addEventListener('click', function() {
                colDiv.remove();
            });
        });
    });
    
    // Adicionar botões para duplicar seções
    const accordionItems = document.querySelectorAll('.accordion-item');
    accordionItems.forEach((item, index) => {
        // Não adicionar botão de duplicar na última seção
        if (index < accordionItems.length - 1) {
            const headerButton = item.querySelector('.accordion-button');
            const collapseDiv = item.querySelector('.accordion-collapse');
            
            // Criar botão de duplicar seção
            const duplicateBtn = document.createElement('button');
            duplicateBtn.type = 'button';
            duplicateBtn.className = 'btn btn-outline-primary btn-sm duplicate-section-btn mt-3 mb-3';
            duplicateBtn.innerHTML = '<i class="bi bi-files me-2"></i>Duplicar para Seção Abaixo';
            duplicateBtn.setAttribute('data-current-section', index);
            duplicateBtn.setAttribute('data-target-section', index + 1);
            
            // Adicionar botão ao final da seção
            collapseDiv.appendChild(duplicateBtn);
            
            // Adicionar event listener para o botão de duplicar
            duplicateBtn.addEventListener('click', function() {
                const currentSectionIndex = parseInt(this.getAttribute('data-current-section'));
                const targetSectionIndex = parseInt(this.getAttribute('data-target-section'));
                
                // Obter a seção atual e a seção alvo
                const currentSection = accordionItems[currentSectionIndex];
                const targetSection = accordionItems[targetSectionIndex];
                
                // Duplicar campos normais
                const currentInputs = currentSection.querySelectorAll('input[type="text"]:not(.campo-dinamico input)');
                const targetInputs = targetSection.querySelectorAll('input[type="text"]:not(.campo-dinamico input)');
                
                // Copiar valores dos campos normais
                currentInputs.forEach((input, i) => {
                    if (i < targetInputs.length) {
                        targetInputs[i].value = input.value;
                        // Adicionar classe is-valid se o campo tiver valor
                        if (input.value.trim() !== '') {
                            targetInputs[i].classList.add('is-valid');
                        }
                    }
                });
                
                // Duplicar campos dinâmicos
                const currentDinamicos = currentSection.querySelectorAll('.campo-dinamico');
                const targetDinamicosContainer = targetSection.querySelector('[id^="campos-dinamicos-"]');
                
                // Limpar campos dinâmicos existentes na seção alvo
                targetDinamicosContainer.innerHTML = '';
                
                // Copiar campos dinâmicos
                currentDinamicos.forEach(campo => {
                    // Obter valores do campo dinâmico atual
                    const nomeCampo = campo.querySelector('input[name^="dinamico_nome_"]').value;
                    const valorCampo = campo.querySelector('input[id^=""]').value;
                    const campoIdOriginal = campo.querySelector('input[name="campos_dinamicos[]"]').value;
                    
                    // Criar novo ID para o campo duplicado
                    const secaoAlvo = targetSection.querySelector('.accordion-button').getAttribute('data-bs-target').replace('#collapse', '');
                    const secaoNome = targetSection.querySelector('.accordion-button').textContent.trim();
                    const campoId = `${secaoNome.replace(/\s+/g, '_').toLowerCase()}_dinamico_${campoCounter}`;
                    campoCounter++;
                    
                    // Criar novo campo dinâmico
                    const novoCampo = document.createElement('div');
                    novoCampo.className = 'col-md-6 mb-3 campo-dinamico';
                    novoCampo.innerHTML = `
                        <div class="d-flex">
                            <div class="flex-grow-1">
                                <input type="text" class="form-control mb-2" 
                                       placeholder="Nome do Campo" 
                                       name="dinamico_nome_${campoId}" 
                                       value="${nomeCampo}">
                                <div class="input-group">
                                    <span class="input-group-text"><i class="bi bi-pencil-fill"></i></span>
                                    <input type="text" class="form-control" 
                                           placeholder="Valor" 
                                           id="${campoId}" 
                                           name="${campoId}" 
                                           value="${valorCampo}">
                                    <input type="hidden" name="campos_dinamicos[]" value="${campoId}">
                                </div>
                            </div>
                            <button type="button" class="btn btn-outline-danger ms-2 remove-campo-btn" 
                                    style="height: 38px; align-self: flex-end;">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    `;
                    
                    // Adicionar o novo campo ao container da seção alvo
                    targetDinamicosContainer.appendChild(novoCampo);
                    
                    // Adicionar event listener para o botão de remover
                    const removeBtn = novoCampo.querySelector('.remove-campo-btn');
                    removeBtn.addEventListener('click', function() {
                        novoCampo.remove();
                    });
                });
                
                // Expandir a seção alvo para mostrar os campos duplicados
                const targetButton = targetSection.querySelector('.accordion-button');
                if (targetButton.classList.contains('collapsed')) {
                    targetButton.click();
                }
                
                // Mostrar mensagem de sucesso
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
                alertDiv.innerHTML = `
                    <strong>Sucesso!</strong> Campos duplicados para a seção abaixo.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                currentSection.appendChild(alertDiv);
                
                // Remover alerta após 3 segundos
                setTimeout(() => {
                    alertDiv.remove();
                }, 3000);
            });
        }
    });
});