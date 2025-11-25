# Opinian Platform - Core JavaScript Functions

## Application Architecture

The Opinian platform uses a modular JavaScript architecture with clear separation of concerns:

```
/opinian-app/
├── core/
│   ├── auth.js          # Authentication and session management
│   ├── api.js           # API communication layer
│   ├── storage.js       # Local storage and caching
│   └── utils.js         # Utility functions
├── components/
│   ├── blog-editor.js   # Rich text editor functionality
│   ├── ai-generator.js  # AI content generation
│   ├── media-upload.js  # File upload and management
│   ├── analytics.js     # Analytics tracking
│   └── admin-tools.js   # Admin dashboard functions
├── pages/
│   ├── home.js          # Homepage logic
│   ├── blog.js          # Blog management
│   ├── ai-tools.js      # AI assistant tools
│   └── admin.js         # Admin interface
└── app.js               # Main application controller
```

## Core Functions

### 1. Authentication System (`auth.js`)

```javascript
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.token = null;
        this.refreshToken = null;
        this.init();
    }

    // Initialize authentication system
    init() {
        this.token = this.getStoredToken();
        this.refreshToken = this.getStoredRefreshToken();
        if (this.token) {
            this.validateToken();
        }
    }

    // User login
    async login(email, password) {
        try {
            const response = await api.post('/auth/login', {
                email: email,
                password: password
            });

            if (response.success) {
                this.token = response.data.token;
                this.refreshToken = response.data.refreshToken;
                this.currentUser = response.data.user;
                
                this.storeTokens();
                this.setupTokenRefresh();
                this.trackLoginEvent();
                
                return { success: true, user: this.currentUser };
            }
            
            return { success: false, error: response.error };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Authentication failed' };
        }
    }

    // User registration
    async register(userData) {
        try {
            const response = await api.post('/auth/register', {
                email: userData.email,
                username: userData.username,
                password: userData.password,
                firstName: userData.firstName,
                lastName: userData.lastName,
                displayName: userData.displayName
            });

            if (response.success) {
                this.trackRegistrationEvent();
                return { success: true, message: 'Registration successful' };
            }
            
            return { success: false, error: response.error };
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, error: 'Registration failed' };
        }
    }

    // Logout user
    async logout() {
        try {
            await api.post('/auth/logout');
            this.clearTokens();
            this.currentUser = null;
            this.trackLogoutEvent();
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    // Token management
    getStoredToken() {
        return localStorage.getItem('opinian_token');
    }

    getStoredRefreshToken() {
        return localStorage.getItem('opinian_refresh_token');
    }

    storeTokens() {
        localStorage.setItem('opinian_token', this.token);
        localStorage.setItem('opinian_refresh_token', this.refreshToken);
    }

    clearTokens() {
        localStorage.removeItem('opinian_token');
        localStorage.removeItem('opinian_refresh_token');
    }

    // Validate JWT token
    async validateToken() {
        try {
            const response = await api.get('/auth/validate', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (response.success) {
                this.currentUser = response.data.user;
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        }
    }

    // Refresh token
    async refreshAccessToken() {
        try {
            const response = await api.post('/auth/refresh', {
                refreshToken: this.refreshToken
            });

            if (response.success) {
                this.token = response.data.token;
                this.storeTokens();
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    // Setup automatic token refresh
    setupTokenRefresh() {
        setInterval(async () => {
            if (this.token && this.refreshToken) {
                await this.refreshAccessToken();
            }
        }, 25 * 60 * 1000); // Refresh every 25 minutes
    }

    // Check user permissions
    hasPermission(permission) {
        if (!this.currentUser) return false;
        
        const userRole = this.currentUser.role;
        const permissions = {
            'admin': ['read', 'write', 'delete', 'admin'],
            'author': ['read', 'write'],
            'reader': ['read']
        };
        
        return permissions[userRole]?.includes(permission) || false;
    }

    // Analytics tracking
    trackLoginEvent() {
        analytics.track('user_login', {
            userId: this.currentUser?.id,
            timestamp: new Date().toISOString()
        });
    }

    trackRegistrationEvent() {
        analytics.track('user_registration', {
            timestamp: new Date().toISOString()
        });
    }

    trackLogoutEvent() {
        analytics.track('user_logout', {
            userId: this.currentUser?.id,
            timestamp: new Date().toISOString()
        });
    }
}
```

### 2. API Communication Layer (`api.js`)

```javascript
class APIClient {
    constructor() {
        this.baseURL = 'https://api.opinian.com/v1';
        this.timeout = 30000;
        this.setupInterceptors();
    }

    // Setup request/response interceptors
    setupInterceptors() {
        // Request interceptor for authentication
        this.requestInterceptor = (config) => {
            const token = auth.getStoredToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        };

        // Response interceptor for error handling
        this.responseInterceptor = (response) => {
            return response;
        };

        this.errorInterceptor = (error) => {
            if (error.response?.status === 401) {
                auth.clearTokens();
                window.location.href = '/login.html';
            }
            return Promise.reject(error);
        };
    }

    // Generic API request method
    async request(config) {
        try {
            const requestConfig = {
                ...config,
                url: `${this.baseURL}${config.url}`,
                timeout: this.timeout
            };

            // Apply request interceptor
            const processedConfig = this.requestInterceptor(requestConfig);
            
            // Make the request
            const response = await fetch(processedConfig.url, {
                method: processedConfig.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...processedConfig.headers
                },
                body: processedConfig.data ? JSON.stringify(processedConfig.data) : undefined
            });

            // Apply response interceptor
            const processedResponse = this.responseInterceptor(response);
            
            const data = await processedResponse.json();
            
            return {
                success: processedResponse.ok,
                data: data,
                status: processedResponse.status
            };
        } catch (error) {
            // Apply error interceptor
            this.errorInterceptor(error);
            return {
                success: false,
                error: error.message,
                status: error.response?.status || 500
            };
        }
    }

    // Convenience methods
    async get(url, config = {}) {
        return this.request({ ...config, method: 'GET', url });
    }

    async post(url, data, config = {}) {
        return this.request({ ...config, method: 'POST', url, data });
    }

    async put(url, data, config = {}) {
        return this.request({ ...config, method: 'PUT', url, data });
    }

    async delete(url, config = {}) {
        return this.request({ ...config, method: 'DELETE', url });
    }

    // File upload method
    async upload(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            if (onProgress) {
                xhr.upload.addEventListener('progress', onProgress);
            }

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', `${this.baseURL}${url}`);
            const token = auth.getStoredToken();
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }
            xhr.send(formData);
        });
    }
}
```

### 3. Blog Editor Component (`blog-editor.js`)

```javascript
class BlogEditor {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Start writing your story...',
            autoSave: true,
            autoSaveInterval: 30000,
            ...options
        };
        
        this.editor = null;
        this.currentPost = null;
        this.autoSaveTimer = null;
        this.isDirty = false;
        
        this.init();
    }

    // Initialize the editor
    init() {
        this.createEditorUI();
        this.setupEditor();
        this.setupToolbar();
        this.setupEventListeners();
        this.setupAutoSave();
    }

    // Create the editor UI structure
    createEditorUI() {
        this.container.innerHTML = `
            <div class="blog-editor">
                <div class="editor-toolbar">
                    <div class="toolbar-group">
                        <button type="button" class="btn-icon" data-command="bold" title="Bold (Ctrl+B)">
                            <i class="icon-bold"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="italic" title="Italic (Ctrl+I)">
                            <i class="icon-italic"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="underline" title="Underline (Ctrl+U)">
                            <i class="icon-underline"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="strikeThrough" title="Strikethrough">
                            <i class="icon-strikethrough"></i>
                        </button>
                    </div>
                    
                    <div class="toolbar-group">
                        <select class="font-family-select" data-command="fontName">
                            <option value="">Font Family</option>
                            <option value="Arial">Arial</option>
                            <option value="Times New Roman">Times New Roman</option>
                            <option value="Courier New">Courier New</option>
                            <option value="Georgia">Georgia</option>
                            <option value="Verdana">Verdana</option>
                        </select>
                        
                        <select class="font-size-select" data-command="fontSize">
                            <option value="1">12px</option>
                            <option value="2">14px</option>
                            <option value="3" selected>16px</option>
                            <option value="4">18px</option>
                            <option value="5">24px</option>
                            <option value="6">32px</option>
                            <option value="7">48px</option>
                        </select>
                    </div>
                    
                    <div class="toolbar-group">
                        <button type="button" class="btn-icon" data-command="justifyLeft" title="Align Left">
                            <i class="icon-align-left"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="justifyCenter" title="Align Center">
                            <i class="icon-align-center"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="justifyRight" title="Align Right">
                            <i class="icon-align-right"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="justifyFull" title="Justify">
                            <i class="icon-align-justify"></i>
                        </button>
                    </div>
                    
                    <div class="toolbar-group">
                        <button type="button" class="btn-icon" data-command="insertUnorderedList" title="Bullet List">
                            <i class="icon-list-bullet"></i>
                        </button>
                        <button type="button" class="btn-icon" data-command="insertOrderedList" title="Numbered List">
                            <i class="icon-list-numbered"></i>
                        </button>
                    </div>
                    
                    <div class="toolbar-group">
                        <button type="button" class="btn-icon" id="insertImage" title="Insert Image">
                            <i class="icon-image"></i>
                        </button>
                        <button type="button" class="btn-icon" id="insertLink" title="Insert Link">
                            <i class="icon-link"></i>
                        </button>
                        <input type="color" class="color-picker" id="textColor" title="Text Color">
                        <input type="color" class="color-picker" id="bgColor" title="Background Color">
                    </div>
                    
                    <div class="toolbar-group">
                        <button type="button" class="btn-icon" id="undo" title="Undo (Ctrl+Z)">
                            <i class="icon-undo"></i>
                        </button>
                        <button type="button" class="btn-icon" id="redo" title="Redo (Ctrl+Y)">
                            <i class="icon-redo"></i>
                        </button>
                        <button type="button" class="btn-icon" id="fullscreen" title="Fullscreen">
                            <i class="icon-fullscreen"></i>
                        </button>
                    </div>
                </div>
                
                <div class="editor-content">
                    <div class="editor-title">
                        <input type="text" id="postTitle" placeholder="Enter your blog title..." class="title-input">
                    </div>
                    
                    <div class="editor-body">
                        <div id="editor" class="editor-textarea" contenteditable="true" 
                             placeholder="${this.options.placeholder}"></div>
                    </div>
                </div>
                
                <div class="editor-footer">
                    <div class="editor-status">
                        <span id="wordCount">0 words</span>
                        <span id="readingTime">0 min read</span>
                        <span id="saveStatus">Saved</span>
                    </div>
                    
                    <div class="editor-actions">
                        <button type="button" id="saveDraft" class="btn btn-secondary">Save Draft</button>
                        <button type="button" id="preview" class="btn btn-outline">Preview</button>
                        <button type="button" id="publish" class="btn btn-primary">Publish</button>
                    </div>
                </div>
            </div>
        `;
    }

    // Setup the rich text editor
    setupEditor() {
        this.editor = this.container.querySelector('#editor');
        this.titleInput = this.container.querySelector('#postTitle');
        
        // Initialize editor with designMode
        document.designMode = 'on';
        
        // Setup editor event listeners
        this.editor.addEventListener('input', () => {
            this.updateWordCount();
            this.markAsDirty();
        });

        this.titleInput.addEventListener('input', () => {
            this.markAsDirty();
        });

        // Keyboard shortcuts
        this.editor.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.saveDraft();
                        break;
                    case 'z':
                        e.preventDefault();
                        document.execCommand('undo');
                        break;
                    case 'y':
                        e.preventDefault();
                        document.execCommand('redo');
                        break;
                }
            }
        });
    }

    // Setup toolbar functionality
    setupToolbar() {
        const toolbarButtons = this.container.querySelectorAll('[data-command]');
        
        toolbarButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const command = button.dataset.command;
                const value = button.dataset.value || null;
                
                if (command === 'fontName' || command === 'fontSize') {
                    const select = button;
                    document.execCommand(command, false, select.value);
                } else {
                    document.execCommand(command, false, value);
                }
                
                this.updateToolbarState();
                this.markAsDirty();
            });
        });

        // Color pickers
        const textColorPicker = this.container.querySelector('#textColor');
        const bgColorPicker = this.container.querySelector('#bgColor');
        
        textColorPicker.addEventListener('change', (e) => {
            document.execCommand('foreColor', false, e.target.value);
            this.markAsDirty();
        });

        bgColorPicker.addEventListener('change', (e) => {
            document.execCommand('hiliteColor', false, e.target.value);
            this.markAsDirty();
        });

        // Custom buttons
        this.container.querySelector('#insertImage').addEventListener('click', () => {
            this.insertImage();
        });

        this.container.querySelector('#insertLink').addEventListener('click', () => {
            this.insertLink();
        });

        this.container.querySelector('#undo').addEventListener('click', () => {
            document.execCommand('undo');
        });

        this.container.querySelector('#redo').addEventListener('click', () => {
            document.execCommand('redo');
        });

        this.container.querySelector('#fullscreen').addEventListener('click', () => {
            this.toggleFullscreen();
        });
    }

    // Setup event listeners for editor actions
    setupEventListeners() {
        this.container.querySelector('#saveDraft').addEventListener('click', () => {
            this.saveDraft();
        });

        this.container.querySelector('#preview').addEventListener('click', () => {
            this.previewPost();
        });

        this.container.querySelector('#publish').addEventListener('click', () => {
            this.publishPost();
        });
    }

    // Insert image functionality
    insertImage() {
        const imageUrl = prompt('Enter image URL:');
        if (imageUrl) {
            const altText = prompt('Enter alt text (optional):') || '';
            document.execCommand('insertImage', false, imageUrl);
            
            // Set alt text for the inserted image
            const images = this.editor.querySelectorAll('img');
            const newImage = images[images.length - 1];
            if (newImage) {
                newImage.alt = altText;
            }
            
            this.markAsDirty();
        }
    }

    // Insert link functionality
    insertLink() {
        const selection = window.getSelection();
        const linkUrl = prompt('Enter URL:');
        
        if (linkUrl) {
            const linkText = selection.toString() || prompt('Enter link text:');
            if (linkText) {
                document.execCommand('createLink', false, linkUrl);
                this.markAsDirty();
            }
        }
    }

    // Toggle fullscreen mode
    toggleFullscreen() {
        const editor = this.container.querySelector('.blog-editor');
        editor.classList.toggle('fullscreen');
        
        const button = this.container.querySelector('#fullscreen i');
        button.classList.toggle('icon-fullscreen');
        button.classList.toggle('icon-fullscreen-exit');
    }

    // Update word count and reading time
    updateWordCount() {
        const content = this.editor.textContent || '';
        const title = this.titleInput.value || '';
        const totalText = title + ' ' + content;
        
        const wordCount = totalText.trim().split(/\s+/).filter(word => word.length > 0).length;
        const readingTime = Math.ceil(wordCount / 200); // 200 words per minute
        
        this.container.querySelector('#wordCount').textContent = `${wordCount} words`;
        this.container.querySelector('#readingTime').textContent = `${readingTime} min read`;
    }

    // Update toolbar state based on selection
    updateToolbarState() {
        const commands = ['bold', 'italic', 'underline', 'strikeThrough'];
        
        commands.forEach(command => {
            const button = this.container.querySelector(`[data-command="${command}"]`);
            if (button) {
                button.classList.toggle('active', document.queryCommandState(command));
            }
        });
    }

    // Mark content as modified
    markAsDirty() {
        this.isDirty = true;
        this.container.querySelector('#saveStatus').textContent = 'Unsaved changes';
        this.container.querySelector('#saveStatus').classList.add('unsaved');
    }

    // Clear dirty state
    markAsClean() {
        this.isDirty = false;
        this.container.querySelector('#saveStatus').textContent = 'Saved';
        this.container.querySelector('#saveStatus').classList.remove('unsaved');
    }

    // Auto-save functionality
    setupAutoSave() {
        if (this.options.autoSave) {
            this.autoSaveTimer = setInterval(() => {
                if (this.isDirty) {
                    this.saveDraft(true);
                }
            }, this.options.autoSaveInterval);
        }
    }

    // Save draft
    async saveDraft(isAutoSave = false) {
        try {
            const postData = {
                title: this.titleInput.value,
                content: this.editor.innerHTML,
                content_text: this.editor.textContent,
                status: 'draft',
                word_count: this.editor.textContent.trim().split(/\s+/).length,
                reading_time: Math.ceil(this.editor.textContent.trim().split(/\s+/).length / 200)
            };

            let response;
            if (this.currentPost?.id) {
                response = await api.put(`/blog/posts/${this.currentPost.id}`, postData);
            } else {
                response = await api.post('/blog/posts', postData);
                if (response.success) {
                    this.currentPost = response.data;
                }
            }

            if (response.success) {
                this.markAsClean();
                if (!isAutoSave) {
                    this.showNotification('Draft saved successfully', 'success');
                }
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Save error:', error);
            this.showNotification('Failed to save draft', 'error');
        }
    }

    // Preview post
    previewPost() {
        const previewWindow = window.open('', '_blank');
        const previewContent = `
            <html>
                <head>
                    <title>${this.titleInput.value}</title>
                    <link rel="stylesheet" href="/css/blog-preview.css">
                </head>
                <body>
                    <article class="blog-post">
                        <h1>${this.titleInput.value}</h1>
                        <div class="post-content">
                            ${this.editor.innerHTML}
                        </div>
                    </article>
                </body>
            </html>
        `;
        
        previewWindow.document.write(previewContent);
        previewWindow.document.close();
    }

    // Publish post
    async publishPost() {
        if (!this.titleInput.value.trim()) {
            this.showNotification('Please enter a title before publishing', 'warning');
            return;
        }

        if (!this.editor.textContent.trim()) {
            this.showNotification('Please add content before publishing', 'warning');
            return;
        }

        try {
            const postData = {
                title: this.titleInput.value,
                content: this.editor.innerHTML,
                content_text: this.editor.textContent,
                status: 'published',
                published_at: new Date().toISOString(),
                word_count: this.editor.textContent.trim().split(/\s+/).length,
                reading_time: Math.ceil(this.editor.textContent.trim().split(/\s+/).length / 200)
            };

            let response;
            if (this.currentPost?.id) {
                response = await api.put(`/blog/posts/${this.currentPost.id}`, postData);
            } else {
                response = await api.post('/blog/posts', postData);
            }

            if (response.success) {
                this.showNotification('Post published successfully!', 'success');
                setTimeout(() => {
                    window.location.href = `/blog/${response.data.slug}`;
                }, 2000);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Publish error:', error);
            this.showNotification('Failed to publish post', 'error');
        }
    }

    // Load existing post
    async loadPost(postId) {
        try {
            const response = await api.get(`/blog/posts/${postId}`);
            if (response.success) {
                this.currentPost = response.data;
                this.titleInput.value = response.data.title;
                this.editor.innerHTML = response.data.content;
                this.updateWordCount();
                this.markAsClean();
            }
        } catch (error) {
            console.error('Load post error:', error);
            this.showNotification('Failed to load post', 'error');
        }
    }

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Destroy editor
    destroy() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
        
        document.designMode = 'off';
        this.container.innerHTML = '';
    }
}
```

### 4. AI Content Generator (`ai-generator.js`)

```javascript
class AIGenerator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPrompt = null;
        this.generationHistory = [];
        this.init();
    }

    init() {
        this.createUI();
        this.loadPrompts();
        this.setupEventListeners();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="ai-generator">
                <div class="generator-header">
                    <h2>AI Content Assistant</h2>
                    <p>Let AI help you create compelling blog content</p>
                </div>
                
                <div class="generator-controls">
                    <div class="prompt-selector">
                        <label for="promptType">Content Type:</label>
                        <select id="promptType" class="form-control">
                            <option value="">Select a content type...</option>
                        </select>
                    </div>
                    
                    <div class="input-section">
                        <label for="topicInput">Topic or Keywords:</label>
                        <textarea id="topicInput" class="form-control" 
                                  placeholder="Enter your blog topic, keywords, or rough ideas..."></textarea>
                    </div>
                    
                    <div class="advanced-options">
                        <div class="option-group">
                            <label for="toneSelect">Writing Style:</label>
                            <select id="toneSelect" class="form-control">
                                <option value="professional">Professional</option>
                                <option value="casual">Casual</option>
                                <option value="academic">Academic</option>
                                <option value="creative">Creative</option>
                                <option value="noir">Noir & Mystery</option>
                            </select>
                        </div>
                        
                        <div class="option-group">
                            <label for="lengthSelect">Content Length:</label>
                            <select id="lengthSelect" class="form-control">
                                <option value="short">Short (300-500 words)</option>
                                <option value="medium" selected>Medium (800-1200 words)</option>
                                <option value="long">Long (1500-2500 words)</option>
                            </select>
                        </div>
                        
                        <div class="option-group">
                            <label for="audienceSelect">Target Audience:</label>
                            <select id="audienceSelect" class="form-control">
                                <option value="general">General Audience</option>
                                <option value="beginners">Beginners</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                                <option value="professionals">Professionals</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="generation-controls">
                        <button type="button" id="generateBtn" class="btn btn-primary">
                            <i class="icon-magic"></i> Generate Content
                        </button>
                        <button type="button" id="enhanceBtn" class="btn btn-secondary" disabled>
                            <i class="icon-wand"></i> Enhance Existing
                        </button>
                    </div>
                </div>
                
                <div class="generation-results">
                    <div class="results-header">
                        <h3>Generated Content</h3>
                        <div class="result-actions">
                            <button type="button" id="exportBtn" class="btn btn-outline" disabled>
                                <i class="icon-download"></i> Export
                            </button>
                            <button type="button" id="useInEditorBtn" class="btn btn-primary" disabled>
                                <i class="icon-edit"></i> Use in Editor
                            </button>
                        </div>
                    </div>
                    
                    <div class="generation-status" id="generationStatus" style="display: none;">
                        <div class="spinner"></div>
                        <span>Generating content...</span>
                    </div>
                    
                    <div class="generated-content" id="generatedContent">
                        <div class="empty-state">
                            <i class="icon-document"></i>
                            <p>Your generated content will appear here</p>
                            <small>Fill in the details above and click "Generate Content" to get started</small>
                        </div>
                    </div>
                </div>
                
                <div class="generation-history">
                    <h3>Recent Generations</h3>
                    <div class="history-list" id="historyList">
                        <div class="empty-state">
                            <p>No previous generations</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadPrompts() {
        try {
            const response = await api.get('/ai/prompts');
            if (response.success) {
                this.populatePromptSelector(response.data);
            }
        } catch (error) {
            console.error('Failed to load prompts:', error);
        }
    }

    populatePromptSelector(prompts) {
        const select = this.container.querySelector('#promptType');
        prompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt.id;
            option.textContent = prompt.name;
            option.dataset.category = prompt.category;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        this.container.querySelector('#generateBtn').addEventListener('click', () => {
            this.generateContent();
        });

        this.container.querySelector('#enhanceBtn').addEventListener('click', () => {
            this.enhanceContent();
        });

        this.container.querySelector('#exportBtn').addEventListener('click', () => {
            this.exportContent();
        });

        this.container.querySelector('#useInEditorBtn').addEventListener('click', () => {
            this.useInEditor();
        });

        this.container.querySelector('#promptType').addEventListener('change', (e) => {
            this.onPromptTypeChange(e.target.value);
        });
    }

    async generateContent() {
        const promptType = this.container.querySelector('#promptType').value;
        const topic = this.container.querySelector('#topicInput').value;
        const tone = this.container.querySelector('#toneSelect').value;
        const length = this.container.querySelector('#lengthSelect').value;
        const audience = this.container.querySelector('#audienceSelect').value;

        if (!promptType) {
            this.showNotification('Please select a content type', 'warning');
            return;
        }

        if (!topic.trim()) {
            this.showNotification('Please enter a topic or keywords', 'warning');
            return;
        }

        this.showGenerationStatus(true);

        try {
            const requestData = {
                promptId: promptType,
                inputs: {
                    topic: topic,
                    tone: tone,
                    length: length,
                    audience: audience
                }
            };

            const response = await api.post('/ai/generate', requestData);
            
            if (response.success) {
                this.displayGeneratedContent(response.data);
                this.addToHistory(response.data, topic);
                this.enableResultActions();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Generation error:', error);
            this.showNotification('Failed to generate content', 'error');
        } finally {
            this.showGenerationStatus(false);
        }
    }

    displayGeneratedContent(content) {
        const container = this.container.querySelector('#generatedContent');
        
        container.innerHTML = `
            <div class="content-result">
                <div class="content-header">
                    <h4>${content.title || 'Generated Content'}</h4>
                    <div class="content-meta">
                        <span class="word-count">${content.wordCount || 0} words</span>
                        <span class="reading-time">${content.readingTime || 0} min read</span>
                    </div>
                </div>
                
                <div class="content-body">
                    ${content.content}
                </div>
                
                ${content.suggestions ? `
                    <div class="content-suggestions">
                        <h5>Suggestions for Improvement</h5>
                        <ul>
                            ${content.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    addToHistory(content, topic) {
        const historyItem = {
            id: content.id || Date.now(),
            topic: topic,
            title: content.title || 'Generated Content',
            content: content.content,
            timestamp: new Date().toISOString(),
            wordCount: content.wordCount || 0
        };

        this.generationHistory.unshift(historyItem);
        
        // Keep only last 10 items
        if (this.generationHistory.length > 10) {
            this.generationHistory = this.generationHistory.slice(0, 10);
        }

        this.updateHistoryDisplay();
    }

    updateHistoryDisplay() {
        const historyList = this.container.querySelector('#historyList');
        
        if (this.generationHistory.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <p>No previous generations</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = this.generationHistory.map(item => `
            <div class="history-item" data-id="${item.id}">
                <div class="history-content">
                    <h5>${item.title}</h5>
                    <p class="history-topic">${item.topic}</p>
                    <div class="history-meta">
                        <span class="history-date">${new Date(item.timestamp).toLocaleDateString()}</span>
                        <span class="history-words">${item.wordCount} words</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button type="button" class="btn-icon" onclick="aiGenerator.loadFromHistory('${item.id}')" title="Load">
                        <i class="icon-load"></i>
                    </button>
                    <button type="button" class="btn-icon" onclick="aiGenerator.deleteFromHistory('${item.id}')" title="Delete">
                        <i class="icon-delete"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    loadFromHistory(itemId) {
        const item = this.generationHistory.find(h => h.id === itemId);
        if (item) {
            this.displayGeneratedContent(item);
            this.enableResultActions();
            
            // Update form fields
            this.container.querySelector('#topicInput').value = item.topic;
        }
    }

    deleteFromHistory(itemId) {
        this.generationHistory = this.generationHistory.filter(h => h.id !== itemId);
        this.updateHistoryDisplay();
    }

    enableResultActions() {
        this.container.querySelector('#exportBtn').disabled = false;
        this.container.querySelector('#useInEditorBtn').disabled = false;
    }

    showGenerationStatus(show) {
        const status = this.container.querySelector('#generationStatus');
        status.style.display = show ? 'flex' : 'none';
    }

    async exportContent() {
        const content = this.container.querySelector('#generatedContent .content-body');
        if (!content) return;

        const title = this.container.querySelector('#generatedContent h4')?.textContent || 'Generated Content';
        const textContent = content.textContent;

        // Create export options modal
        const modal = this.createExportModal(title, textContent, content.innerHTML);
        document.body.appendChild(modal);
    }

    createExportModal(title, textContent, htmlContent) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Export Content</h3>
                    <button type="button" class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="export-options">
                        <div class="export-option">
                            <label>
                                <input type="radio" name="exportFormat" value="text" checked>
                                <span>Plain Text (.txt)</span>
                            </label>
                        </div>
                        <div class="export-option">
                            <label>
                                <input type="radio" name="exportFormat" value="html">
                                <span>HTML Document (.html)</span>
                            </label>
                        </div>
                        <div class="export-option">
                            <label>
                                <input type="radio" name="exportFormat" value="markdown">
                                <span>Markdown (.md)</span>
                            </label>
                        </div>
                        <div class="export-option">
                            <label>
                                <input type="radio" name="exportFormat" value="word">
                                <span>Word Document (via HTML)</span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="export-filename">
                        <label for="exportFilename">Filename:</label>
                        <input type="text" id="exportFilename" value="${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}" class="form-control">
                    </div>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary modal-cancel">Cancel</button>
                    <button type="button" class="btn btn-primary modal-confirm">Export</button>
                </div>
            </div>
        `;

        // Setup modal event listeners
        modal.querySelector('.modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.modal-cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.modal-confirm').addEventListener('click', () => {
            const format = modal.querySelector('input[name="exportFormat"]:checked').value;
            const filename = modal.querySelector('#exportFilename').value;
            this.performExport(format, filename, title, textContent, htmlContent);
            document.body.removeChild(modal);
        });

        return modal;
    }

    performExport(format, filename, title, textContent, htmlContent) {
        let content, mimeType, extension;

        switch (format) {
            case 'text':
                content = textContent;
                mimeType = 'text/plain';
                extension = '.txt';
                break;
            case 'html':
                content = `<!DOCTYPE html>
<html>
<head>
    <title>${title}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .content { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>${title}</h1>
    <div class="content">${htmlContent}</div>
</body>
</html>`;
                mimeType = 'text/html';
                extension = '.html';
                break;
            case 'markdown':
                content = `# ${title}\n\n${this.htmlToMarkdown(htmlContent)}`;
                mimeType = 'text/markdown';
                extension = '.md';
                break;
            case 'word':
                // Word export via HTML
                content = `<!DOCTYPE html>
<html>
<head>
    <title>${title}</title>
    <meta charset="utf-8">
    <!--[if gte mso 9]>
    <xml>
        <w:WordDocument>
            <w:View>Print</w:View>
            <w:Zoom>100</w:Zoom>
        </w:WordDocument>
    </xml>
    <![endif]-->
    <style>
        body { font-family: 'Times New Roman', serif; margin: 1in; }
        h1 { font-size: 16pt; font-weight: bold; margin-bottom: 12pt; }
        p { margin-bottom: 12pt; line-height: 1.15; }
    </style>
</head>
<body>
    <h1>${title}</h1>
    ${htmlContent}
</body>
</html>`;
                mimeType = 'application/msword';
                extension = '.doc';
                break;
        }

        // Create and trigger download
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename + extension;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification(`${format.toUpperCase()} file exported successfully`, 'success');
    }

    htmlToMarkdown(html) {
        // Simple HTML to Markdown conversion
        return html
            .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
            .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
            .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
            .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
            .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
            .replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**')
            .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
            .replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*')
            .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
            .replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)')
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<[^>]*>/g, '')
            .trim();
    }

    useInEditor() {
        const content = this.container.querySelector('#generatedContent .content-body');
        const title = this.container.querySelector('#generatedContent h4')?.textContent || '';
        
        if (content && window.blogEditor) {
            window.blogEditor.titleInput.value = title;
            window.blogEditor.editor.innerHTML = content.innerHTML;
            window.blogEditor.updateWordCount();
            window.blogEditor.markAsDirty();
            
            // Navigate to editor page if not already there
            if (!window.location.pathname.includes('editor')) {
                window.location.href = '/editor.html';
            }
            
            this.showNotification('Content loaded in editor', 'success');
        } else {
            this.showNotification('Editor not available', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    onPromptTypeChange(promptId) {
        if (promptId) {
            this.container.querySelector('#enhanceBtn').disabled = false;
        } else {
            this.container.querySelector('#enhanceBtn').disabled = true;
        }
    }

    async enhanceContent() {
        // This would integrate with existing content in the editor
        const currentContent = window.blogEditor?.editor?.innerHTML;
        if (!currentContent) {
            this.showNotification('No content to enhance', 'warning');
            return;
        }

        this.showGenerationStatus(true);

        try {
            const response = await api.post('/ai/enhance', {
                content: currentContent,
                promptId: this.container.querySelector('#promptType').value
            });

            if (response.success) {
                this.displayGeneratedContent(response.data);
                this.enableResultActions();
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Enhancement error:', error);
            this.showNotification('Failed to enhance content', 'error');
        } finally {
            this.showGenerationStatus(false);
        }
    }
}
```

## 5. Media Upload System (`media-upload.js`)

```javascript
class MediaUploader {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            maxFileSize: 5 * 1024 * 1024, // 5MB
            allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
            maxFiles: 10,
            uploadUrl: '/api/media/upload',
            ...options
        };
        
        this.uploadedFiles = [];
        this.uploadQueue = [];
        this.isUploading = false;
        
        this.init();
    }

    init() {
        this.createUI();
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="media-uploader">
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-prompt">
                        <i class="icon-cloud-upload"></i>
                        <h3>Drop files here or click to browse</h3>
                        <p>Supports JPG, PNG, GIF, WebP, SVG (Max 5MB each)</p>
                        <input type="file" id="fileInput" multiple accept="image/*" style="display: none;">
                        <button type="button" id="browseBtn" class="btn btn-primary">
                            Choose Files
                        </button>
                    </div>
                </div>
                
                <div class="upload-progress" id="uploadProgress" style="display: none;">
                    <div class="progress-header">
                        <span>Uploading files...</span>
                        <span id="progressText">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
                
                <div class="uploaded-files" id="uploadedFiles">
                    <h3>Uploaded Files</h3>
                    <div class="file-grid" id="fileGrid">
                        <div class="empty-state">
                            <i class="icon-image"></i>
                            <p>No files uploaded yet</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const browseBtn = this.container.querySelector('#browseBtn');
        const fileInput = this.container.querySelector('#fileInput');

        browseBtn.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
    }

    setupDragAndDrop() {
        const uploadZone = this.container.querySelector('#uploadZone');

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            this.handleFileSelection(e.dataTransfer.files);
        });
    }

    handleFileSelection(files) {
        const fileArray = Array.from(files);
        const validFiles = this.validateFiles(fileArray);

        if (validFiles.length === 0) {
            return;
        }

        if (this.uploadedFiles.length + validFiles.length > this.options.maxFiles) {
            this.showNotification(`Maximum ${this.options.maxFiles} files allowed`, 'warning');
            return;
        }

        this.uploadQueue.push(...validFiles);
        this.processUploadQueue();
    }

    validateFiles(files) {
        const validFiles = [];
        
        files.forEach(file => {
            if (!this.options.allowedTypes.includes(file.type)) {
                this.showNotification(`Invalid file type: ${file.name}`, 'error');
                return;
            }

            if (file.size > this.options.maxFileSize) {
                this.showNotification(`File too large: ${file.name}`, 'error');
                return;
            }

            validFiles.push(file);
        });

        return validFiles;
    }

    async processUploadQueue() {
        if (this.isUploading || this.uploadQueue.length === 0) {
            return;
        }

        this.isUploading = true;
        this.showUploadProgress(true);

        const totalFiles = this.uploadQueue.length;
        let processedFiles = 0;

        for (const file of this.uploadQueue) {
            try {
                await this.uploadFile(file, (progress) => {
                    const overallProgress = (processedFiles + progress / 100) / totalFiles * 100;
                    this.updateProgress(overallProgress);
                });
                
                processedFiles++;
            } catch (error) {
                console.error('Upload error:', error);
                this.showNotification(`Failed to upload ${file.name}`, 'error');
            }
        }

        this.uploadQueue = [];
        this.isUploading = false;
        this.showUploadProgress(false);
        this.updateFileGrid();
    }

    async uploadFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('filename', file.name);
            formData.append('mimeType', file.type);

            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = (e.loaded / e.total) * 100;
                    onProgress(progress);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        this.uploadedFiles.push(response.data);
                        resolve(response.data);
                    } else {
                        reject(new Error(response.error));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', this.options.uploadUrl);
            const token = auth.getStoredToken();
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }
            xhr.send(formData);
        });
    }

    showUploadProgress(show) {
        const progress = this.container.querySelector('#uploadProgress');
        progress.style.display = show ? 'block' : 'none';
    }

    updateProgress(percentage) {
        const progressFill = this.container.querySelector('#progressFill');
        const progressText = this.container.querySelector('#progressText');
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${Math.round(percentage)}%`;
    }

    updateFileGrid() {
        const fileGrid = this.container.querySelector('#fileGrid');
        
        if (this.uploadedFiles.length === 0) {
            fileGrid.innerHTML = `
                <div class="empty-state">
                    <i class="icon-image"></i>
                    <p>No files uploaded yet</p>
                </div>
            `;
            return;
        }

        fileGrid.innerHTML = this.uploadedFiles.map(file => `
            <div class="file-item" data-id="${file.id}">
                <div class="file-preview">
                    <img src="${file.thumbnailUrl || file.url}" alt="${file.originalName}" loading="lazy">
                    <div class="file-overlay">
                        <button type="button" class="btn-icon" onclick="mediaUploader.viewFile('${file.id}')" title="View">
                            <i class="icon-eye"></i>
                        </button>
                        <button type="button" class="btn-icon" onclick="mediaUploader.copyUrl('${file.url}')" title="Copy URL">
                            <i class="icon-copy"></i>
                        </button>
                        <button type="button" class="btn-icon" onclick="mediaUploader.deleteFile('${file.id}')" title="Delete">
                            <i class="icon-delete"></i>
                        </button>
                    </div>
                </div>
                <div class="file-info">
                    <div class="file-name" title="${file.originalName}">${file.originalName}</div>
                    <div class="file-meta">
                        <span class="file-size">${this.formatFileSize(file.fileSize)}</span>
                        <span class="file-type">${file.mimeType.split('/')[1].toUpperCase()}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    viewFile(fileId) {
        const file = this.uploadedFiles.find(f => f.id === fileId);
        if (file) {
            const modal = this.createImageModal(file);
            document.body.appendChild(modal);
        }
    }

    createImageModal(file) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay image-viewer';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${file.originalName}</h3>
                    <button type="button" class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <img src="${file.url}" alt="${file.originalName}" style="max-width: 100%; height: auto;">
                    <div class="image-info">
                        <p><strong>File Size:</strong> ${this.formatFileSize(file.fileSize)}</p>
                        <p><strong>Type:</strong> ${file.mimeType}</p>
                        <p><strong>Uploaded:</strong> ${new Date(file.uploadedAt).toLocaleDateString()}</p>
                        <p><strong>URL:</strong> <code>${file.url}</code></p>
                    </div>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-primary" onclick="mediaUploader.copyUrl('${file.url}')">
                        Copy URL
                    </button>
                    <button type="button" class="btn btn-secondary modal-close">
                        Close
                    </button>
                </div>
            </div>
        `;

        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        });

        return modal;
    }

    copyUrl(url) {
        navigator.clipboard.writeText(url).then(() => {
            this.showNotification('URL copied to clipboard', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy URL', 'error');
        });
    }

    async deleteFile(fileId) {
        if (!confirm('Are you sure you want to delete this file?')) {
            return;
        }

        try {
            const response = await api.delete(`/media/files/${fileId}`);
            if (response.success) {
                this.uploadedFiles = this.uploadedFiles.filter(f => f.id !== fileId);
                this.updateFileGrid();
                this.showNotification('File deleted successfully', 'success');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Failed to delete file', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Get uploaded files
    getUploadedFiles() {
        return this.uploadedFiles;
    }

    // Clear all uploaded files
    clearFiles() {
        this.uploadedFiles = [];
        this.updateFileGrid();
    }
}
```

These core JavaScript functions provide the foundation for the Opinian platform's sophisticated functionality, including authentication, content creation, AI integration, and media management. Each module is designed to be modular, maintainable, and seamlessly integrated with the 1920s-1940s noir aesthetic.