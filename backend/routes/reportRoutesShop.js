import express from 'express';
import PDFDocument from 'pdfkit';
import moment from 'moment';
import fs from 'fs';
import Product from '../models/Product.js';
import User from '../models/userModel.js';

const router = express.Router();

// GET /api/reports/catalog-report?userEmail=xxx - Generate the product catalog PDF report.
router.get('/catalog-report', async (req, res) => {
  try {
    // Fetch user details using email instead of ID.
    const userEmail = req.query.userEmail;
    if (!userEmail) {
      return res.status(400).json({ message: 'User email is required to generate the report.' });
    }
    const user = await User.findOne({ email: userEmail });
    if (!user) {
      return res.status(404).json({ message: 'User not found.' });
    }

    // Fetch all products from the database.
    const products = await Product.find();

    // Create a new PDF document.
    const doc = new PDFDocument({ margin: 50, size: 'A4' });

    // Set response headers to display the PDF in the browser.
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'inline; filename="ProductCatalogReport.pdf"');
    doc.pipe(res);

    // ---------------------------
    // HEADER SECTION
    // ---------------------------

    // Place the logo in the top-left.
    const logoPath = './backend/public/AlphaITSolutionsLogo.jpg';
    if (fs.existsSync(logoPath)) {
      doc.image(logoPath, 50, 40, { width: 190 });
    }

    // Company name next to the logo:
    doc
      .font('Helvetica-Bold')
      .fontSize(18)
      .text('Alpha IT Solutions', 120, 45)
      .font('Helvetica')
      .fontSize(10)
      .text('123 Galle Road, Colombo, Sri Lanka', 120, 70)
      .text('Phone: +94 112 345 67', 120, 85);

    // Report generation date/time aligned to the right.
    doc
      .fontSize(10)
      .text(`Report Generated: ${moment().format('YYYY-MM-DD HH:mm')}`, 50, 50, { align: 'right' })
      .moveDown(2);

    // Draw a horizontal line after the header
    doc
      .moveTo(50, 110)
      .lineTo(550, 110)
      .stroke();
    doc.moveDown(2);

    doc.on('pageAdded', () => {
      // Repeat header content on new pages
      if (fs.existsSync(logoPath)) {
        doc.image(logoPath, 50, 40, { width: 60 });
      }
      doc
        .font('Helvetica-Bold')
        .fontSize(18)
        .text('Alpha IT Solutions', 120, 45)
        .font('Helvetica')
        .fontSize(10)
        .text('123 Galle Road, Colombo, Sri Lanka', 120, 70)
        .text('Phone: +94 112 345 67', 120, 85);

      doc
        .fontSize(10)
        .text(`Report Generated: ${moment().format('YYYY-MM-DD HH:mm')}`, 50, 50, { align: 'right' })
        .moveDown(2);

      doc
        .moveTo(50, 110)
        .lineTo(550, 110)
        .stroke();
      doc.moveDown(2);
    });

    // ---------------------------
    // USER INFORMATION SECTION
    // ---------------------------
    doc
      .font('Helvetica-Bold')
      .fontSize(14)
      .text('User Information', { underline: true })
      .moveDown(1);

    doc
      .font('Helvetica')
      .fontSize(10)
      .text(`Name: ${user.name}`)
      .text(`Email: ${user.email}`)
      .text(`Contact Number: ${user.contactNumber}`)
      .text(`Address: ${user.address}`)
      .moveDown(1);

    // Draw a line under user info
    doc
      .moveTo(50, doc.y)
      .lineTo(550, doc.y)
      .stroke();
    doc.moveDown(2);

    // ---------------------------
    // PRODUCT CATALOG SECTION
    // ---------------------------
    doc
      .font('Helvetica-Bold')
      .fontSize(14)
      .text('Product Catalog', { underline: true })
      .moveDown(1);

    products.forEach((prod) => {
      doc
        .font('Helvetica-Bold')
        .fontSize(11)
        .fillColor('black')
        .text(`Product ID: ${prod._id}`, { continued: true })
        .text(` | Category: ${prod.category}`);

      // Price display
      if (prod.discountPrice && prod.discountPrice !== 0) {
        doc
          .font('Helvetica')
          .fontSize(10)
          .fillColor('green')
          .text(`Price: Rs. ${prod.discountPrice.toFixed(2)} `, { continued: true });

        // Strikethrough original price in red
        const originalPrice = `Rs. ${prod.price.toFixed(2)}`;
        const currentX = doc.x;
        const currentY = doc.y - 12;
        doc
          .fillColor('red')
          .text(originalPrice, currentX, currentY, { strike: true });
      } else {
        doc
          .font('Helvetica')
          .fontSize(10)
          .fillColor('black')
          .text(`Price: Rs. ${prod.price.toFixed(2)}`);
      }

      // Other product info
      doc
        .font('Helvetica')
        .fontSize(10)
        .fillColor('black')
        .text(`Availability: ${prod.availability}`)
        .text(`State: ${prod.state}`)
        .text(`Description: ${prod.description}`)
        .moveDown(0.5);

      // Show specs in bullet form if you want
      if (prod.specs && prod.specs.length > 0) {
        doc.font('Helvetica-Bold').text('Specifications:', { underline: false });
        doc.font('Helvetica');
        prod.specs.forEach((spec) => {
          doc.list([`${spec.key}: ${spec.value}`], { bulletRadius: 2, textIndent: 20 });
        });
      }

      doc.moveDown();

      // Draw a separator line between products
      doc
        .moveTo(50, doc.y)
        .lineTo(550, doc.y)
        .stroke();
      doc.moveDown(1);
    });

    // ---------------------------
    // FOOTER SECTION
    // ---------------------------
    const footerY = doc.page.height - 100;
    doc.fontSize(9)
      .text('Please show this PDF when the device is handed over.', 50, footerY, { align: 'center' })
      .text('Alpha IT Solutions', { align: 'center' })
      .text('123 Galle Road, Colombo, Sri Lanka', { align: 'center' })
      .text('Phone: +94 112 345 678 | Email: info@alphaitsolutions.com', { align: 'center' });

    // Finalize the PDF and end the document.
    doc.end();
  } catch (err) {
    console.error('Error generating catalog report:', err);
    res.status(500).json({ message: 'Error generating catalog report' });
  }
});

export default router;
