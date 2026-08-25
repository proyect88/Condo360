// ============================================
// Admin Panel JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // Sidebar Toggle (Mobile)
    // ============================================
    const sidebarToggle = document.getElementById('sidebarToggle');
    const adminSidebar = document.querySelector('.admin-sidebar');
    
    if (sidebarToggle && adminSidebar) {
        sidebarToggle.addEventListener('click', function() {
            adminSidebar.classList.toggle('open');
        });
    }

    // ============================================
    // Table Search/Filter
    // ============================================
    document.querySelectorAll('.table-search').forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.table-container').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });

    // ============================================
    // Bulk Actions
    // ============================================
    document.querySelectorAll('.select-all').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const container = this.closest('.table-container');
            const checkboxes = container.querySelectorAll('tbody input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = this.checked);
        });
    });

    // ============================================
    // Delete Confirmation
    // ============================================
    document.querySelectorAll('.delete-confirm').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.dataset.message || '¿Estás seguro de eliminar este elemento?';
            if (confirm(message)) {
                this.closest('form').submit();
            }
        });
    });

    // ============================================
    // Status Update (AJAX)
    // ============================================
    document.querySelectorAll('.status-update').forEach(select => {
        select.addEventListener('change', async function() {
            const ticketId = this.dataset.ticketId;
            const status = this.value;
            const url = `/admin/tickets/${ticketId}/actualizar`;
            
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]');
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        ...(csrfToken ? { 'X-CSRFToken': csrfToken.getAttribute('content') } : {})
                    },
                    body: `status=${status}`
                });
                
                if (response.ok) {
                    window.showNotification('Estado actualizado correctamente', 'success');
                    // Actualizar badge de color
                    const badge = this.closest('td').querySelector('.badge');
                    if (badge) {
                        badge.className = `badge badge-${getStatusColor(status)}`;
                        badge.textContent = getStatusLabel(status);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                window.showNotification('Error al actualizar estado', 'danger');
            }
        });
    });

    // ============================================
    // Charts (Dashboard)
    // ============================================
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        const chartData = container.dataset.chartData;
        const chartType = container.dataset.chartType || 'bar';
        
        if (chartData && typeof Chart !== 'undefined') {
            try {
                const data = JSON.parse(chartData);
                const ctx = container.querySelector('canvas');
                
                if (ctx) {
                    new Chart(ctx, {
                        type: chartType,
                        data: data,
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                }
            } catch (e) {
                console.error('Error al renderizar chart:', e);
            }
        }
    });

    // ============================================
    // Toast Notifications
    // ============================================
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            // Crear contenedor si no existe
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
                width: 100%;
            `;
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `notification notification-${type}`;
        toast.style.animation = 'slideInRight 0.3s ease';
        
        const icons = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <i class="fas ${icons[type] || icons.info}"></i>
                <span>${message}</span>
            </div>
            <button class="close-notification">&times;</button>
        `;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
        
        toast.querySelector('.close-notification').addEventListener('click', () => {
            toast.remove();
        });
    };

    // ============================================
    // Form Validation (Admin)
    // ============================================
    document.querySelectorAll('.admin-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            this.querySelectorAll('.required').forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            // Email validation
            this.querySelectorAll('input[type="email"]').forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    field.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                window.showToast('Por favor, revisa los campos resaltados', 'warning');
            }
        });
    });

    // ============================================
    // Helper Functions
    // ============================================
    function getStatusColor(status) {
        const colors = {
            'new': 'primary',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    function getStatusLabel(status) {
        const labels = {
            'new': 'Nuevo',
            'in_progress': 'En Progreso',
            'resolved': 'Resuelto',
            'closed': 'Cerrado',
            'cancelled': 'Cancelado'
        };
        return labels[status] || status;
    }
    
    function isValidEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }

    // ============================================
    // Refresh Stats (AJAX)
    // ============================================
    async function refreshStats() {
        try {
            const response = await fetch('/admin/api/tickets/stats');
            if (response.ok) {
                const stats = await response.json();
                
                document.querySelector('.stat-total')?.textContent = stats.total;
                document.querySelector('.stat-pending')?.textContent = stats.pending;
                document.querySelector('.stat-resolved')?.textContent = stats.resolved;
                document.querySelector('.stat-critical')?.textContent = stats.critical;
            }
        } catch (error) {
            console.error('Error al actualizar estadísticas:', error);
        }
    }
    
    // Actualizar cada 30 segundos
    if (document.querySelector('.dashboard-stats')) {
        setInterval(refreshStats, 30000);
    }

    console.log('Admin Panel - Condo Services 360 Inicializado');
});

// Confirmaciones sin atributos onsubmit/onclick inline (CSP estricta)
document.addEventListener('submit', function (e) {
    var form = e.target;
    if (form.matches('form[data-confirm]')) {
        if (!window.confirm(form.getAttribute('data-confirm'))) {
            e.preventDefault();
        }
    }
}, true);
