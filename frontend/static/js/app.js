// Booking App for Telegram Mini App
class BookingApp {
    constructor() {
        this.masterSlug = this.getMasterSlugFromURL();
        this.apiBase = window.location.origin + '/api';
        this.currentState = 'masterCard'; // masterCard, serviceSelection, dateSelection, timeSelection, confirmation, success
        this.selectedService = null;
        this.selectedDate = null;
        this.selectedTime = null;
        this.masterData = null;
        this.services = [];
        this.availableSlots = [];

        this.init();
    }

    getMasterSlugFromURL() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[pathParts.length - 1];
    }

    async init() {
        try {
            await this.loadMasterData();
            await this.loadServices();
            this.showMasterCard();
        } catch (error) {
            this.showError('Ошибка загрузки данных мастера');
            console.error(error);
        }
    }

    async loadMasterData() {
        const response = await fetch(`${this.apiBase}/masters/${this.masterSlug}`);
        if (!response.ok) throw new Error('Master not found');
        this.masterData = await response.json();
    }

    async loadServices() {
        if (!this.masterData) return;
        const response = await fetch(`${this.apiBase}/masters/${this.masterData.id}/services`);
        if (!response.ok) throw new Error('Failed to load services');
        this.services = await response.json();
    }

    showMasterCard() {
        document.getElementById('masterName').textContent = this.masterData.first_name;
        document.getElementById('masterSpecialization').textContent = this.masterData.specialization || 'Специалист';
        document.getElementById('masterDescription').textContent = this.masterData.description || '';

        // Load schedule info
        this.loadSchedule();

        // Show service selection
        this.showServiceSelection();
    }

    async loadSchedule() {
        try {
            const response = await fetch(`${this.apiBase}/masters/${this.masterData.id}/work-schedules`);
            const schedules = await response.json();

            const daysOfWeek = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
            let scheduleText = '';

            schedules.forEach(schedule => {
                const dayName = daysOfWeek[schedule.day_of_week];
                scheduleText += `${dayName} ${schedule.start_time} - ${schedule.end_time}\n`;
            });

            document.getElementById('masterSchedule').textContent =
                scheduleText || 'График не установлен';
        } catch (error) {
            console.error('Failed to load schedule:', error);
        }
    }

    showServiceSelection() {
        this.hideAll();
        document.getElementById('serviceSelection').style.display = 'block';

        const servicesList = document.getElementById('servicesList');
        servicesList.innerHTML = '';

        if (this.services.length === 0) {
            servicesList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📋</div><div>Нет доступных услуг</div></div>';
            return;
        }

        this.services.forEach(service => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.cursor = 'pointer';
            card.onclick = () => this.selectService(service);

            const price = service.price ? `₽${service.price.toLocaleString()}` : 'Уточнить';
            const duration = `${service.duration_minutes} мин`;

            card.innerHTML = `
                <div class="card-title">${service.name}</div>
                <div class="card-description">${service.description || ''}</div>
                <div style="margin-top: var(--spacing-md); display: flex; justify-content: space-between; font-size: 14px; color: var(--gray-500);">
                    <span>⏱ ${duration}</span>
                    <span class="font-bold" style="color: var(--primary);">${price}</span>
                </div>
            `;
            servicesList.appendChild(card);
        });
    }

    selectService(service) {
        this.selectedService = service;
        this.showDateSelection();
    }

    showDateSelection() {
        this.hideAll();
        document.getElementById('dateSelection').style.display = 'block';

        const today = new Date();
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 30);

        document.getElementById('targetDate').min = today.toISOString().split('T')[0];
        document.getElementById('targetDate').max = maxDate.toISOString().split('T')[0];
        document.getElementById('targetDate').value = today.toISOString().split('T')[0];

        document.getElementById('targetDate').addEventListener('change', (e) => {
            this.selectedDate = e.target.value;
            this.loadAvailableSlots();
        });

        // Load slots for today
        this.selectedDate = today.toISOString().split('T')[0];
        this.loadAvailableSlots();
    }

    async loadAvailableSlots() {
        if (!this.selectedDate || !this.selectedService) return;

        try {
            const response = await fetch(
                `${this.apiBase}/available-slots/${this.masterSlug}?` +
                `service_id=${this.selectedService.id}&target_date=${this.selectedDate}`
            );

            if (!response.ok) throw new Error('Failed to load slots');

            const data = await response.json();
            this.availableSlots = data.slots;

            if (this.availableSlots.length > 0) {
                this.showTimeSelection();
            }
        } catch (error) {
            this.showError('Нет доступных слотов на эту дату');
            console.error(error);
        }
    }

    showTimeSelection() {
        this.hideAll();
        document.getElementById('timeSelection').style.display = 'block';

        const timeSlots = document.getElementById('timeSlots');
        timeSlots.innerHTML = '';

        if (this.availableSlots.length === 0) {
            timeSlots.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><div>Нет доступных времён</div></div>';
            return;
        }

        this.availableSlots.forEach(slot => {
            const startTime = new Date(slot.start_time);
            const timeStr = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}`;

            const btn = document.createElement('button');
            btn.className = 'time-slot';
            btn.textContent = timeStr;
            btn.onclick = () => this.selectTime(slot);
            timeSlots.appendChild(btn);
        });
    }

    selectTime(slot) {
        this.selectedTime = slot;
        this.showConfirmation();
    }

    showConfirmation() {
        this.hideAll();
        document.getElementById('confirmation').style.display = 'block';

        document.getElementById('confirmServiceName').textContent = this.selectedService.name;
        document.getElementById('confirmServiceDetails').textContent =
            `${this.selectedService.duration_minutes} мин • ₽${this.selectedService.price || 0}`;

        const startTime = new Date(this.selectedTime.start_time);
        const dateStr = startTime.toLocaleDateString('ru-RU');
        const timeStr = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}`;

        document.getElementById('confirmDateTime').textContent = `${dateStr}, ${timeStr}`;
    }

    async submitBooking() {
        const clientPhone = document.getElementById('clientPhone').value;
        const telegramId = this.getTelegramId();

        if (!telegramId) {
            this.showError('Не удалось получить Telegram ID. Откройте приложение через Telegram.');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/bookings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    master_slug: this.masterSlug,
                    telegram_id: telegramId,
                    service_id: this.selectedService.id,
                    start_time: this.selectedTime.start_time,
                    client_phone: clientPhone,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка при создании бронирования');
            }

            this.showSuccess();
        } catch (error) {
            this.showError(error.message);
            console.error(error);
        }
    }

    showSuccess() {
        this.hideAll();
        document.getElementById('successMessage').style.display = 'block';
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    backToDateSelection() {
        this.selectedTime = null;
        this.showDateSelection();
    }

    backToTimeSelection() {
        this.selectedDate = null;
        this.showTimeSelection();
    }

    previousMonth() {
        const input = document.getElementById('targetDate');
        const date = new Date(input.value);
        date.setMonth(date.getMonth() - 1);
        input.value = date.toISOString().split('T')[0];
        this.selectedDate = input.value;
        this.loadAvailableSlots();
    }

    nextMonth() {
        const input = document.getElementById('targetDate');
        const date = new Date(input.value);
        date.setMonth(date.getMonth() + 1);
        input.value = date.toISOString().split('T')[0];
        this.selectedDate = input.value;
        this.loadAvailableSlots();
    }

    reset() {
        this.selectedService = null;
        this.selectedDate = null;
        this.selectedTime = null;
        this.showServiceSelection();
    }

    hideAll() {
        document.getElementById('masterCard').style.display = 'none';
        document.getElementById('serviceSelection').style.display = 'none';
        document.getElementById('dateSelection').style.display = 'none';
        document.getElementById('timeSelection').style.display = 'none';
        document.getElementById('confirmation').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';
    }

    getTelegramId() {
        // In real Mini App, this comes from Telegram Web App API
        if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
            return String(window.Telegram.WebApp.initDataUnsafe.user.id);
        }
        // Fallback for development
        return localStorage.getItem('telegramId') || String(Math.random() * 1e9 | 0);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BookingApp();
});
