// Opinian Platform - Main Application Controller
// Integrates all components and manages global state

class OpinianApp {
    constructor() {
        this.version = '1.0.0';
        this.initialized = false;
        this.currentUser = null;
        this.config = {};
        this.modules = {};
        
        this.init();
    }

    // Initialize the application
    async init() {
        try {
            console.log('Initializing Opinian Platform v' + this.version);
            
            // Load configuration
            await this.loadConfig();
            
            // Initialize core modules
            await this.initializeCore();
            
            // Setup global event listeners
            this.setupGlobalEvents();
            
            // Initialize page-specific functionality
            await this.initializePage();
            
            this.initialized = true;
            console.log('Opinian Platform initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Opinian Platform:', error);
            this.showError('Failed to load application. Please refresh the page.');
        }
    }

    // Load application configuration
    async loadConfig() {
        // Mock configuration - in a real app, this would come from a config file or API
        this.config = {
            api: {
                baseUrl: 'https://api.opinian.com/v1',
                timeout: 30000
            },
            ui: {
                animations: true,
                theme: 'noir',
                language: 'en'
            },
            features: {
                ai: true,
                analytics: true,
                socialLogin: true,
                notifications: true
            },
            limits: {
                maxFileSize: 5 * 1024 * 1024, // 5MB
                maxFiles: 10,
                maxPostsPerDay: 10,
                maxCommentsPerHour: 20
            }
        };
    }

    // Initialize core modules
    async initializeCore() {
        // Initialize authentication system
        this.modules.auth = new AuthManager();
        
        // Initialize API client
        this.modules.api = new APIClient(this.config.api);
        
        // Initialize analytics
        if (this.config.features.analytics) {
            this.modules.analytics = new AnalyticsTracker();
        }
        
        // Initialize notification system
        if (this.config.features.notifications) {
            this.modules.notifications = new NotificationManager();
        }
        
        // Initialize theme manager
        this.modules.theme = new ThemeManager();
        
        // Initialize storage manager
        this.modules.storage = new StorageManager();
    }

    // Setup global event listeners
    setupGlobalEvents() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });

        // Handle window resize
        window.addEventListener('resize', this.debounce(() => {
            this.onWindowResize();
        }, 250));

        // Handle online/offline status
        window.addEventListener('online', () => {
            this.onNetworkStatusChange(true);
        });

        window.addEventListener('offline', () => {
            this.onNetworkStatusChange(false);
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Handle navigation
        window.addEventListener('beforeunload', (e) => {
            return this.onBeforeUnload(e);
        });
    }

    // Initialize page-specific functionality
    async initializePage() {
        const currentPage = this.getCurrentPage();
        
        switch (currentPage) {
            case 'index':
                await this.initializeHomePage();
                break;
            case 'editor':
                await this.initializeEditorPage();
                break;
            case 'ai-tools':
                await this.initializeAIToolsPage();
                break;
            case 'admin-dashboard':
                await this.initializeAdminPage();
                break;
            case 'login':
                await this.initializeLoginPage();
                break;
            default:
                console.log('No specific initialization for page:', currentPage);
        }
    }

    // Get current page identifier
    getCurrentPage() {
        const path = window.location.pathname;
        const page = path.split('/').pop().replace('.html', '') || 'index';
        return page;
    }

    // Initialize home page
    async initializeHomePage() {
        console.log('Initializing home page');
        
        // Initialize hero animations
        this.initializeHeroAnimations();
        
        // Load featured content
        await this.loadFeaturedContent();
        
        // Initialize scroll animations
        this.initializeScrollAnimations();
    }

    // Initialize editor page
    async initializeEditorPage() {
        console.log('Initializing editor page');
        
        // Check authentication
        if (!this.modules.auth.isAuthenticated()) {
            this.redirectToLogin();
            return;
        }
        
        // Initialize blog editor
        if (typeof BlogEditor !== 'undefined') {
            window.blogEditor = new BlogEditor('blogEditor', {
                placeholder: 'Begin your story here... Let the words flow like shadows in the night.',
                autoSave: true,
                autoSaveInterval: 30000
            });
            
            // Load existing post if editing
            const postId = this.getUrlParameter('post');
            if (postId) {
                await window.blogEditor.loadPost(postId);
            }
        }
        
        // Initialize media uploader
        if (typeof MediaUploader !== 'undefined') {
            window.mediaUploader = new MediaUploader('mediaUploader', {
                maxFileSize: this.config.limits.maxFileSize,
                allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
                maxFiles: this.config.limits.maxFiles,
                uploadUrl: '/api/media/upload'
            });
        }
    }

    // Initialize AI tools page
    async initializeAIToolsPage() {
        console.log('Initializing AI tools page');
        
        // Check authentication
        if (!this.modules.auth.isAuthenticated()) {
            this.redirectToLogin();
            return;
        }
        
        // Initialize AI generator
        if (typeof AIGenerator !== 'undefined') {
            window.aiGenerator = new AIGenerator('aiGenerator');
        }
    }

    // Initialize admin dashboard
    async initializeAdminPage() {
        console.log('Initializing admin dashboard');
        
        // Check admin authentication
        if (!this.modules.auth.hasRole('admin')) {
            this.showError('Access denied. Admin privileges required.');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
            return;
        }
        
        // Initialize admin components
        await this.initializeAdminComponents();
    }

    // Initialize login page
    async initializeLoginPage() {
        console.log('Initializing login page');
        
        // Check if already authenticated
        if (this.modules.auth.isAuthenticated()) {
            this.redirectToDashboard();
            return;
        }
    }

    // Initialize hero animations for home page
    initializeHeroAnimations() {
        if (typeof Typed !== 'undefined') {
            // Initialize typed text animation
            const typed = new Typed('#typed-text', {
                strings: [
                    'Where Stories<br>Come Alive',
                    'Where Noir Meets<br>Digital Age',
                    'Where AI Enhances<br>Creativity',
                    'Where Every Voice<br>Finds Power'
                ],
                typeSpeed: 60,
                backSpeed: 30,
                backDelay: 2000,
                loop: true,
                showCursor: true,
                cursorChar: '|'
            });
        }
    }

    // Load featured content for home page
    async loadFeaturedContent() {
        try {
            // Simulate API call to load featured blogs
            const featuredBlogs = await this.getFeaturedBlogs();
            this.displayFeaturedBlogs(featuredBlogs);
        } catch (error) {
            console.error('Failed to load featured content:', error);
        }
    }

    // Get featured blogs (mock data)
    async getFeaturedBlogs() {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: 'blog1',
                        title: "The Art of Noir Storytelling in Digital Age",
                        excerpt: "Explore how the timeless appeal of noir aesthetics influences contemporary digital narratives and creates compelling storytelling experiences.",
                        author: "Elena Blackwood",
                        date: "Jan 15, 2024",
                        readTime: "8 min read",
                        views: "2.4K",
                        likes: "156",
                        image: null
                    },
                    {
                        id: 'blog2',
                        title: "AI as Your Creative Writing Partner",
                        excerpt: "Discover how artificial intelligence can enhance your creative process, from generating ideas to refining your prose with sophisticated suggestions.",
                        author: "Marcus Sterling",
                        date: "Jan 12, 2024",
                        readTime: "6 min read",
                        views: "1.8K",
                        likes: "203",
                        image: null
                    },
                    {
                        id: 'blog3',
                        title: "Building Suspense in Modern Narratives",
                        excerpt: "Master the techniques of creating tension and mystery in your stories, drawing inspiration from classic detective fiction and psychological thrillers.",
                        author: "Victoria Shadows",
                        date: "Jan 10, 2024",
                        readTime: "10 min read",
                        views: "3.1K",
                        likes: "289",
                        image: null
                    }
                ]);
            }, 1000);
        });
    }

    // Display featured blogs
    displayFeaturedBlogs(blogs) {
        const container = document.getElementById('blogsGrid');
        if (!container) return;

        blogs.forEach((blog, index) => {
            const blogCard = document.createElement('div');
            blogCard.className = 'blog-card';
            blogCard.innerHTML = `
                <div class="blog-image"></div>
                <div class="blog-content">
                    <div class="blog-meta">
                        <span>${blog.author}</span>
                        <span>•</span>
                        <span>${blog.date}</span>
                    </div>
                    <h3 class="blog-title">${blog.title}</h3>
                    <p class="blog-excerpt">${blog.excerpt}</p>
                    <div class="blog-stats">
                        <span>${blog.readTime}</span>
                        <span>${blog.views} views</span>
                        <span>${blog.likes} likes</span>
                    </div>
                </div>
            `;
            
            container.appendChild(blogCard);
            
            // Animate card appearance
            setTimeout(() => {
                anime({
                    targets: blogCard,
                    opacity: [0, 1],
                    translateY: [30, 0],
                    duration: 600,
                    delay: index * 200,
                    easing: 'easeOutCubic'
                });
            }, 1000);
        });
    }

    // Initialize scroll animations
    initializeScrollAnimations() {
        if (typeof anime !== 'undefined') {
            // Create intersection observer for scroll animations
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate');
                    }
                });
            }, observerOptions);

            // Observe elements for animation
            document.querySelectorAll('.section-header, .blog-card, .stat-item, .ai-content, .ai-visual').forEach(el => {
                observer.observe(el);
            });
        }
    }

    // Initialize admin components
    async initializeAdminComponents() {
        // Initialize analytics chart
        if (typeof echarts !== 'undefined') {
            this.initializeAnalyticsChart();
        }
        
        // Load user management data
        await this.loadUserManagement();
        
        // Initialize content moderation
        await this.initializeContentModeration();
    }

    // Initialize analytics chart
    initializeAnalyticsChart() {
        const chartDom = document.getElementById('analyticsChart');
        if (!chartDom) return;

        const myChart = echarts.init(chartDom, 'dark');
        
        // Hide loading spinner
        const loadingElement = document.getElementById('chartLoading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        const option = {
            backgroundColor: 'transparent',
            title: {
                text: 'Platform Analytics',
                textStyle: {
                    color: '#d4af37',
                    fontSize: 18,
                    fontFamily: 'Playfair Display'
                }
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: '#1a1a1a',
                borderColor: '#d4af37',
                textStyle: {
                    color: '#f8f6f0'
                }
            },
            legend: {
                data: ['Users', 'Posts', 'Views', 'AI Usage'],
                textStyle: {
                    color: '#f8f6f0'
                },
                top: 30
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: ['Jan 1', 'Jan 5', 'Jan 10', 'Jan 15', 'Jan 20', 'Jan 25', 'Jan 30'],
                axisLine: {
                    lineStyle: {
                        color: '#d4af37'
                    }
                },
                axisLabel: {
                    color: '#8a8a8a'
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: '#d4af37'
                    }
                },
                axisLabel: {
                    color: '#8a8a8a'
                },
                splitLine: {
                    lineStyle: {
                        color: '#2d2d2d'
                    }
                }
            },
            series: [
                {
                    name: 'Users',
                    type: 'line',
                    smooth: true,
                    data: [2100, 2250, 2400, 2600, 2750, 2800, 2847],
                    lineStyle: {
                        color: '#d4af37'
                    },
                    itemStyle: {
                        color: '#d4af37'
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [{
                                offset: 0, color: 'rgba(212, 175, 55, 0.3)'
                            }, {
                                offset: 1, color: 'rgba(212, 175, 55, 0.05)'
                            }]
                        }
                    }
                },
                {
                    name: 'Posts',
                    type: 'line',
                    smooth: true,
                    data: [980, 1020, 1100, 1150, 1180, 1210, 1234],
                    lineStyle: {
                        color: '#722f37'
                    },
                    itemStyle: {
                        color: '#722f37'
                    }
                },
                {
                    name: 'Views',
                    type: 'line',
                    smooth: true,
                    data: [32000, 35000, 38000, 41000, 43000, 44500, 45678],
                    lineStyle: {
                        color: '#4ade80'
                    },
                    itemStyle: {
                        color: '#4ade80'
                    }
                },
                {
                    name: 'AI Usage',
                    type: 'line',
                    smooth: true,
                    data: [2800, 2950, 3100, 3250, 3350, 3400, 3456],
                    lineStyle: {
                        color: '#60a5fa'
                    },
                    itemStyle: {
                        color: '#60a5fa'
                    }
                }
            ]
        };

        myChart.setOption(option);

        // Make chart responsive
        window.addEventListener('resize', () => {
            myChart.resize();
        });
    }

    // Load user management data
    async loadUserManagement() {
        const users = await this.getUsers();
        this.displayUsers(users);
    }

    // Get users (mock data)
    async getUsers() {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: 'user1',
                        name: 'Elena Blackwood',
                        email: 'elena@example.com',
                        role: 'author',
                        status: 'active',
                        posts: 15,
                        joinDate: '2023-06-15',
                        avatar: 'EB'
                    },
                    {
                        id: 'user2',
                        name: 'Marcus Sterling',
                        email: 'marcus@example.com',
                        role: 'author',
                        status: 'active',
                        posts: 8,
                        joinDate: '2023-08-22',
                        avatar: 'MS'
                    },
                    {
                        id: 'user3',
                        name: 'Victoria Shadows',
                        email: 'victoria@example.com',
                        role: 'author',
                        status: 'suspended',
                        posts: 23,
                        joinDate: '2023-04-10',
                        avatar: 'VS'
                    },
                    {
                        id: 'user4',
                        name: 'Admin User',
                        email: 'admin@opinian.com',
                        role: 'admin',
                        status: 'active',
                        posts: 5,
                        joinDate: '2023-01-01',
                        avatar: 'AU'
                    },
                    {
                        id: 'user5',
                        name: 'John Reader',
                        email: 'john@example.com',
                        role: 'reader',
                        status: 'active',
                        posts: 0,
                        joinDate: '2023-09-05',
                        avatar: 'JR'
                    }
                ]);
            }, 500);
        });
    }

    // Display users in table
    displayUsers(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>
                    <div class="user-info">
                        <div class="user-avatar">${user.avatar}</div>
                        <div>
                            <div class="user-name">${user.name}</div>
                            <div class="user-email">${user.email}</div>
                        </div>
                    </div>
                </td>
                <td><span class="role-badge">${user.role}</span></td>
                <td><span class="status-badge status-${user.status}">${user.status}</span></td>
                <td>${user.posts}</td>
                <td>${new Date(user.joinDate).toLocaleDateString()}</td>
                <td>
                    <div class="user-actions">
                        <button class="btn btn-small btn-outline" onclick="app.editUser('${user.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="app.viewUser('${user.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${user.status === 'active' ? 
                            `<button class="btn btn-small btn-outline" onclick="app.suspendUser('${user.id}')">
                                <i class="fas fa-pause"></i>
                            </button>` :
                            `<button class="btn btn-small btn-primary" onclick="app.activateUser('${user.id}')">
                                <i class="fas fa-play"></i>
                            </button>`
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // Initialize content moderation
    async initializeContentModeration() {
        // Tab switching functionality is handled in the HTML
        // Additional moderation features can be added here
    }

    // Global event handlers
    onPageHidden() {
        // Page is hidden - pause non-essential operations
        if (this.modules.analytics) {
            this.modules.analytics.pauseTracking();
        }
    }

    onPageVisible() {
        // Page is visible - resume operations
        if (this.modules.analytics) {
            this.modules.analytics.resumeTracking();
        }
    }

    onWindowResize() {
        // Handle window resize
        if (typeof echarts !== 'undefined') {
            // Resize any active charts
            const charts = document.querySelectorAll('[id$="Chart"]');
            charts.forEach(chartDom => {
                const chart = echarts.getInstanceByDom(chartDom);
                if (chart) {
                    chart.resize();
                }
            });
        }
    }

    onNetworkStatusChange(isOnline) {
        if (isOnline) {
            this.showSuccess('Connection restored');
            // Retry any pending operations
            this.syncPendingData();
        } else {
            this.showError('Connection lost - working offline');
        }
    }

    handleKeyboardShortcuts(e) {
        // Global keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'k':
                    e.preventDefault();
                    this.openSearch();
                    break;
                case 'n':
                    e.preventDefault();
                    this.newPost();
                    break;
                case '/':
                    e.preventDefault();
                    this.focusSearch();
                    break;
            }
        }

        // Escape key to close modals
        if (e.key === 'Escape') {
            this.closeModals();
        }
    }

    onBeforeUnload(e) {
        // Check for unsaved changes
        if (this.hasUnsavedChanges()) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    }

    // Utility methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    getUrlParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    hasUnsavedChanges() {
        // Check if there are unsaved changes in the editor or other components
        if (window.blogEditor && window.blogEditor.isDirty) {
            return true;
        }
        return false;
    }

    // Navigation methods
    redirectToLogin() {
        window.location.href = 'login.html';
    }

    redirectToDashboard() {
        const userRole = this.modules.auth.currentUser?.role;
        if (userRole === 'admin') {
            window.location.href = 'admin-dashboard.html';
        } else {
            window.location.href = 'dashboard.html';
        }
    }

    // Global notification methods
    showSuccess(message) {
        if (this.modules.notifications) {
            this.modules.notifications.show(message, 'success');
        } else {
            this.showNotification(message, 'success');
        }
    }

    showError(message) {
        if (this.modules.notifications) {
            this.modules.notifications.show(message, 'error');
        } else {
            this.showNotification(message, 'error');
        }
    }

    showWarning(message) {
        if (this.modules.notifications) {
            this.modules.notifications.show(message, 'warning');
        } else {
            this.showNotification(message, 'warning');
        }
    }

    showInfo(message) {
        if (this.modules.notifications) {
            this.modules.notifications.show(message, 'info');
        } else {
            this.showNotification(message, 'info');
        }
    }

    showNotification(message, type = 'info') {
        // Fallback notification system
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
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Global action methods
    openSearch() {
        // Implement global search functionality
        console.log('Opening global search');
    }

    newPost() {
        if (this.modules.auth.isAuthenticated()) {
            window.location.href = 'editor.html';
        } else {
            this.showError('Please log in to create a new post');
        }
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], .search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }

    closeModals() {
        // Close any open modals
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(modal => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
        });
    }

    syncPendingData() {
        // Sync any pending data when connection is restored
        console.log('Syncing pending data');
    }

    // User management methods (for admin)
    editUser(userId) {
        this.showInfo(`Editing user: ${userId}`);
    }

    viewUser(userId) {
        this.showInfo(`Viewing user details: ${userId}`);
    }

    suspendUser(userId) {
        this.showSuccess(`User ${userId} suspended successfully`);
        // Refresh user list
        setTimeout(() => {
            this.loadUserManagement();
        }, 1000);
    }

    activateUser(userId) {
        this.showSuccess(`User ${userId} activated successfully`);
        // Refresh user list
        setTimeout(() => {
            this.loadUserManagement();
        }, 1000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.app = new OpinianApp();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OpinianApp;
}