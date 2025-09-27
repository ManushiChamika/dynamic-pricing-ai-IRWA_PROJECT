export const inquiryTemplate = (fullName, inquiryType, productName, additionalDetails) => {
    return `
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }
                .container {
                    max-width: 600px;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                h2 {
                    color: #333;
                }
                p {
                    font-size: 16px;
                    color: #555;
                }
                .footer {
                    margin-top: 20px;
                    font-size: 14px;
                    color: #888;
                    text-align: center;
                }
                .highlight {
                    font-weight: bold;
                    color: #007BFF;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Inquiry Submitted Successfully</h2>
                <p>Dear <span class="highlight">${fullName}</span>,</p>
                <p>Thank you for reaching out to us. Your inquiry has been received and our team will review it shortly.</p>
                
                <h3>Inquiry Details:</h3>
                <p><strong>Type:</strong> ${inquiryType}</p>
                ${productName ? `<p><strong>Product:</strong> ${productName}</p>` : ""}
                <p><strong>Details:</strong> ${additionalDetails}</p>

                <p>If your inquiry requires urgent attention, feel free to contact our support team.</p>

                <div class="footer">
                    <p>Best regards,</p>
                    <p><strong>Alpha IT Solutions</strong></p>
                    <p>Email: support@alphaITSolutions.com | Phone: 077 625 2822</p>
                </div>
            </div>
        </body>
        </html>
    `;
};
