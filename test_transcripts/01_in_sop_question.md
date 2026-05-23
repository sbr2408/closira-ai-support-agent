# Scenario 1: In-SOP question (Botox pricing)

**Expected behaviour:** Answer accurately from SOP only; no invented prices or policies.

---

**Assistant:** Hello! You have reached Bloom Aesthetics Clinic. I can help with our services, hours, and booking. How can I assist you today?

**Customer:** What are your Botox prices?

**Assistant:** Botox treatments start from £200. The exact price depends on the treatment area and is confirmed at consultation.

**Customer:** /end

**[Session summary]**

- **Customer intent:** Pricing enquiry for Botox treatments  
- **Key details:** Botox from £200 (SOP); may need consultation for exact quote  
- **SOP gaps:** None  
- **Escalations:** None  
- **Recommended next action:** Offer free consultation booking via WhatsApp  

**Notes:** Response cites only SOP fields (`services[].name`, `starting_price_gbp`). No medical advice or negotiated pricing.
