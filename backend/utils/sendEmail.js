// sendEmail.js
import nodemailer from 'nodemailer';
import orderStatusUpdate from '../emailTemplates/orderStatusUpdate.js'; // optional, for HTML templates
import dotenv from 'dotenv';

dotenv.config();

const transporter = nodemailer.createTransport({
  service: 'Gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD,
  },
});

const sendEmail = async (to, subject, text, options = {}) => {
  try {
    const mailOptions = {
      from: `"Alpha IT Solutions" <${process.env.EMAIL_USER}>`,
      to,
      subject,
      text,
      html: options.useTemplate ? orderStatusUpdate(text) : undefined,
      attachments: options.attachments || [], // 👈 allow attachments if provided
    };

    const info = await transporter.sendMail(mailOptions);
    console.log("Email sent:", info.messageId);
  } catch (error) {
    console.error("Error sending email:", error);
    throw error;
  }
};

export default sendEmail;
