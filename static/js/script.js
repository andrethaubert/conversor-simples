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