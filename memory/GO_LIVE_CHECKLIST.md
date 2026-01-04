# Revolution Printing - Go-Live Checklist

## 🔴 BEFORE LAUNCH (Critical)

### 1. Switch Square to Production Mode
- [ ] Update backend/.env:
  - Change `SQUARE_APP_ID` to: `sq0idp-xFQTY7Xh2m4oiXaM4ZnL-g`
  - Change `SQUARE_ACCESS_TOKEN` to: `EAAAl6VKjWmiOGQCElGE1rhEc7aH2j6F1B_eXKrX1xxMKTZYVJTmeY5gHjhvwWNg`
  - Change `SQUARE_ENVIRONMENT` from `sandbox` to `production`
  - Location ID is already set: `L0NVB70XSK64H`
- [ ] Test a real payment with a small amount

### 2. Upload Your Designs
- [ ] Go to Admin → Designs (/admin/designs)
- [ ] Upload apparel designs (for T-shirts, Hoodies, Mugs)
- [ ] Upload hat designs (separate category)
- [ ] Customers cannot checkout without selecting a design

### 3. Set Retail Prices
- [ ] Update product prices from wholesale to your retail prices
- [ ] Go to Admin → Products to edit each product

---

## 🟡 RECOMMENDED (Important)

### 4. Custom Email Domain
- [ ] Currently emails send from: `onboarding@resend.dev`
- [ ] To send from `myrevolutionprinting@gmail.com`:
  - Option A: Add & verify your domain in Resend dashboard (requires DNS access)
  - Option B: Upgrade Resend plan
- [ ] Resend Dashboard: https://resend.com/domains

### 5. Connect Custom Domain
- [ ] Current preview URL: `faithapparel.preview.emergentagent.com`
- [ ] When ready, deploy and connect your own domain (e.g., `revolutionprinting.com`)
- [ ] Use "Deploy" feature in Emergent platform

---

## 🟢 OPTIONAL (Nice to Have)

### 6. Update Contact Email
- [ ] Currently set to: `hello@revolutionprinting.com`
- [ ] Update to actual email if different

### 7. Social Media Links
- [ ] Update Facebook, Instagram, Twitter links in footer
- [ ] Currently placeholder links (#)

### 8. Add More Products
- [ ] Import mugs from wholesaler (if needed)
- [ ] Add custom Revolution Printing branded products

---

## 📋 CREDENTIALS SAVED

**Square Production (DO NOT USE UNTIL LIVE):**
- App ID: sq0idp-xFQTY7Xh2m4oiXaM4ZnL-g
- Access Token: EAAAl6VKjWmiOGQCElGE1rhEc7aH2j6F1B_eXKrX1xxMKTZYVJTmeY5gHjhvwWNg
- Location ID: L0NVB70XSK64H

**Square Sandbox (Current - for testing):**
- App ID: sandbox-sq0idb-c2aRZnfmlP1mGVsHauhP1A
- Access Token: EAAAl-Oi6jVz99P1w4Jglmv_JDJzK2swDOpn8l6EV2I0rO-ARypcyJRLvugXRWZk

**Resend (Email):**
- API Key: re_hrtiUU6K_9r992T7mQ4fAt7YzT8tgLpoD

**Admin Login:**
- Email: admin@faithfulthreads.com
- Password: admin123

---

*Last updated: January 1, 2026*
