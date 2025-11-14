# Test Account Credentials

**⚠️ IMPORTANT: Keep this file secure and do not commit to public repositories**

## Production/Staging Test Accounts

### Demo Account (REGULAR)
- **Email:** `gerardoh@gmail.com`
- **Password:** `Test123456!`
- **Account ID:** `912014c3-6deb-4b40-a28d-489ef3923a3a`
- **Account Name:** Demo Account
- **Account Type:** `REGULAR`
- **Plan:** `free` (can be upgraded via Stripe)
- **User ID:** `abdcef61-20f2-46b9-8b24-8c4ce4462ee0`
- **Role:** `ADMIN`

**Use for testing:**
- Login flows
- Plan upgrades (Stripe)
- Schedule creation
- Report generation
- Multi-account features (when additional accounts added)

---

## Database Connection

### Render PostgreSQL (mr-staging-db)
- **Dashboard:** https://dashboard.render.com/d/dpg-d474qiqli9vc738g17e0-a
- **Connection String:** Available in Render Dashboard → Connect button
- **Database:** `mr_staging_db`
- **User:** `mr_staging_db_user`
- **Password:** See Render Dashboard
- **Host:** `dpg-d474qiqli9vc738g17e0-a.oregon-postgres.render.com`
- **Port:** `5432`

---

## Application URLs

### Frontend (Vercel)
- **Production:** https://reportscompany-web.vercel.app
- **Login:** https://reportscompany-web.vercel.app/login
- **Dashboard:** https://reportscompany-web.vercel.app/app

### Backend (Render)
- **API Base:** https://reportscompany.onrender.com
- **Health Check:** https://reportscompany.onrender.com/health
- **Docs:** https://reportscompany.onrender.com/docs

---

## Stripe Test Credentials

### Test Mode Keys (Already Configured on Render)
- **Secret Key:** `sk_test_51SNzPk...` (See Render environment variables)
- **Webhook Secret:** `whsec_mIar...` (See Render environment variables)
- **Pro Plan Price ID:** `price_1STMtBBKYbtiKxfswkmFEPeR`
- **Team Plan Price ID:** `price_1STMtfBKYbtiKxfsqQ4r29Cw`

### Test Card Numbers
- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- **Requires Auth:** `4000 0027 6000 3184`
- **Expiry:** Any future date (e.g., `12/34`)
- **CVC:** Any 3 digits (e.g., `123`)
- **ZIP:** Any 5 digits (e.g., `12345`)

---

## Password Reset Script

If you need to reset the password again, use:

```bash
python reset_password.py
```

Or manually via SQL:

```sql
UPDATE users 
SET password_hash = '$2b$12$6.xT9JvdYXl6f8HRoYyhq.7nUhIqcg5DRNeQ6WrWOt3p271KZN4d.',
    email_verified = true
WHERE email = 'gerardoh@gmail.com';
```

---

## Notes

- All passwords use bcrypt hashing with salt
- Test account created: November 13, 2025
- Password last updated: November 14, 2025
- Database is PostgreSQL 17 on Render
- All services deployed to Oregon region

---

**Last Updated:** November 14, 2025  
**Status:** ✅ Active and tested

