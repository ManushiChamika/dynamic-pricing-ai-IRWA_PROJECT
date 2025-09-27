import PDFDocument from 'pdfkit';
import fs from 'fs';

export function createInvoicePDF(invoiceData, filePath) {
  const doc = new PDFDocument();

  doc.pipe(fs.createWriteStream(filePath));

  doc.fontSize(25).text('Invoice', { align: 'center' });

  doc.moveDown();
  doc.fontSize(14).text(`Customer: ${invoiceData.customerName}`);
  doc.text(`Date: ${invoiceData.date.toDateString()}`);
  doc.text(`Status: ${invoiceData.status}`);

  doc.moveDown();
  doc.text('Items:', { underline: true });
  invoiceData.items.forEach(item => {
    doc.text(`${item.name} - ${item.quantity} x $${item.price}`);
  });

  doc.moveDown();
  doc.fontSize(16).text(`Total: $${invoiceData.totalAmount}`, { bold: true });

  doc.end();
}
