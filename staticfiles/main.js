/*
 * UniBooks - Client scripts
 * Modern interactions: sidebar toggle, toast notifications, small UX improvements
 * Uses vanilla JS, accessible and lightweight.
 */

function setupAuthForm() {
    const form = document.querySelector('.auth-form');
    if (!form) return;

    const submitBtn = form.querySelector('.btn-login');

    form.addEventListener('submit', function () {
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            submitBtn.setAttribute('aria-busy', 'true');
        }
    });

    // Micro-feedback on inputs
    const inputs = form.querySelectorAll('input');
    inputs.forEach((input) => {
        const wrapper = input.closest('.input-with-icon');
        if (!wrapper) return;
        input.addEventListener('focus', () => wrapper.classList.add('focus'));
        input.addEventListener('blur', () => wrapper.classList.remove('focus'));
    });
}

function showToast(message, type = 'info', timeout = 3200) {
    const container = document.getElementById('toast-container') || document.body;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'status');

    const icon = document.createElement('div');
    icon.className = 'toast-icon';
    icon.innerHTML = type === 'success' ? '<i class="fas fa-check"></i>' : type === 'error' ? '<i class="fas fa-exclamation-triangle"></i>' : '<i class="fas fa-info-circle"></i>';

    const text = document.createElement('div');
    text.className = 'toast-text';
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);
    (container === document.body ? document.body : container).appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, timeout);
}

function setupFormValidation() {
    const missingRequestForm = document.querySelector('.ub-form-modern');
    if (!missingRequestForm) return;

    missingRequestForm.addEventListener('submit', function (e) {
        const textarea = this.querySelector('textarea[name="content"]');
        const submitBtn = this.querySelector('button[type="submit"]');

        if (textarea && textarea.value.trim().length < 10) {
            e.preventDefault();
            textarea.classList.add('input-error');
            textarea.focus();
            showToast('La justification doit contenir au moins 10 caractères.', 'error');
            return false;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Envoi en cours...';
        }
    });
}

function setupNotifications() {
    // Header bell dot: hide it on pages where the user has opened /notifications/
    // The server marks notifications as read on the notifications page, but to provide
    // a responsive UX we also remove the visual dot if the user opens the notifications
    // pane in the current session (or views the notifications page).
    const notifDot = document.querySelector('.notif-dot');
    // If we're on the notifications page, remove the dot immediately (server also marks read)
    if (window.location.pathname.replace(/\/$/, '') === document.querySelector('.nav-link[href$="/notifications/"]')?.getAttribute('href')?.replace(/\/$/, '') || window.location.pathname.replace(/\/$/, '') === '/notifications') {
        if (notifDot) notifDot.remove();
    }

    // Also listen for clicks on the bell to proactively remove the dot client-side
    const notifBtn = document.querySelector('.notif-btn');
    if (notifBtn) {
        notifBtn.addEventListener('click', (e) => {
            // Let the link navigate, but remove the dot for immediate feedback
            if (notifDot) notifDot.remove();
        });
    }

    // Additionally, remove unread-highlight on individual notification items when hovered
    const unreadItems = document.querySelectorAll('.borrow-card.unread-highlight, .notif-card.unread-highlight');
    unreadItems.forEach((item) => {
        item.addEventListener('mouseenter', function () {
            setTimeout(() => {
                this.classList.remove('unread-highlight');
                const dot = this.querySelector('.status-dot');
                if (dot) dot.classList.remove('active');
            }, 800);
        });
    });
}

function highlightActiveLink() {
    const currentPath = window.location.pathname.replace(/\/$/, '');
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach((link) => {
        const href = (link.getAttribute('href') || '').replace(/\/$/, '');
        if (href && href === currentPath) {
            const li = link.closest('.nav-item');
            if (li) li.classList.add('active');
            link.classList.add('active-link');
        }
    });
}

function initSidebarToggle() {
    const toggle = document.querySelector('.mobile-toggle');
    const sidebar = document.getElementById('site-sidebar');
    const overlay = document.getElementById('overlay');

    if (!toggle || !sidebar) return;

    // Set sensible default: sidebar visible on large screens, hidden on small screens
    const isMobile = () => window.innerWidth <= 900;
    if (isMobile()) {
        sidebar.hidden = true;
        if (overlay) overlay.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
    } else {
        sidebar.hidden = false;
        sidebar.classList.add('open');
        if (overlay) { overlay.hidden = true; overlay.style.opacity = '0'; }
        toggle.setAttribute('aria-expanded', 'true');
    }

    const openSidebar = () => {
        sidebar.hidden = false;
        sidebar.classList.add('open');
        if (overlay) { overlay.hidden = false; overlay.style.opacity = '1'; }
        toggle.setAttribute('aria-expanded', 'true');
    };

    const closeSidebar = () => {
        sidebar.classList.remove('open');
        if (overlay) overlay.style.opacity = '0';
        toggle.setAttribute('aria-expanded', 'false');
        setTimeout(() => {
            sidebar.hidden = true;
            if (overlay) overlay.hidden = true;
        }, 220);
    };

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        if (sidebar.hidden) openSidebar(); else closeSidebar();
    });

    overlay && overlay.addEventListener('click', closeSidebar);

    // close with Escape
    document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') closeSidebar();
    });

    // On mobile, when a nav link is clicked, close the sidebar to reveal content
    const navLinks = sidebar.querySelectorAll('.nav-link');
    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            if (isMobile()) closeSidebar();
        });
    });

    // Keep sidebar state consistent on resize
    let resizeTimer = null;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (isMobile()) {
                sidebar.hidden = true;
                sidebar.classList.remove('open');
                if (overlay) { overlay.hidden = true; overlay.style.opacity = '0'; }
                toggle.setAttribute('aria-expanded', 'false');
            } else {
                sidebar.hidden = false;
                sidebar.classList.add('open');
                if (overlay) { overlay.hidden = true; overlay.style.opacity = '0'; }
                toggle.setAttribute('aria-expanded', 'true');
            }
        }, 150);
    });
}

function setupCommentReplies() {
    // Toggle inline reply forms and enforce max depth via data-level attribute
    document.addEventListener('click', function (e) {
        const replyBtn = e.target.closest('.reply-btn');
        if (replyBtn) {
            const parentId = replyBtn.getAttribute('data-parent');
            const level = parseInt(replyBtn.getAttribute('data-level') || '0', 10);
            // Only allow reply if level is 0 or 1 (max two nested levels)
            if (level > 1) return;
            const container = document.querySelector(`.reply-form-container[data-for="${parentId}"]`);
            if (!container) return;
            const isVisible = container.style.display !== 'none' && container.style.display !== '';
            // Close any other open reply forms for a cleaner UX
            document.querySelectorAll('.reply-form-container').forEach(c => {
                if (c !== container) c.style.display = 'none';
            });
            container.style.display = isVisible ? 'none' : 'block';
            if (!isVisible) {
                const ta = container.querySelector('textarea');
                if (ta) {
                    ta.focus();
                    // small scroll into view
                    setTimeout(() => container.scrollIntoView({behavior: 'smooth', block: 'center'}), 120);
                }
            }
            return;
        }

        const cancel = e.target.closest('.cancel-reply');
        if (cancel) {
            const parentId = cancel.getAttribute('data-parent');
            const container = document.querySelector(`.reply-form-container[data-for="${parentId}"]`);
            if (container) container.style.display = 'none';
            return;
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    setupFormValidation();
    setupNotifications();
    highlightActiveLink();
    setupAuthForm();
    initSidebarToggle();
    setupCommentReplies();
    // Reveal on scroll (fade+slide) for elements with .reveal
    if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    // If you want the animation only once, unobserve after visible
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        document.querySelectorAll('.reveal').forEach(el => io.observe(el));
    } else {
        // Fallback: reveal immediately if IntersectionObserver not supported
        document.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'));
    }
});