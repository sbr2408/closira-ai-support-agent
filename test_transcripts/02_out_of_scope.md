# Scenario 2: Out-of-scope question (parking)

**Expected behaviour:** Acknowledge the SOP gap and escalate — do not guess.

---

**Assistant:** Hello! You have reached Bloom Aesthetics Clinic. I can help with our services, hours, and booking. How can I assist you today?

**Customer:** Do you have free parking on site?

**Assistant:** I do not have parking information in our records. I am connecting you with a member of our team who can help further.  
*(Reason logged: `out_of_scope` — Parking not in SOP)*

**Customer:** /end

**[Session summary]**

- **Customer intent:** Facility question (parking) — out of SOP scope  
- **Key details:** Asked about on-site parking; escalated to human  
- **SOP gaps:** Parking availability  
- **Escalations:** `[out_of_scope] Parking not in SOP`  
- **Recommended next action:** Human agent to confirm parking options and callback  

**Notes:** `sop_gap=true` and `unanswered_sop_count` incremented. Escalation written to `logs/escalations.jsonl`.
