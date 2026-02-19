# Email Verification Setup

PharmaGuard supports email verification for new user registrations. The system works in two modes:

## Development Mode (Default)
When SMTP is **not configured**, the system operates in development mode:
- Verification codes are displayed directly on the registration page
- No actual emails are sent
- Users can immediately see and use the verification code

## Production Mode (Email Enabled)
When SMTP is **configured**, the system sends verification emails:
- Verification codes are sent to the user's email address
- Codes are NOT displayed on the page
- Professional HTML email templates are used

## Configuration

### 1. Create a `.env` file
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Configure SMTP Settings
Edit `.env` and add your SMTP credentials:

```env
# Gmail Example (requires App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@pharmaguard.com
SMTP_FROM_NAME=PharmaGuard
```

### 3. SMTP Provider Examples

#### Gmail
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use these settings:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

#### SendGrid
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### AWS SES
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

#### Outlook/Office365
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

## Testing

### Development Mode (Default)
Simply start the backend without SMTP configuration. Registration will show the verification code on screen.

### Production Mode
1. Configure SMTP settings in `.env`
2. Restart the backend
3. Register a new user
4. Check the registered email inbox for the verification code
5. Use the code to verify the account

## Troubleshooting

### Emails not sending
- Check SMTP credentials are correct
- Verify the SMTP port (587 for TLS, 465 for SSL)
- Check firewall/network settings allow outbound SMTP
- Review backend logs for error messages

### Gmail "Less secure apps" error
- Use an App Password instead of your regular password
- Enable 2FA first, then generate App Password

### Development mode when it should be production
- Ensure all SMTP environment variables are set
- Restart the backend after changing `.env`
- Check backend logs for "SMTP_ENABLED" status

## Security Notes

- **Never commit `.env` to version control**
- Use App Passwords instead of account passwords when possible
- Rotate SMTP credentials regularly
- Consider using dedicated email service (SendGrid, AWS SES) for production
- Monitor email sending rates to avoid spam flagging
