/**
 * 문화콘텐츠학과 실습실 예약 시스템 메인 자바스크립트 파일
 * 날짜 및 시간 검증, 폼 제출, 메시지 표시 등의 클라이언트 측 기능을 처리합니다.
 */

document.addEventListener('DOMContentLoaded', function() {
    // 플래시 메시지 자동 숨김 기능 초기화
    initFlashMessages();
    
    // 예약 폼 검증 기능 초기화
    initReservationForm();
    
    // 대시보드 기능 초기화
    initDashboard();
    
    // 관리자 기능 초기화
    initAdminFeatures();
});

/**
 * 플래시 메시지를 자동으로 숨기는 기능을 초기화합니다.
 */
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    if (flashMessages.length > 0) {
        // 3초 후에 메시지 숨기기
        setTimeout(function() {
            flashMessages.forEach(message => {
                // 부드러운 페이드아웃 효과 적용
                message.style.opacity = '1';
                message.style.transition = 'opacity 0.5s ease';
                
                setTimeout(function() {
                    message.style.opacity = '0';
                    
                    setTimeout(function() {
                        message.style.display = 'none';
                    }, 500);
                }, 100);
            });
        }, 3000);
    }
}

/**
 * 예약 폼에 관련된 기능을 초기화합니다.
 */
function initReservationForm() {
    const reservationForm = document.querySelector('form[action*="reserve"]');
    
    if (!reservationForm) return;
    
    const dateInput = document.getElementById('date');
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    // 날짜 제한 설정 (일요일만 선택 가능)
    if (dateInput) {
        // 오늘 날짜 이후부터 선택 가능하도록 설정
        const today = new Date();
        const formattedToday = formatDateForInput(today);
        dateInput.min = formattedToday;
        
        // 날짜 변경 시 일요일인지 확인
        dateInput.addEventListener('change', function() {
            validateSunday(this);
        });
    }
    
    // 시간 입력 검증
    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener('change', function() {
            validateTime();
        });
        
        endTimeInput.addEventListener('change', function() {
            validateTime();
        });
    }
    
    // 폼 제출 전 최종 검증
    if (reservationForm) {
        reservationForm.addEventListener('submit', function(event) {
            if (!validateReservationForm()) {
                event.preventDefault();
            }
        });
    }
}

/**
 * 날짜가 일요일인지 확인하고, 그렇지 않으면 경고 메시지를 표시합니다.
 * @param {HTMLInputElement} dateInput - 날짜 입력 요소
 */
function validateSunday(dateInput) {
    const selectedDate = new Date(dateInput.value);
    const dayOfWeek = selectedDate.getDay();
    
    // 일요일은 0
    if (dayOfWeek !== 0) {
        alert('일요일에만 예약할 수 있습니다.');
        dateInput.value = '';
    }
}

/**
 * 시작 시간이 종료 시간보다 이전인지 확인하고, 최소 예약 시간과 최대 예약 시간을 검증합니다.
 */
function validateTime() {
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    if (!startTimeInput || !endTimeInput || !startTimeInput.value || !endTimeInput.value) {
        return;
    }
    
    const startTime = new Date(`2023-01-01T${startTimeInput.value}`);
    const endTime = new Date(`2023-01-01T${endTimeInput.value}`);
    
    // 시작 시간이 종료 시간보다 이후인 경우
    if (startTime >= endTime) {
        alert('시작 시간은 종료 시간보다 이전이어야 합니다.');
        endTimeInput.value = '';
        return false;
    }
    
    // 예약 시간 차이 계산 (분 단위)
    const diffMinutes = (endTime - startTime) / (1000 * 60);
    
    // 최소 30분부터 예약 가능
    if (diffMinutes < 30) {
        alert('최소 30분 이상 예약해야 합니다.');
        endTimeInput.value = '';
        return false;
    }
    
    // 최대 3시간까지 예약 가능 (180분)
    if (diffMinutes > 180) {
        alert('최대 3시간까지 예약할 수 있습니다.');
        endTimeInput.value = '';
        return false;
    }
    
    return true;
}

/**
 * 예약 폼 전체를 검증합니다.
 * @returns {boolean} 폼이 유효하면 true, 그렇지 않으면 false
 */
function validateReservationForm() {
    const dateInput = document.getElementById('date');
    
    if (!dateInput || !dateInput.value) {
        alert('날짜를 선택해주세요.');
        return false;
    }
    
    // 날짜가 일요일인지 확인
    // const selectedDate = new Date(dateInput.value);
    // if (selectedDate.getDay() !== 0) {
    //     alert('일요일에만 예약할 수 있습니다.');
    //     return false;
    // }
    
    // 시간 검증
    return validateTime();
}

/**
 * Date 객체를 HTML date input 형식(YYYY-MM-DD)으로 변환합니다.
 * @param {Date} date - 변환할 Date 객체
 * @returns {string} YYYY-MM-DD 형식의 문자열
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 대시보드 페이지의 기능을 초기화합니다.
 */
function initDashboard() {
    // 예약 취소 버튼에 이벤트 리스너 추가
    const cancelButtons = document.querySelectorAll('.cancel-reservation-btn');
    
    cancelButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('정말 예약을 취소하시겠습니까?')) {
                event.preventDefault();
            }
        });
    });
}

/**
 * 관리자 기능을 초기화합니다.
 */
function initAdminFeatures() {
    // 예약 승인/거절 버튼에 이벤트 리스너 추가
    const approveButtons = document.querySelectorAll('.approve-btn');
    const rejectButtons = document.querySelectorAll('.reject-btn');
    
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!confirm('이 예약을 승인하시겠습니까?')) {
                event.preventDefault();
            }
        });
    });
    
    rejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!confirm('이 예약을 거절하시겠습니까?')) {
                event.preventDefault();
            }
        });
    });
    
    // 차단 시간 등록 폼 검증
    const blockTimeForm = document.querySelector('form[action*="block_time"]');
    
    if (blockTimeForm) {
        blockTimeForm.addEventListener('submit', function(event) {
            const startTime = document.getElementById('block_start_time').value;
            const endTime = document.getElementById('block_end_time').value;
            
            if (startTime >= endTime) {
                alert('시작 시간은 종료 시간보다 이전이어야 합니다.');
                event.preventDefault();
            }
        });
    }
}