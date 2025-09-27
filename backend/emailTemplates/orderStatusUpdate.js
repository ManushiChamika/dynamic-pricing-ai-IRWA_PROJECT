const orderStatusUpdate = (text) => `
  <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
    <h2 style="color: #4CAF50; text-align: center;">Alpha IT Solutions</h2>
    <p style="font-size: 16px; color: #333;">Dear Customer,</p>
    <p style="font-size: 16px; color: #333;">
      ${text}
    </p>
    <p style="font-size: 16px; color: #333;">Thank you for choosing Alpha IT Solutions.<br\> We're always here to serve you!</p>
    <hr style="border: none; border-top: 1px solid #eee;">
    <p style="font-size: 12px; color: #999; text-align: center;">This is an automated message. Please do not reply to this email.</p>
  </div>
`;

export default orderStatusUpdate;
