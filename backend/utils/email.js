import nodemailer from 'nodemailer';

let transporter = null;

const getTransporter = () => {
  if (!transporter) {
    transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
      },
    });
  }
  return transporter;
};

export async function sendOTPEmail(to, otp, purpose) {
  const isReset = purpose === 'reset';
  const subject = isReset ? 'Reset your Echobit password' : 'Verify your Echobit email';
  const heading = isReset ? 'Password Reset Code' : 'Email Verification Code';
  const body = isReset
    ? 'You requested to reset your password. Use the code below:'
    : 'Thanks for signing up! Use the code below to verify your email:';

  await getTransporter().sendMail({
    from: process.env.EMAIL_FROM || `Echobit <${process.env.EMAIL_USER}>`,
    to,
    subject,
    html: `
      <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #f9fafb; border-radius: 12px;">
        <h2 style="color: #059669; margin: 0 0 8px;">${heading}</h2>
        <p style="color: #6b7280; margin: 0 0 24px;">${body}</p>
        <div style="background: white; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #e5e7eb;">
          <span style="font-size: 40px; font-weight: 800; letter-spacing: 12px; color: #111827;">${otp}</span>
        </div>
        <p style="color: #9ca3af; font-size: 13px; margin: 20px 0 0; text-align: center;">
          This code expires in <strong>10 minutes</strong>. Do not share it with anyone.
        </p>
      </div>
    `,
  });
}
