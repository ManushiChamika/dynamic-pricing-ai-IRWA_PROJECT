import nodemailer from 'nodemailer';

// Create a reusable transporter object using SMTP transport
const transporter = nodemailer.createTransport({
    service: 'gmail', // You can use Gmail or any other service
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASSWORD,
    }
});

// Function to send email alert
const suspiciousTransaction = async (transaction) => {
    const mailOptions = {
        from: `"Alpha IT Solutions" <${process.env.EMAIL_USER}>`, // Sender address
        to: 'thushaliniammu12@gmail.com', // Receiver address (Admin email)
        subject: 'Suspicious Transaction Alert', // Email subject
        text: `A suspicious transaction has been detected:

Transaction Details:
- Amount: ${transaction.amount}
- Type: ${transaction.type}
- Category: ${transaction.category}
- Date: ${transaction.date}
- Description: ${transaction.description}
- Suspicious: ${transaction.isSuspicious}

Please review the transaction for further action.` // Email body
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log("Suspicious transaction email sent to admin.");
    } catch (error) {
        console.error("Error sending email:", error);
    }
};

export default suspiciousTransaction;