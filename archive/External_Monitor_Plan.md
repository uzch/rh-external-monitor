# Red Hat External Monitor

## Six-Week SMART Delivery Roadmap

## Overview

External Monitor is a seller-support tool that turns noisy external account information into concise, Red Hat-relevant account intelligence.

The goal is to deliver a working pilot that shows sellers:

* What materially changed at an account  
* Why it may matter to Red Hat  
* What should be validated next  
* The source and rationale behind the recommendation

The JPMC PoC is the reference standard for the final product experience.

## Week 6 Outcome

By the end of Week 6, deliver a working pilot that:

* Monitors a controlled set of enterprise accounts  
* Collects and filters external account developments  
* Ranks the most relevant signals  
* Applies a Red Hat-specific lens  
* Produces seller-ready account views and briefs  
* Preserves source evidence and scoring rationale  
* Captures seller feedback for improvement

The objective is not enterprise scale. The objective is a credible, usable product that proves value and creates a clear path to scale.

---

# Six-Week SMART Plan

| Week | SMART Goal | Primary Deliverable |
| :---- | :---- | :---- |
| 1 | Define and approve the product scope, seller workflow, technical approach, source boundaries, and success criteria. | Approved roadmap, JPMC PoC, product contract, pilot scope |
| 2 | Build a navigable product experience using structured sample data that reflects the JPMC PoC. | Portfolio view, account page, signal cards, evidence view |
| 3 | Process real public account information through a working collection, filtering, ranking, and audit workflow. | Real source-linked signals for selected pilot accounts |
| 4 | Connect the working signal workflow to the product interface and generate seller-ready account briefs. | Multi-account pilot workflow and generated briefs |
| 5 | Validate usefulness with manager and seller feedback, then improve relevance, clarity, and actionability. | Feedback log, calibrated scoring, refined product |
| 6 | Deliver a stable pilot, final demonstration, documentation, and recommended next-phase plan. | Product demo, final deck, clean repository, handoff package |

---

## Week 1 — Define the Product

### SMART Goal

By the end of Week 1, finalize the product scope, pilot boundaries, seller workflow, technical approach, and success measures so development can begin without unresolved core decisions.

### Product Work

* Finalize the JPMC PoC as the product-output standard.  
    
* Confirm the seller workflow:  
    
  * Portfolio view  
  * Account view  
  * Executive summary  
  * Ranked signals  
  * Red Hat lens  
  * Recommended next action  
  * Evidence and rationale


* Define the criteria for selecting pilot accounts.  
    
* Confirm source boundaries and source-quality rules.  
    
* Finalize Keep, Watch, and Reject definitions.  
    
* Finalize the Red Hat Motion Catalog.  
    
* Define the seller-feedback rubric.

### Build Work

* Organize the repository around the JPMC PoC.  
    
* Convert JPMC PoC content into structured sample data.  
    
* Define the core data model:  
    
  * Account  
  * Source item  
  * Signal  
  * Score  
  * Red Hat motion  
  * Account brief  
  * Feedback


* Define the first product workflow and technical architecture.

### Week 1 Success Measure

* Product scope approved.  
* Pilot-account selection method approved.  
* Source boundaries confirmed.  
* Technical approach documented.  
* No unresolved decision blocks Week 2\.

---

## Week 2 — Build the Seller Experience

### SMART Goal

By the end of Week 2, deliver a clickable product experience that allows a seller to move from account portfolio to account detail to evidence-backed signal.

### Product Work

* Define what sellers see first.  
    
* Define what belongs on the portfolio page.  
    
* Define what belongs on the account page.  
    
* Finalize the signal-card format:  
    
  * What changed  
  * Why it matters  
  * Red Hat lens  
  * Suggested next action  
  * Source evidence


* Define feedback controls.

### Build Work

* Build a portfolio view.  
* Build an account-detail view.  
* Build signal cards.  
* Build executive-summary view.  
* Build source and rationale view.  
* Build simple feedback controls.  
* Populate the product with JPMC and structured sample data.

### Week 2 Success Measure

* A user can navigate the full seller workflow.  
* The JPMC PoC is represented in the product interface.  
* The spreadsheet is no longer required to understand the intended product experience.

---

## Week 3 — Build the Signal Workflow

### SMART Goal

By the end of Week 3, process real public account information into source-linked, filtered, ranked signals with a visible audit trail.

### Product Work

* Define source priority rules.  
    
* Define duplicate-handling rules.  
    
* Define when a signal is:  
    
  * Keep  
  * Watch  
  * Reject


* Build a test set using known JPMC examples.

### Build Work

* Build public-source collection workflow.  
* Match source items to accounts.  
* Normalize source records.  
* Remove duplicates.  
* Filter low-value and non-actionable content.  
* Score and rank retained signals.  
* Store source links, disposition, score rationale, and seller action.  
* Generate concise event summaries.

### Week 3 Success Measure

* At least one account completes the full signal workflow using real public-source content.  
* High-priority signals include source links, score rationale, and seller action.  
* Rejected items remain visible in the audit trail.

---

## Week 4 — Build the Pilot Product

### SMART Goal

By the end of Week 4, connect real processed signals to the product interface and generate usable seller briefs for the selected pilot accounts.

### Product Work

* Review automated output quality.  
* Identify weak signals, false positives, and weak Red Hat mappings.  
* Refine seller language and suggested actions.  
* Confirm pilot-account coverage is sufficient to demonstrate value.

### Build Work

* Connect processed signals to the portfolio view.  
* Add account priority or heat logic.  
* Generate executive account summaries.  
* Generate seller-ready account briefs.  
* Add refresh history.  
* Add feedback persistence.  
* Expand the workflow to the approved pilot-account set.

### Week 4 Success Measure

* Sellers can move from portfolio → account → signal → evidence.  
* Seller briefs are generated from processed account signals.  
* The product works across the selected pilot accounts.

---

## Week 5 — Validate and Improve

### SMART Goal

By the end of Week 5, collect structured feedback from the manager and available sellers, then improve the product based on documented findings.

### Product Work

* Conduct manager review.  
    
* Conduct seller or seller-proxy review where available.  
    
* Capture feedback on:  
    
  * Relevance  
  * Trust  
  * Actionability  
  * Clarity  
  * Noise  
  * Missing signals


* Identify strongest use cases and failure modes.

### Build Work

* Improve filtering logic.  
* Improve ranking logic.  
* Improve summary quality.  
* Improve Red Hat motion mapping.  
* Improve seller-action recommendations.  
* Improve interface clarity.  
* Improve demo reliability.

### Week 5 Success Measure

* Feedback is documented.  
* Product changes directly reflect feedback.  
* Strong and weak signal examples are identified.  
* Final demo workflow is stable.

---

## Week 6 — Final Delivery and Handoff

### SMART Goal

By the end of Week 6, deliver a stable, demonstrable pilot with complete documentation and a recommended next-phase plan.

### Product Work

* Prepare final manager narrative:  
    
  * Problem  
  * Product  
  * PoC evidence  
  * Pilot outcome  
  * Feedback  
  * Limitations  
  * Next phase


* Prepare final demo script.  
    
* Document decisions, learnings, and recommended follow-on work.

### Build Work

* Complete final QA.  
* Verify source links and score rationale.  
* Verify account refresh workflow.  
* Verify brief generation.  
* Clean the repository.  
* Finalize setup instructions, screenshots, and demo materials.

### Week 6 Success Measure

* Working pilot product.  
* Final manager presentation.  
* Demo-ready workflow.  
* Clean GitHub repository.  
* Clear continuation plan.

---

# Weekly Management Checkpoints

| Week | Manager Decision |
| :---- | :---- |
| 1 | Approve scope, pilot approach, and technical direction |
| 2 | Confirm seller experience is practical and easy to navigate |
| 3 | Confirm signal quality is strong enough to continue |
| 4 | Confirm the pilot demonstrates practical value |
| 5 | Review feedback and approve final refinements |
| 6 | Review final pilot and determine next-phase ownership |

---

# Technical Design Appendix

## 1\. Agent Workflow

Agents are included as controlled roles in the signal workflow.

They should not act independently without traceability. Each agent receives defined inputs, produces defined outputs, and passes its work to the next step.

| Agent | Role | Output |
| :---- | :---- | :---- |
| Source Agent | Collects account-related public information from approved sources | Raw source items with title, date, source, URL, and text |
| Signal Agent | Identifies duplicates, irrelevant content, stale items, and material account changes | Keep, Watch, or Reject recommendation with rationale |
| Red Hat Context Agent | Maps retained signals to approved Red Hat motions and discovery questions | Red Hat lens, bounded hypothesis, suggested seller question |
| Ranking Agent | Scores signals based on materiality, relevance, actionability, evidence, and recency | Ranked signal list with score explanation |
| Briefing Agent | Creates concise account summary and seller-ready brief | Executive summary, top signals, recommended moves |
| Quality Agent | Checks for missing evidence, unsupported claims, duplicate signals, and weak recommendations | Quality flags and required corrections |

### Agent Workflow

### ![][image1]

### Agent Guardrails

* Every kept signal must retain the original source URL.  
* Every ranked signal must include a score rationale.  
* Every Red Hat relevance statement must be a conversation hypothesis, not an opportunity claim.  
* Every seller action must be specific enough to use.  
* Rejected items remain in the audit trail.  
* The product must distinguish facts from interpretation.

---

## 2\. API Role

APIs are the connections that allow the product to retrieve information, process it, and display results.

### External Source APIs

Used to retrieve public account information from approved sources.

Examples:

* News or business-information source  
* Company newsroom  
* Investor-relations feed  
* Company technology blog  
* Approved public data feed

### Product APIs

Used by the product interface to display and manage information.

Examples:

Get accounts

Get account signals

Get signal evidence

Refresh an account

Generate an account brief

Submit seller feedback

### Model API

Used for structured tasks such as:

* Event extraction  
* Signal classification  
* Signal summarization  
* Red Hat motion mapping  
* Brief generation

Model output should be structured and reviewable, not uncontrolled free-form text.

---

## 3\. RAG Role

RAG is not the starting point for the product.

RAG becomes useful when the product needs to retrieve approved Red Hat knowledge to improve the Red Hat lens.

### RAG Inputs

* Approved Red Hat product information  
* Approved solution messaging  
* Approved industry playbooks  
* Approved seller content  
* Approved account context, if authorized

### RAG Role

| External account event \+ Approved Red Hat knowledge |
| :---: |

↓

| Grounded Red Hat relevance |
| :---: |

↓

| Seller discovery question |
| :---: |

### RAG Guardrail

External sources establish what changed at the account.

RAG only provides approved Red Hat context. It must not create unsupported claims about the customer, opportunity, buying intent, or architecture.

### RAG Decision Point

RAG should be added only when:

* An approved knowledge source exists.  
* The content has a clear owner.  
* Access is approved.  
* Retrieved content can be traced.  
* It improves output beyond the structured Red Hat Motion Catalog.

---

## 4\. MCP Role

MCP is an optional integration layer.

It is not required for the core product workflow.

Potential later uses:

* Create a Gmail draft from an account brief.  
* Retrieve approved Red Hat knowledge.  
* Retrieve authorized account context.  
* Create a CRM note.  
* Send a signal to an approved collaboration channel.

The pilot should use MCP only when an approved integration clearly improves the seller workflow.

Do not build a custom MCP server unless an existing approved connection cannot support a high-value need.  


[image1]: <data:image/png;base64,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>