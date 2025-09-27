export const forgotPasswordTemplate = (name) => {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {
          font-family: Arial, sans-serif;
          background-color: #f4f4f4;
          margin: 0;
          padding: 0;
        }
        .container {
          max-width: 600px;
          margin: 20px auto;
          background: #ffffff;
          padding: 20px;
          border-radius: 10px;
          box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        }
        h2 {
          color: #333;
          text-align: center;
        }
        p {
          font-size: 16px;
          color: #555;
          text-align: center;
        }
        .button {
          display: block;
          width: 200px;
          margin: 20px auto;
          padding: 10px;
          text-align: center;
          background-color: #007BFF;
          color: white;
          text-decoration: none;
          border-radius: 5px;
          font-weight: bold;
        }
        .footer {
          text-align: center;
          font-size: 12px;
          color: #777;
          margin-top: 20px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Password Reset Successful</h2>
        <p>Hi <strong>${name}</strong>,</p>
        <p>Your password has been successfully reset.</p>
        <p>If you did not request this change, please contact support immediately.</p>
        <a href="http://localhost:3000/login" class="button">Login Now</a>
        <p class="footer">If you have any questions, contact us at <a href="mailto:support@yourapp.com">support@yourapp.com</a></p>
      </div>
    </body>
    </html>
  `;
};

