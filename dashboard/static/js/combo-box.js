/**
 * Combo Box / Dropdown Component
 * Vanilla JavaScript implementation with search functionality
 * Dark theme optimized
 */

class ComboBox {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`ComboBox: Container "${containerId}" not found`);
            return;
        }

        this.options = {
            placeholder: options.placeholder || 'Select...',
            label: options.label || '',
            items: options.items || [], // Array of { value, label }
            onChange: options.onChange || (() => {}),
            darkTheme: options.darkTheme !== false
        };

        this.isOpen = false;
        this.selectedValue = '';
        this.inputValue = '';
        this.filteredItems = [...this.options.items];

        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        const themeClasses = this.options.darkTheme ? {
            container: 'bg-surface-container-high border-surface-container-highest text-on-surface',
            input: 'bg-surface-container-high border-surface-container-highest text-on-surface placeholder-outline',
            dropdown: 'bg-surface-container-high border-surface-container-highest shadow-2xl',
            item: 'text-on-surface hover:bg-surface-container-highest',
            itemSecondary: 'text-outline',
            checkIcon: 'text-primary'
        } : {
            container: 'bg-white border-gray-300 text-gray-900',
            input: 'bg-white border-gray-300 text-gray-900 placeholder-gray-500',
            dropdown: 'bg-white border-gray-300 shadow-lg',
            item: 'text-gray-900 hover:bg-gray-100',
            itemSecondary: 'text-gray-500',
            checkIcon: 'text-gray-600'
        };

        // Use inputValue if set, otherwise show placeholder
        const displayValue = this.inputValue || '';

        this.container.innerHTML = `
            ${this.options.label ? `<label class="block text-sm font-medium mb-1 ${this.options.darkTheme ? 'text-on-surface-variant' : 'text-gray-700'}">${this.options.label}</label>` : ''}
            <div class="relative w-full">
                <div class="relative">
                    <input
                        type="text"
                        class="w-full px-4 py-2.5 pr-10 border rounded-lg bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-colors ${themeClasses.input}"
                        placeholder="${this.options.placeholder}"
                        value="${displayValue}"
                        readonly
                    />
                    <button
                        type="button"
                        class="absolute inset-y-0 right-0 flex items-center px-3 ${this.options.darkTheme ? 'text-outline hover:text-on-surface' : 'text-gray-400 hover:text-gray-600'}"
                    >
                        <svg class="w-4 h-4 transition-transform ${this.isOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                    </button>
                </div>

                <div class="dropdown-menu absolute z-50 w-full mt-1 border rounded-lg max-h-60 overflow-auto hidden ${themeClasses.dropdown}">
                    <div class="items-container"></div>
                </div>
            </div>
        `;

        this.updateDropdownItems(themeClasses);
        
        // Ensure input shows selected value after render
        const input = this.container.querySelector('input');
        if (input && this.inputValue) {
            input.value = this.inputValue;
        }
    }

    updateDropdownItems(themeClasses) {
        const itemsContainer = this.container.querySelector('.items-container');
        if (!itemsContainer) return;

        if (this.filteredItems.length > 0) {
            itemsContainer.innerHTML = this.filteredItems.map((item, index) => `
                <div
                    data-index="${index}"
                    data-value="${item.value}"
                    class="px-4 py-2.5 cursor-pointer flex items-center justify-between group ${themeClasses.item}"
                >
                    <div>
                        <div class="font-medium">${item.label}</div>
                        ${item.secondary ? `<div class="text-xs ${themeClasses.itemSecondary}">${item.secondary}</div>` : ''}
                    </div>
                    ${this.selectedValue === item.value ? `
                        <svg class="w-4 h-4 ${themeClasses.checkIcon}" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                        </svg>
                    ` : ''}
                </div>
            `).join('');
        } else {
            itemsContainer.innerHTML = `<div class="px-4 py-3 ${themeClasses.itemSecondary}">No options found</div>`;
        }
    }

    attachEventListeners() {
        const input = this.container.querySelector('input');
        const dropdownBtn = this.container.querySelector('button');
        const dropdown = this.container.querySelector('.dropdown-menu');

        if (!input || !dropdownBtn || !dropdown) return;

        // Toggle dropdown
        dropdownBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggle();
        });

        // Input changes (for search/filtering)
        input.addEventListener('input', (e) => {
            this.inputValue = e.target.value;
            this.filterItems();
            this.open();
        });

        // Focus
        input.addEventListener('focus', () => {
            this.open();
        });

        // Blur - restore selected value if user typed something invalid
        input.addEventListener('blur', () => {
            // If user typed something that doesn't match a selection, restore the selected value
            if (this.selectedValue && this.inputValue) {
                setTimeout(() => {
                    input.value = this.inputValue;
                }, 100);
            }
        });

        // Item selection
        dropdown.addEventListener('click', (e) => {
            const item = e.target.closest('[data-index]');
            if (item) {
                const index = parseInt(item.dataset.index);
                this.selectItem(this.filteredItems[index]);
            }
        });

        // Keyboard navigation
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.open();
                this.focusFirstItem();
            } else if (e.key === 'Escape') {
                this.close();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (this.filteredItems.length > 0) {
                    this.selectItem(this.filteredItems[0]);
                }
            }
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });

        // Close on scroll (only on window scroll, not dropdown scroll)
        window.addEventListener('scroll', (e) => {
            // Don't close if scrolling inside the dropdown
            if (e.target === this.dropdown || this.dropdown?.contains(e.target)) {
                return;
            }
            this.close();
        }, { passive: true });
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        const dropdown = this.container.querySelector('.dropdown-menu');
        const chevron = this.container.querySelector('button svg');
        if (dropdown) {
            dropdown.classList.remove('hidden');
            dropdown.style.zIndex = '50';  // Ensure dropdown is above other elements
        }
        if (chevron) chevron.classList.add('rotate-180');
    }

    close() {
        this.isOpen = false;
        const dropdown = this.container.querySelector('.dropdown-menu');
        const chevron = this.container.querySelector('button svg');
        if (dropdown) {
            dropdown.classList.add('hidden');
            dropdown.style.zIndex = '';
        }
        if (chevron) chevron.classList.remove('rotate-180');
    }

    filterItems() {
        const search = this.inputValue.toLowerCase();
        this.filteredItems = this.options.items.filter(item =>
            item.label.toLowerCase().includes(search) ||
            (item.secondary && item.secondary.toLowerCase().includes(search))
        );
        this.updateDropdownItems(this.options.darkTheme ? {
            item: 'text-on-surface hover:bg-surface-container-highest',
            itemSecondary: 'text-outline',
            checkIcon: 'text-primary'
        } : {
            item: 'text-gray-900 hover:bg-gray-100',
            itemSecondary: 'text-gray-500',
            checkIcon: 'text-gray-600'
        });
    }

    selectItem(item) {
        if (!item) return;
        
        console.log('ComboBox: Selecting item', item.label, item.value);
        
        this.selectedValue = item.value;
        this.inputValue = item.label;

        // IMMEDIATELY update the input field value in the DOM
        const input = this.container.querySelector('input');
        if (input) {
            input.value = item.label;
            console.log('ComboBox: Input value set to', input.value);
        }

        // Update checkmark in dropdown
        this.updateDropdownItems(this.options.darkTheme ? {
            item: 'text-on-surface hover:bg-surface-container-highest',
            itemSecondary: 'text-outline',
            checkIcon: 'text-primary'
        } : {
            item: 'text-gray-900 hover:bg-gray-100',
            itemSecondary: 'text-gray-500',
            checkIcon: 'text-gray-600'
        });

        // Close dropdown
        this.close();

        // Trigger callback AFTER updating UI
        this.options.onChange(item);
    }

    focusFirstItem() {
        const firstItem = this.container.querySelector('[data-index="0"]');
        if (firstItem) firstItem.focus();
    }

    // Public methods
    setItems(items) {
        console.log('ComboBox: setItems called with', items.length, 'items');
        console.log('ComboBox: Current selectedValue is', this.selectedValue);
        
        // Save current selection
        const savedSelectedValue = this.selectedValue;
        const savedInputValue = this.inputValue;
        
        this.options.items = items;
        this.filteredItems = [...items];
        
        // Update dropdown items with checkmarks
        const themeClasses = this.options.darkTheme ? {
            item: 'text-on-surface hover:bg-surface-container-highest',
            itemSecondary: 'text-outline',
            checkIcon: 'text-primary'
        } : {
            item: 'text-gray-900 hover:bg-gray-100',
            itemSecondary: 'text-gray-500',
            checkIcon: 'text-gray-600'
        };
        
        this.updateDropdownItems(themeClasses);

        // ALWAYS update input field to show selected value
        const input = this.container.querySelector('input');
        if (input && this.inputValue) {
            input.value = this.inputValue;
            console.log('ComboBox: Input restored to', this.inputValue);
        }
    }

    setValue(value) {
        const item = this.options.items.find(i => i.value === value);
        if (item) {
            this.selectItem(item);
        }
    }

    getValue() {
        return this.selectedValue;
    }

    clear() {
        this.selectedValue = '';
        this.inputValue = '';
        const input = this.container.querySelector('input');
        if (input) input.value = '';
        this.filterItems();
    }
}

window.ComboBox = ComboBox;
