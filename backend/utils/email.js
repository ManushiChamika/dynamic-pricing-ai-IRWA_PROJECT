// utils/email.js
import nodemailer from "nodemailer";

const transporter = nodemailer.createTransport({
  service: process.env.SMTP_SERVICE,    // e.g. "gmail"
  auth: {
    user: process.env.EMAIL_USER,       // your admin Gmail address
    pass: process.env.EMAIL_PASSWORD,   // your SMTP/app password
  }
});

/**
 * Send a low-stock alert email to the admin.
 */
export async function sendLowStockAlert(product) {
  const toEmail = "mckettipearachchi@gmail.com"; // or process.env.ADMIN_EMAIL

  const mailOptions = {
    from: `"Inventory Alert" <${process.env.EMAIL_USER}>`,
    to:   toEmail,
    subject: `Low Stock: ${product.description}`,
    text: `
Product "${product.description}" (ID: ${product._id}) is low in stock.
Current displayedStock: ${product.displayedStock}
Threshold: ${product.threshold}

Please restock as soon as possible.
    `.trim()
  };

  // send and log result for visibility
  const info = await transporter.sendMail(mailOptions);
  console.log("Low-stock alert sent:", info.messageId, "to", toEmail);
  return info;
}
