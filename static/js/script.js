// Funções auxiliares para melhorar a experiência do usuário
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar validação visual aos campos do formulário
    const inputs = document.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
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