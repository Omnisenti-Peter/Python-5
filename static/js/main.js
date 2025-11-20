/**
 * Opinian - Main JavaScript File
 * Client-side functionality for the blogging platform
 */

// ===== AUTHENTICATION MODAL =====
function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function hideLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

function toggleAuthForm() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const authToggle = document.querySelector('.auth-toggle');

    if (loginForm && registerForm && authToggle) {
        if (loginForm.classList.contains('hidden')) {
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            authToggle.innerHTML = '<p>Don\'t have an account? <a href="#" onclick="toggleAuthForm(); return false;">Register here</a></p>';
        } else {
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            authToggle.innerHTML = '<p>Already have an account? <a href="#" onclick="toggleAuthForm(); return false;">Login here</a></p>';
        }
    }
}

// ===== AUTO-HIDE FLASH MESSAGES =====
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Add smooth scrolling for links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// ===== ESCAPE KEY TO CLOSE MODAL =====
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideLoginModal();
    }
});

// ===== FORM VALIDATION =====
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Add validation to registration form
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
        const email = document.getElementById('register-email').value;
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;

        if (username.length < 3) {
            e.preventDefault();
            alert('Username must be at least 3 characters long');
            return false;
        }

        if (!validateEmail(email)) {
            e.preventDefault();
            alert('Please enter a valid email address');
            return false;
        }

        if (password.length < 6) {
            e.preventDefault();
            alert('Password must be at least 6 characters long');
            return false;
        }
    });
}

// ===== TEXTAREA AUTO-RESIZE =====
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Apply to all textareas
document.querySelectorAll('textarea').forEach(textarea => {
    textarea.addEventListener('input', function() {
        autoResizeTextarea(this);
    });
    // Initial resize
    autoResizeTextarea(textarea);
});

// ===== CHARACTER COUNTER FOR TITLE =====
const titleInput = document.getElementById('blog-title-input');
if (titleInput) {
    const maxLength = titleInput.getAttribute('maxlength');
    if (maxLength) {
        const counter = document.createElement('div');
        counter.style.textAlign = 'right';
        counter.style.color = 'var(--smoke-gray)';
        counter.style.fontSize = '0.9rem';
        counter.style.marginTop = '0.5rem';
        titleInput.parentNode.insertBefore(counter, titleInput.nextSibling);

        function updateCounter() {
            const remaining = maxLength - titleInput.value.length;
            counter.textContent = `${titleInput.value.length} / ${maxLength} characters`;
            if (remaining < 20) {
                counter.style.color = 'var(--art-gold)';
            } else {
                counter.style.color = 'var(--smoke-gray)';
            }
        }

        titleInput.addEventListener('input', updateCounter);
        updateCounter();
    }
}

// ===== CONFIRM BEFORE LEAVING WITH UNSAVED CHANGES =====
let formChanged = false;

const forms = document.querySelectorAll('#blog-form, #ai-form');
forms.forEach(form => {
    const inputs = form.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            formChanged = true;
        });
    });

    form.addEventListener('submit', function() {
        formChanged = false;
    });
});

window.addEventListener('beforeunload', function(e) {
    if (formChanged) {
        e.preventDefault();
        e.returnValue = '';
        return '';
    }
});

// ===== LOADING ANIMATION FOR BUTTONS =====
function addLoadingState(button, originalText) {
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> ' + (originalText || 'Processing...');
}

function removeLoadingState(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// ===== LOCAL STORAGE FOR DRAFTS =====
function saveDraftToLocalStorage() {
    const title = document.getElementById('blog-title-input')?.value;
    const content = document.getElementById('blog-content-input')?.value;

    if (title || content) {
        localStorage.setItem('opinian_draft', JSON.stringify({
            title: title,
            content: content,
            timestamp: new Date().toISOString()
        }));
    }
}

function loadDraftFromLocalStorage() {
    const draft = localStorage.getItem('opinian_draft');
    if (draft) {
        try {
            const data = JSON.parse(draft);
            const titleInput = document.getElementById('blog-title-input');
            const contentInput = document.getElementById('blog-content-input');

            if (titleInput && contentInput && !titleInput.value && !contentInput.value) {
                if (confirm('Found an unsaved draft. Would you like to restore it?')) {
                    titleInput.value = data.title || '';
                    contentInput.value = data.content || '';
                }
            }
        } catch (e) {
            console.error('Error loading draft:', e);
        }
    }
}

function clearDraftFromLocalStorage() {
    localStorage.removeItem('opinian_draft');
}

// Auto-save draft every 30 seconds
if (document.getElementById('blog-title-input')) {
    loadDraftFromLocalStorage();
    setInterval(saveDraftToLocalStorage, 30000);

    // Clear draft on successful submission
    const blogForm = document.getElementById('blog-form');
    if (blogForm) {
        blogForm.addEventListener('submit', function() {
            clearDraftFromLocalStorage();
        });
    }
}

// ===== SMOOTH PAGE TRANSITIONS =====
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const pages = document.querySelectorAll('.page, .blog-container, .ai-container, .admin-container');
    pages.forEach(page => {
        page.style.opacity = '0';
        page.style.transform = 'translateY(20px)';
        setTimeout(() => {
            page.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            page.style.opacity = '1';
            page.style.transform = 'translateY(0)';
        }, 100);
    });
});

// ===== COPY TO CLIPBOARD UTILITY =====
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text)
            .then(() => true)
            .catch(() => false);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve(true);
        } catch (e) {
            document.body.removeChild(textArea);
            return Promise.resolve(false);
        }
    }
}

// ===== SCROLL TO TOP BUTTON =====
window.addEventListener('scroll', function() {
    const scrollButton = document.getElementById('scroll-to-top');
    if (window.pageYOffset > 300) {
        if (!scrollButton) {
            createScrollToTopButton();
        } else {
            scrollButton.style.display = 'block';
        }
    } else if (scrollButton) {
        scrollButton.style.display = 'none';
    }
});

function createScrollToTopButton() {
    const button = document.createElement('button');
    button.id = 'scroll-to-top';
    button.innerHTML = '<i class="fas fa-arrow-up"></i>';
    button.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(45deg, var(--art-gold), var(--bronze));
        color: var(--noir-black);
        border: none;
        cursor: pointer;
        font-size: 1.2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        z-index: 999;
    `;

    button.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    button.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
        this.style.boxShadow = '0 6px 15px rgba(212, 175, 55, 0.5)';
    });

    button.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.3)';
    });

    document.body.appendChild(button);
}

console.log('Opinian platform loaded successfully');
