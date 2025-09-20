// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Toggle between user and admin login forms
    const userLoginBtn = document.getElementById('user-login-btn');
    const adminLoginBtn = document.getElementById('admin-login-btn');
    const userLoginForm = document.getElementById('user-login-form');
    const adminLoginForm = document.getElementById('admin-login-form');
    
    if (userLoginBtn && adminLoginBtn) {
        userLoginBtn.addEventListener('click', function() {
            userLoginForm.classList.remove('d-none');
            adminLoginForm.classList.add('d-none');
            userLoginBtn.classList.add('active', 'btn-success');
            userLoginBtn.classList.remove('btn-outline-success');
            adminLoginBtn.classList.remove('active', 'btn-warning');
            adminLoginBtn.classList.add('btn-outline-warning');
        });
        
        adminLoginBtn.addEventListener('click', function() {
            adminLoginForm.classList.remove('d-none');
            userLoginForm.classList.add('d-none');
            adminLoginBtn.classList.add('active', 'btn-warning');
            adminLoginBtn.classList.remove('btn-outline-warning');
            userLoginBtn.classList.remove('active', 'btn-success');
            userLoginBtn.classList.add('btn-outline-success');
        });
    }
    
    // Handle slot booking
    const bookSlotButtons = document.querySelectorAll('.book-slot');
    bookSlotButtons.forEach(button => {
        button.addEventListener('click', function() {
            const slotId = this.dataset.slotId;
            bookSlot(slotId);
        });
    });
    
    // Function to book a slot
    function bookSlot(slotId) {
        fetch('/book/slot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `slot_id=${slotId}`
        })
        .then(response => response.json())
        .then(data => {
            const bookingResult = document.getElementById('booking-result');
            const bookingDetails = document.getElementById('booking-details');
            
            if (data.success) {
                bookingDetails.innerHTML = `
                    <div class="alert alert-success">
                        <h4>Booking Successful!</h4>
                        <p>Your booking ID: ${data.booking_id}</p>
                        <div class="qr-code">
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${data.qr_code}" alt="QR Code">
                        </div>
                        <p class="mt-2">Please show this QR code at the temple entrance.</p>
                    </div>
                `;
            } else {
                bookingDetails.innerHTML = `
                    <div class="alert alert-danger">
                        <h4>Booking Failed</h4>
                        <p>${data.message}</p>
                    </div>
                `;
            }
            bookingResult.classList.remove('d-none');
        })
        .catch(error => {
            console.error('Error:', error);
            const bookingResult = document.getElementById('booking-result');
            const bookingDetails = document.getElementById('booking-details');
            bookingDetails.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error</h4>
                    <p>Something went wrong. Please try again.</p>
                </div>
            `;
            bookingResult.classList.remove('d-none');
        });
    }
});
