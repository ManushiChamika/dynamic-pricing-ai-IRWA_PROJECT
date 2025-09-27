export const resetOTPTemplate = (name, newOTP) => {
    return `
        <html>
        <head>
            <style>
                .container {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    max-width: 600px;
                    margin: auto;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                .header {
                    background: #4CAF50;
                    color: white;
                    text-align: center;
                    padding: 10px;
                    font-size: 20px;
                    font-weight: bold;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                }
                .content {
                    padding: 20px;
                    text-align: center;
                    font-size: 16px;
                }
                .otp {
                    font-size: 24px;
                    font-weight: bold;
                    color: #4CAF50;
                }
                .footer {
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    padding: 10px;
                    border-top: 1px solid #ddd;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">Resed OTP Verification</div>
                <div class="content">
                    <p>Hello ${name},</p>
                    <p>Your One-Time Password (OTP) for verification is:</p>
                    <p class="otp">${newOTP}</p>
                    <p>Please use this OTP to complete your registration.</p>
                </div>
                <div class="footer">If you didn't request this, please ignore this email.</div>
            </div>
        </body>
        </html>
    `;
}