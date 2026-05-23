# Scenario 4: Lead qualification

**Expected behaviour:** Ask 2–3 structured questions, store answers, produce a qualification summary.

---

**Assistant:** Hello! You have reached Bloom Aesthetics Clinic. I can help with our services, hours, and booking. How can I assist you today?

**Customer:** /qualify

**Assistant:** To help us understand your needs better: What type of business are you enquiring on behalf of (e.g. sole trader, salon, clinic)?

**Customer:** We run a small salon with 4 staff.

**Assistant:** To help us understand your needs better: Roughly how many team members handle customer enquiries?

**Customer:** Four people handle enquiries.

**Assistant:** To help us understand your needs better: Which tools do you currently use for WhatsApp, email, or phone support?

**Customer:** We use WhatsApp Business and Gmail.

**Assistant:** Thank you — I have noted your details.

**Lead qualification summary:**

| Question | Answer |
|----------|--------|
| Business type | Small salon, 4 staff |
| Enquiry handlers | Four people |
| Current tools | WhatsApp Business and Gmail |

**Customer:** /end

**[Session summary]**

- **Customer intent:** B2B lead qualification  
- **Qualification summary:** Salon; 4 enquiry handlers; WhatsApp Business + Gmail  
- **Recommended next action:** Schedule product demo with decision-maker  

**Notes:** Questions sourced from `sop/bloom_aesthetics.json` → `qualification_questions`. Answers stored in `ConversationState.qualification_answers`.
