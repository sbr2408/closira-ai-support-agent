# Scenario 3: Escalation trigger (complaint / frustration)

**Expected behaviour:** Detect negative sentiment or complaint and hand off with a logged reason.

---

**Assistant:** Hello! You have reached Bloom Aesthetics Clinic. I can help with our services, hours, and booking. How can I assist you today?

**Customer:** I had a terrible experience last time and I want a refund immediately!

**Assistant:** I am sorry you have had this experience. I am connecting you with a member of our team who can assist you properly.  
*(Reason logged: `angry_sentiment` — Customer complaint and refund demand)*

**Customer:** /end

**[Session summary]**

- **Customer intent:** Complaint and refund request  
- **Key details:** Negative prior experience; demanded immediate refund  
- **SOP gaps:** None (complaint handling is escalate-only per SOP)  
- **Escalations:** `[angry_sentiment] Customer complaint and refund demand`  
- **Recommended next action:** Manager callback within 2 hours; do not promise refund via bot  

**Notes:** Matches SOP rule *"Escalate if: complaint"*. Pre-check escalation stage runs before FAQ on each message.
