# LLM & Prompt-Focused Evaluation Results

Secondary eval — tests refusal behavior, paraphrase robustness, and structural correctness (not just routing).

**Routing accuracy:** 8/8 (100%)  
**Behavior checks passed:** 6/8 (75%)

| # | Test | Expected Intent | Actual | Routing | Behavior Check | Latency (s) |
|---|---|---|---|---|---|---|
| 1 | Refusal on missing info | lookup | lookup | ✅ | ✅ | 73.68 |
| 2 | Paraphrase robustness — draft_new | draft_new | draft_new | ✅ | ✅ | 155.86 |
| 3 | Paraphrase robustness — draft_adapt | draft_adapt | draft_adapt | ✅ | ✅ | 37.74 |
| 4 | Paraphrase robustness — compare | compare | compare | ✅ | ❌ | 58.64 |
| 5 | Typo / casual phrasing robustness | lookup | lookup | ✅ | ✅ | 21.75 |
| 6 | Draft structural correctness | draft_new | draft_new | ✅ | ✅ | 88.72 |
| 7 | Comparator structural correctness (2nd case) | compare | compare | ✅ | ❌ | 57.99 |
| 8 | Grounded citation check | lookup | lookup | ✅ | ✅ | 16.48 |

## Details

### 1. Refusal on missing info
*Query: What blockchain risks does Bank of America disclose?*  
*Check: Answer should say the info isn't in the context, not invent an answer.*

The provided context does not contain any relevant filing text from Bank of America or any other company, so I cannot provide information on the blockchain risks that Bank of America discloses.

### 2. Paraphrase robustness — draft_new
*Query: I want to create fresh AI disclosure text for a healthcare startup*  
*Check: Should use the placeholder, confirming it drafted from scratch correctly.*

**SEC Disclosure Section for [Your Company]**

**Forward-Looking Statements**

This section contains forward-looking statements within the meaning of Section 27A of the Securities Act of 1933, as amended, and Section 21E of the Securities Exchange Act of 1934, as amended. These statements are based on management’s current expectations and beliefs and are subject to risks and uncertainties that could cause actual results to differ materially from those expressed or implied by these forward-looking statements. Readers are cautioned not to place undue reliance on these forward-looking statements, which speak only as of the date hereof. [Your Company] does not undertake any obligation to update or revise any forward-looking statements to reflect events or circumstances after the date hereof.

**Business Overview and Risk Factors**

[Your Company] is a healthcare startup focused on developing artificial intelligence (AI) solutions to enhance patient care and improve healthcare outcomes. The Company’s primary business is the development, testing, and commercialization of AI-driven diagnostic tools and predictive analytics for various medical conditions. The Company’s operations are subject to significant risks and uncertainties, including those described below.

**Risks Related to Our Business and Operations**

1. **Dependence on AI Technology**: The success of our business is highly dependent on the development and commercialization of our AI technology. The effectiveness and reliability of our AI tools are critical to our success. Any failure of our AI technology to perform as expected could significantly harm our business and reputation.

2. **Regulatory Compliance**: Our business is subject to extensive regulation by federal, state, and local authorities. Compliance with these regulations is complex and costly. Any failure to comply with applicable regulations could result in significant fines, penalties, or other sanctions, which could have a material adverse effect on our business.

3. **Intellectual Property Risks**: The protection of our intellectual property is critical to our business. We rely on a combination of patents, trademarks, copyrights, and trade secrets to protect our technology. However, the legal protection of intellectual property is complex and uncertain. Infringement claims, if successful, could result in significant costs and could harm our business.

4. **Market Risks**: The healthcare industry is highly competitive and subject to rapid technological change. Our success depends on our ability to develop and commercialize innovative AI solutions that meet the needs of healthcare providers and patients. Failure to do so could result in loss of market share and revenue.

5. **Financial Risks**: Our business is capital-intensive, and we may require additional financing to fund our operations. If we are unable to secure adequate financing, our ability to continue operations could be materially impaired.

6. **Dependence on Key Personnel**: Our success depends on the skills and experience of our key personnel. The loss of any of these individuals could have a material adverse effect on our business.

7. **Cybersecurity Risks**: As a healthcare provider, we are subject to cybersecurity risks. Any breach of our systems could result in the loss of sensitive patient data, which could lead to significant legal and financial liabilities.

8. **Healthcare Reimbursement and Payment Risks**: Our business is dependent on the availability of reimbursement from third-party payers, including government and private insurance plans. Changes in healthcare reimbursement policies or payment rates could have a material adverse effect on our business.

9. **Supply Chain Risks**: Our business may be impacted by disruptions in the supply chain, including shortages of critical components or materials. Such disruptions could delay our product development and commercialization efforts.

10. **Environmental, Social, and Governance (ESG) Risks**: As a responsible corporate citizen, we are committed to ESG principles. However, failure to meet ESG standards could result in reputational damage and legal liabilities.

**Conclusion**

The risks and uncertainties described above are not the only risks facing [Your Company]. Additional risks and uncertainties not presently known to us or that we currently deem immaterial may also impair our business operations. Readers are encouraged to consider these risks and uncertainties in evaluating our business and prospects.

**Legal Disclaimer**

This disclosure section is intended to provide information to investors and does not constitute a solicitation for investment. The information provided herein is for general informational purposes only and does not constitute legal, financial, or other professional advice. Readers should consult with their own advisors before making any investment decisions.

[Your Company] reserves the right to amend or update this disclosure section at any time without notice.

### 3. Paraphrase robustness — draft_adapt
*Query: Use NOCERA INC's filing as a base and rewrite it for us*  
*Check: Should have actually retrieved NOCERA's text, not fallen back to a blank draft.*

LOI.

The Letter of Intent (LOI) contains certain binding provisions, but does not obligate either party to consummate the Proposed Transaction unless and until the parties enter into definitive documentation. There can be no assurance that the parties will enter into a definitive agreement or that the Proposed Transaction will be consummated on the terms described herein or at all.

This Current Report on Form 8-K contains forward-looking statements within the meaning of Section 27A of the Securities Act of 1933, as amended, and Section 21E of the Securities Exchange Act of 1934, as amended. Such statements are subject to risks and uncertainties that could cause actual results to differ materially, including the ability of the parties to negotiate definitive documentation, the results of due diligence, regulatory approvals, market conditions, and other risks described in [Your Company]'s filings with the Securities and Exchange Commission. [Your Company] undertakes no obligation to update forward-looking statements.

### 4. Paraphrase robustness — compare
*Query: How does Eightco Holdings Inc's AI disclosure differ from Cuentas Inc's?*  
*Check: All 3 fixed dimensions should produce a finding — tests the Send fan-out actually completed.*

Gap analysis: Eightco Holdings Inc vs. Cuentas Inc

**AI-related risk factors:**
Based on the provided disclosures, Eightco Holdings Inc does not disclose any specific information regarding AI-related risk factors or its involvement with OpenAI beyond mentioning the indirect economic interests. In contrast, Cuentas Inc does not provide any information related to AI or AI-related risk factors in the given excerpt. Therefore, there is no specific information that Cuentas Inc discloses on this dimension that Eightco Holdings Inc does not, as neither company provides relevant details in the given excerpts.

**forward-looking statements about AI:**
Finding: Cuentas Inc's disclosure on this dimension is more specific and detailed compared to Eightco Holdings Inc's. Cuentas Inc mentions the appointment of Ofek Haim Suchard as the Chief Artificial Intelligence Officer, providing background information on his qualifications and the transition from his previous role. Eightco Holdings Inc, on the other hand, does not provide any information about AI-related appointments or the company's AI strategy, making the disclosure less informative on this specific dimension.

**financial metrics or figures related to AI investments:**
Finding: Eightco Holdings Inc's disclosure does not provide any specific financial metrics or figures related to AI investments, whereas Cuentas Inc discloses the appointment of a new Chief Artificial Intelligence Officer, Ofek Haim Suchard, who will lead the company's AI initiatives. This information from Cuentas Inc offers insight into the company's strategic direction in AI, but lacks the quantitative financial data that Eightco Holdings Inc omits.


### 5. Typo / casual phrasing robustness
*Query: wut did hoth therapeutics say in their 8-K filing*  
*Check: Should still classify and answer correctly despite typos/casual tone.*

Based on the provided context, Hoth Therapeutics Inc. filed an 8-K report on an unspecified date, which included a press release dated May 19, 2026. The press release (Exhibit 99.1) was filed as part of this Current Report on Form 8-K but the specific content of the press release is not provided in the given context. Therefore, I cannot state what Hoth Therapeutics said in their 8-K filing without more information.

### 6. Draft structural correctness
*Query: Write a new AI cybersecurity risk disclosure*  
*Check: Placeholder convention should be followed consistently across draft_new calls.*

**SECURITY RISKS AND UNCERTAINTIES**

[Your Company] is subject to various cybersecurity risks and uncertainties, including risks related to the use of artificial intelligence (AI) in its operations. The following disclosure addresses the specific risks associated with AI cybersecurity.

**Risks Related to AI Cybersecurity**

1. **AI-Driven Threats:** The increasing sophistication of AI-driven cyber threats poses a significant risk to [Your Company]'s cybersecurity posture. While AI can enhance our detection and response capabilities, it also increases the complexity of our systems, potentially creating new vulnerabilities. [Your Company] is actively monitoring and addressing these threats through continuous updates to its cybersecurity protocols and the integration of AI-driven security solutions.

2. **Data Privacy and Security:** The use of AI in cybersecurity involves the collection, storage, and analysis of large volumes of sensitive data. [Your Company] is committed to protecting this data through robust data protection measures, including encryption, access controls, and regular security audits. However, there is a risk that these measures may not be sufficient to prevent data breaches, which could result in significant financial, legal, and reputational harm to [Your Company].

3. **Cybersecurity Talent Shortage:** The shortage of skilled cybersecurity professionals, particularly those with expertise in AI, poses a challenge for [Your Company]. While [Your Company] is investing in training and development programs to address this issue, there is no guarantee that these efforts will be successful in mitigating the risk of cybersecurity breaches.

4. **Regulatory Compliance:** [Your Company] is subject to various cybersecurity regulations and standards, including those related to the use of AI. Compliance with these regulations is critical to maintaining [Your Company]'s operations and avoiding potential legal and financial penalties. However, changes in regulations or the interpretation of existing regulations could impact [Your Company]'s ability to effectively manage cybersecurity risks.

5. **Third-Party Risks:** [Your Company] relies on third-party vendors and service providers for various aspects of its operations, including cybersecurity. The failure of these third parties to maintain adequate cybersecurity measures could expose [Your Company] to significant risks. [Your Company] is working to ensure that its third-party vendors meet or exceed its cybersecurity standards, but there is no assurance that these efforts will be successful.

**Forward-Looking Statements**

The preceding discussion of cybersecurity risks and uncertainties includes forward-looking statements that involve risks and uncertainties. These statements are based on current expectations and assumptions that are subject to risks and uncertainties. Actual results could differ materially from those anticipated in these forward-looking statements. [Your Company] does not undertake any obligation to update these forward-looking statements to reflect subsequent events or circumstances.

**Conclusion**

[Your Company] is committed to maintaining a robust cybersecurity posture, including the use of AI to enhance its security capabilities. However, the risks associated with AI cybersecurity are significant and cannot be fully eliminated. [Your Company] will continue to monitor and address these risks through ongoing investment in cybersecurity measures and the integration of AI-driven solutions.

---

This disclosure section follows SEC conventions, providing clear, factual, and hedged language for forward-looking statements, and addresses the specific risks related to AI cybersecurity.

### 7. Comparator structural correctness (2nd case)
*Query: Compare Hoth Therapeutics AI disclosure against NOCERA INC and identify gaps*  
*Check: Confirms Send fan-out reliability across a different company pair.*

Gap analysis: Hoth Therapeutics Inc vs. NOCERA INC

**AI-related risk factors:**
NOCERA INC's disclosure on AI-related risk factors is more comprehensive as it explicitly mentions the risks associated with the proposed transaction, including the ability to negotiate definitive documentation, due diligence outcomes, regulatory approvals, market conditions, and other risks. Hoth Therapeutics Inc's disclosure, on the other hand, focuses more on the restructuring of its business and name change, without detailing the specific risks related to AI infrastructure or other technologies. Therefore, Hoth Therapeutics Inc's disclosure is weaker in terms of identifying and addressing potential risks associated with AI-related initiatives.

**forward-looking statements about AI:**
NOCERA INC's disclosure includes a more explicit acknowledgment of the risks associated with forward-looking statements, specifically mentioning the risks related to negotiating definitive documentation, due diligence, regulatory approvals, market conditions, and other risks. Hoth Therapeutics Inc's disclosure does not provide similar risk disclaimers or acknowledge the uncertainties surrounding their forward-looking statements.

**financial metrics or figures related to AI investments:**
Based on the provided disclosures, Hoth Therapeutics Inc's filing does not provide specific financial metrics or figures related to AI investments, whereas NOCERA INC's disclosure includes details about a potential transaction that could involve AI investments, including the possibility of issuing securities and the valuation mechanism. Therefore, NOCERA INC's disclosure offers more concrete information regarding potential AI investments and financial aspects compared to Hoth Therapeutics Inc's more general announcement about restructuring the business to pursue AI opportunities.


### 8. Grounded citation check
*Query: What did Eightco Holdings Inc report in their filing?*  
*Check: Answer should be traceable to an actually-retrieved source.*

Eightco Holdings Inc reported that on March 20, 2026, they issued a press release announcing additional investment in exchange for beneficial interests in the equity of OpenAI Group PBC. This information is from Item 7.01 Regulation FD Disclosure in the 8-K filing.
