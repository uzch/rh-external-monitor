# First PoC — Visuals and Build Blueprint

## 1. First PoC flow

```mermaid
flowchart LR
    A[Public source set<br/>official company sources + independent reporting] --> B[Raw signal register<br/>title, date, source, URL]
    B --> C[Filter and deduplicate<br/>remove duplicate, stale, generic, and non-actionable items]
    C --> D[Apply Red Hat lens<br/>bounded seller hypotheses, not product/opportunity claims]
    D --> E[Transparent score and rank<br/>materiality + RH relevance + actionability + evidence + recency]
    E --> F[Account Pulse<br/>executive summary + top signals + seller moves]
    B --> G[Audit trail<br/>source URLs, score inputs, filter rationale]
    F --> H[Seller validation<br/>new? relevant? trusted? actionable?]
```

## 2. Clear boundary: manual POC versus coded product

```mermaid
flowchart TB
    subgraph NOW["First PoC — manual, controlled, source-traceable"]
        N1[Select account and coverage window]
        N2[Collect bounded source set]
        N3[Review, filter, deduplicate]
        N4[Map to Red Hat motion catalog]
        N5[Score and produce Account Pulse]
        N6[Collect seller feedback]
        N1 --> N2 --> N3 --> N4 --> N5 --> N6
    end

    subgraph LATER["Coded product — automate only what proved useful"]
        L1[Source connectors / scheduled retrieval]
        L2[Entity matching / normalization]
        L3[Duplicate detection + classifier]
        L4[Scoring service + evidence store]
        L5[Web portfolio and account pages]
        L6[Approved digest delivery + feedback loop]
        L1 --> L2 --> L3 --> L4 --> L5 --> L6
    end

    NOW -->|Validated workflow and acceptance criteria| LATER
```

## 3. Seller-first information hierarchy

```mermaid
flowchart TD
    A[Seller opens account view] --> B{Can the seller understand it in 30 seconds?}
    B -->|Yes| C[Executive summary]
    C --> D[Top 3 ranked signals]
    D --> E[Why it matters through a Red Hat lens]
    E --> F[Next account-team question or action]
    F --> G[Source link and score rationale available on demand]
    B -->|No| H[Remove raw detail from the first view; retain it in the audit trail]
    H --> C
```

## 4. Product acceptance criteria

| Criterion | Test |
|---|---|
| Seller usability | A seller can state: what changed, why it matters, and what should be validated next without opening the raw register. |
| Traceability | Every surfaced signal has a publication date, source URL, factual summary, score inputs, disposition, and a written rationale. |
| Relevance discipline | Generic content, duplicates, stale items, and events with no Red Hat-relevant action are retained in the audit trail but do not interrupt sellers. |
| No invented account claims | Product output states hypotheses and discovery questions; unproven account needs, architecture, opportunity, or buying intent remain UNKNOWN. |
| Automation readiness | The manual POC maps directly to the later functions: retrieval, normalize, dedupe, classify, rank, publish, and collect feedback. |

## 5. What is deliberately **not** in the first PoC

- RAG or vector database
- MCP server
- Autonomous agents
- CRM writeback
- Automatic Gmail send
- Internal Red Hat account data
- Enterprise deployment, SSO, or role-based access control

Those items are only justified after the seller output proves useful and the required access, ownership, governance, and data controls are known.
