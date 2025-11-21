# People System - Quick Start Guide

## 🎯 Why You're Seeing "Nothing"

The People system is working correctly! You're just logged in as an affiliate account that **doesn't have any contacts or groups yet**.

Our test data was created for the "Demo Title Company" account (`6588ca4a-9509-4118-9359-d1cbf72dcd52`).

---

## ✅ Quick Fix: Add Your First Contact

### Option 1: Use the UI (Recommended)

1. On the `/app/people` page, click **"Add Contact"**
2. Fill in:
   - **Name**: John Doe
   - **Email**: john@example.com  
   - **Type**: Client
   - **Notes**: Test contact
3. Click **"Add Contact"**
4. ✅ You should now see 1 contact!

### Option 2: Import CSV

1. Create a file `test-contacts.csv`:
```csv
name,email,type,group
Alice Johnson,alice@example.com,client,VIP Clients
Bob Smith,bob@example.com,client,VIP Clients
Charlie Brown,charlie@example.com,agent,Partners
```

2. On `/app/people`, click **"Import CSV"**
3. Upload the file
4. ✅ You should see 3 contacts and 2 groups!

---

## 🧪 Testing the Features

### Test Contacts
1. **Add Contact**: Click "Add Contact" → Fill form → Save
2. **Edit Contact**: Click pencil icon on any contact → Change name → Save
3. **Delete Contact**: Click trash icon → Confirm

### Test Groups
1. **Switch to Groups tab**: Click "Groups" tab at the top
2. **Create Group**: Click "New Group" → Name: "VIP Clients" → Save
3. **Add to Group**: Go back to "People" tab → Click on a person → "Add to Group" → Select "VIP Clients"
4. **View Group**: Go to "Groups" tab → Click on "VIP Clients" → See members

### Test CSV Import
1. **Create CSV** with format: `name,email,type,group`
2. **Click "Import CSV"** button
3. **Upload** and see summary

---

## 🔍 Debugging: Check Your Account

If you want to verify which account you're logged in as:

1. Open browser DevTools (F12)
2. Go to **Console**
3. Type: `fetch('/api/proxy/v1/me').then(r => r.json()).then(console.log)`
4. Press Enter
5. Look for `account_type` and `id`

**Example output:**
```json
{
  "id": "abc-123-...",
  "email": "your@email.com",
  "account_id": "def-456-...",
  "account_type": "INDUSTRY_AFFILIATE",
  ...
}
```

---

## 📊 Expected UI

Once you have data, you should see:

### **Header**
```
People
Manage your sponsored agents and client contacts

[Import CSV] [Add Contact]
```

### **Stats Cards** (for affiliates)
```
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Sponsored Agents    │ │ Contacts        │ │ Total People    │
│         2           │ │       3         │ │       5         │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
```

### **People Tab** (table view)
| Name | Email | Type | Reports | Last Activity | Actions |
|------|-------|------|---------|---------------|---------|
| Alice Johnson | alice@... | Client | — | — | ✏️ 🗑️ ⋯ |
| Bob Smith | bob@... | Client | — | — | ✏️ 🗑️ ⋯ |
| Agent Name | — | Agent (Sponsored) | 5 | 2 days ago | ⋯ |

### **Groups Tab** (table view)
| Group Name | Description | Members | Created | Actions |
|------------|-------------|---------|---------|---------|
| VIP Clients | High-value... | 2 | Nov 21 | 👁️ 🗑️ |

---

## 🐛 Still Seeing Nothing?

### Check 1: Network Errors
1. Open DevTools → **Network** tab
2. Refresh page
3. Look for `/api/proxy/v1/contacts` request
4. Check response:
   - ✅ Status 200: API is working
   - ❌ Status 401: Auth issue
   - ❌ Status 500: Server error

### Check 2: Console Errors
1. Open DevTools → **Console** tab
2. Look for red error messages
3. Common issues:
   - `Failed to load people data` → API error
   - `Unauthorized` → Cookie/session expired
   - `Network error` → API unreachable

### Check 3: Empty Response
If API returns `{"contacts": []}` (empty array):
- This is **CORRECT** - you just don't have data yet
- Solution: Add a contact using the UI!

---

## 🎉 Success Criteria

You'll know it's working when:
- ✅ "Add Contact" button is visible
- ✅ "Import CSV" button is visible  
- ✅ "People" and "Groups" tabs exist
- ✅ After adding a contact, it appears in the table
- ✅ Stats cards update (for affiliates)
- ✅ You can click "Add to Group" on any person

---

## 🔧 For Developers

### Test Data Script
To populate test data for ANY affiliate account:

```bash
# Get your account ID first
curl -H "Cookie: mr_token=YOUR_TOKEN" \
  https://reportscompany.onrender.com/v1/me

# Then run our test script with your account ID
DATABASE_URL="..." \
TEST_ACCOUNT_ID="your-account-id-here" \
python scripts/test_people_system.py
```

### API Endpoints to Test

```bash
# List contacts (should return your data)
curl -H "Cookie: mr_token=YOUR_TOKEN" \
  https://reportscompany.onrender.com/v1/contacts

# List groups
curl -H "Cookie: mr_token=YOUR_TOKEN" \
  https://reportscompany.onrender.com/v1/contact-groups

# Get affiliate overview (for sponsored agents)
curl -H "Cookie: mr_token=YOUR_TOKEN" \
  https://reportscompany.onrender.com/v1/affiliate/overview
```

---

## 📝 Summary

**Not a bug!** The system is working perfectly. You just need to add data to your account.

**Fastest way**:
1. Go to `/app/people`
2. Click "Add Contact"
3. Fill in any name/email
4. Click "Add Contact"
5. ✅ See your first contact!

**Questions?** Check the console for errors or create an issue with:
- Your account ID (from `/v1/me`)
- Network tab screenshot
- Console errors (if any)

---

**Last Updated**: November 21, 2024  
**Status**: ✅ All features working, waiting for user data

