export const welcomeTemplate = (name) => {
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
                    background: #007BFF;
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
                <div class="header">Welcome to Our Platform!</div>
                <div class="content">
                    <p>Hello ${name},</p>
                    <p>Thank you for joining us! We are excited to have you on board.</p>
                    <p>Explore our features and get started!</p>
                </div>
                <div class="footer">If you have any questions, feel free to contact us.</div>
            </div>
        </body>
        </html>
    `;
};
