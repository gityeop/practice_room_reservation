/**
 * 토스트 알림 시스템
 * 페이지 상단에 임시 알림을 표시합니다
 */

class ToastNotification {
    constructor() {
        this.toasts = [];
        this.initStyles();
        this.createContainer(); // 초기화 시 컨테이너 생성
    }

    /**
     * 토스트 알림 스타일을 초기화합니다
     */
    initStyles() {
        // 이미 스타일이 적용되어 있는지 확인
        if (document.getElementById('toast-notification-styles')) return;
        
        // 스타일 요소 생성
        const style = document.createElement('style');
        style.id = 'toast-notification-styles';
        style.textContent = `
            .toast-notification-container {
                position: fixed;
                top: 16px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-width: 320px;
                pointer-events: none; /* 컨테이너가 마우스 이벤트를 가로채지 않도록 함 */
            }
            
            .toast-notification {
                padding: 12px 16px;
                background-color: #333;
                color: white;
                border-radius: 4px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                font-size: 14px;
                opacity: 0;
                transform: translateY(-20px);
                transition: opacity 0.3s, transform 0.3s;
                pointer-events: auto; /* 토스트 자체는 마우스 이벤트를 받도록 함 */
                text-align: center;
                min-width: 250px;
            }
            
            .toast-notification.show {
                opacity: 1;
                transform: translateY(0);
            }
            
            .toast-notification.success {
                background-color: #28a745;
            }
            
            .toast-notification.error {
                background-color: #dc3545;
            }
            
            .toast-notification.info {
                background-color: #17a2b8;
            }
            
            .toast-notification.warning {
                background-color: #ffc107;
                color: #333;
            }
            
            .toast-notification .close-toast {
                position: absolute;
                right: 10px;
                top: 10px;
                cursor: pointer;
                color: inherit;
                opacity: 0.7;
            }
            
            .toast-notification .close-toast:hover {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * 토스트 컨테이너를 생성하거나 가져옵니다
     */
    createContainer() {
        // 이미 컨테이너가 존재하는지 확인
        if (document.querySelector('.toast-notification-container')) return;
        
        // 새 컨테이너 생성
        const container = document.createElement('div');
        container.className = 'toast-notification-container';
        
        // body의 첫 번째 자식으로 추가 (DOM 트리 최상단에 위치)
        if (document.body.firstChild) {
            document.body.insertBefore(container, document.body.firstChild);
        } else {
            document.body.appendChild(container);
        }
    }

    /**
     * 토스트 컨테이너를 가져옵니다
     */
    getContainer() {
        let container = document.querySelector('.toast-notification-container');
        if (!container) {
            this.createContainer();
            container = document.querySelector('.toast-notification-container');
        }
        return container;
    }

    /**
     * 새로운 토스트 알림을 표시합니다
     * @param {string} message - 표시할 메시지
     * @param {string} type - 알림 타입 (success, error, info, warning)
     * @param {number} duration - 표시 시간 (밀리초)
     * @returns {HTMLElement} 생성된 토스트 요소
     */
    show(message, type = 'info', duration = 3000) {
        const container = this.getContainer();
        
        // 토스트 요소 생성
        const toast = document.createElement('div');
        toast.className = `toast-notification ${type}`;
        
        // 닫기 버튼 추가
        const closeBtn = document.createElement('span');
        closeBtn.className = 'close-toast';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => this.close(toast);
        
        // 내용 추가
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        toast.appendChild(messageSpan);
        toast.appendChild(closeBtn);
        
        // 컨테이너에 추가
        container.appendChild(toast);
        
        // 토스트 배열에 추가
        this.toasts.push(toast);
        
        // 표시 애니메이션
        setTimeout(() => toast.classList.add('show'), 10);
        
        // 시간이 지난 후 자동으로 닫기
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) this.close(toast);
            }, duration);
        }
        
        return toast;
    }

    /**
     * 토스트 알림을 닫습니다
     * @param {HTMLElement} toast - 닫을 토스트 요소
     */
    close(toast) {
        toast.classList.remove('show');
        
        // 애니메이션 완료 후 요소 제거
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
            this.toasts = this.toasts.filter(t => t !== toast);
        }, 300);
    }

    /**
     * 모든 토스트 알림을 닫습니다
     */
    closeAll() {
        [...this.toasts].forEach(toast => this.close(toast));
    }

    /**
     * 성공 토스트 표시
     */
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    /**
     * 오류 토스트 표시
     */
    error(message, duration = 3000) {
        return this.show(message, 'error', duration);
    }

    /**
     * 정보 토스트 표시
     */
    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    /**
     * 경고 토스트 표시
     */
    warning(message, duration = 3000) {
        return this.show(message, 'warning', duration);
    }
}

// 싱글톤 인스턴스 생성
if (!window.toast) {
    window.toast = new ToastNotification();
}

// Flash 메시지 자동 변환
document.addEventListener('DOMContentLoaded', function() {
    // Flash 메시지 처리
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(flashElement) {
        const message = flashElement.textContent.trim();
        let type = 'info';
        
        // 메시지 타입 결정
        if (flashElement.classList.contains('alert-success')) type = 'success';
        if (flashElement.classList.contains('alert-danger') || flashElement.classList.contains('alert-error')) type = 'error';
        if (flashElement.classList.contains('alert-warning')) type = 'warning';
        if (flashElement.classList.contains('alert-info')) type = 'info';
        
        // 토스트 표시
        window.toast.show(message, type);
        
        // 기존 flash 메시지 요소 숨기기
        flashElement.style.display = 'none';
    });
});
