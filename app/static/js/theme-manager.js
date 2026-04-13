/**
 * Theme Manager - Dark Mode Toggle
 * Manages light/dark theme with localStorage persistence
 * and respects system preference on first visit.
 */
class ThemeManager {
    constructor() {
        this.storageKey = 'aldudu-theme';
        this.currentTheme = this.getStoredTheme();
        this.init();
    }

    init() {
        // Apply theme immediately to prevent flash
        this.applyTheme(this.currentTheme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!this.getStoredTheme()) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    /**
     * Get stored theme from localStorage
     * Falls back to system preference, then 'light'
     */
    getStoredTheme() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) return stored;

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }

        return 'light';
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        this.currentTheme = theme;
    }

    /**
     * Toggle between light and dark
     */
    toggle() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        localStorage.setItem(this.storageKey, newTheme);

        // Dispatch custom event for other scripts to listen
        window.dispatchEvent(new CustomEvent('theme:change', { detail: { theme: newTheme } }));
    }

    /**
     * Set specific theme
     */
    setTheme(theme) {
        if (!['light', 'dark'].includes(theme)) {
            throw new Error('Invalid theme. Must be "light" or "dark"');
        }
        this.applyTheme(theme);
        localStorage.setItem(this.storageKey, theme);
        window.dispatchEvent(new CustomEvent('theme:change', { detail: { theme } }));
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Check if currently in dark mode
     */
    isDark() {
        return this.currentTheme === 'dark';
    }
}

// Initialize global instance
window.ThemeManager = new ThemeManager();

// Auto-apply theme before DOMContentLoaded to prevent flash
(function() {
    const theme = localStorage.getItem('aldudu-theme');
    if (theme === 'dark' || (!theme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
})();
