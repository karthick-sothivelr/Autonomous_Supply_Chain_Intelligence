# VeganFlow: Autonomous Supply Chain Intelligence

## Problem Statement
Retail supply chain management is a high-stakes balancing act, especially for niche sectors like vegan retail where products have short shelf-lives and tight margins.

**The Core Problem:** Traditional procurement is reactive, manual, and fragmented. Store managers spend hours juggling inventory spreadsheets, vendor emails, and point-of-sale data. This disconnection leads to two costly failures:
1.  **Stockouts:** High-velocity items run out unexpectedly, causing lost revenue and customer dissatisfaction.
2.  **Waste:** Over-ordering perishables leads to spoilage, directly impacting the bottom line.

This is an interesting problem to solve because it requires balancing conflicting constraints—price, delivery speed, expiry dates, and vendor reliability—in real-time. Standard automation tools fail here because they lack the reasoning capabilities to negotiate prices or adapt to dynamic market conditions.

## Why Agents?
Agents are the ideal solution because supply chain management is **inherently non-deterministic** and requires **autonomous negotiation**.

* **Complex Decision Making:** Unlike a standard script that follows linear `if-this-then-that` logic, an agent can evaluate trade-offs. It can decide to pay a slightly higher price for faster delivery if a critical item is about to stock out, or wait for a better deal if inventory is sufficient.
* **Autonomous Action:** Agents close the loop. Instead of just alerting a human about low stock (passive monitoring), an agent can actively contact vendors, negotiate terms, and finalize an order (active execution).
* **Scalability:** A multi-agent system can simultaneously monitor thousands of SKUs and negotiate with dozens of vendors in parallel—a task impossible for a human team to do manually at speed.

## What I Created
I built **VeganFlow**, a hierarchical Multi-Agent System (MAS) designed to fully autonomize retail operations.

### Architecture Overview
The system follows a **Hierarchical Delegation Pattern** with a central "Brain" and specialized "Workers."

1.  **Orchestrator (Store Manager):** The root agent that interfaces with the user. It understands high-level goals (e.g., "Analyze inventory risks") and delegates tasks to the appropriate specialists.
2.  **Inventory Agent (Shelf Monitor):** The "Eyes" of the store. It has direct SQL access to the local retail database (`veganflow_store.db`) to analyze stock levels, sales velocity, and expiry dates. It identifies *what* needs to be bought.
3.  **Procurement Agent (Negotiator):** The "Hands" of the store. It takes requirements from the Inventory Agent and executes the solution. It uses the **Agent-to-Agent (A2A)** protocol to connect with external vendor agents, negotiates prices based on strategic targets held in memory, and finalizes deals.
4.  **Vendor Ecosystem:** A simulated cluster of **11 independent agents** representing external suppliers. Each vendor has its own personality, pricing model, reliability score, and API endpoint.


## Demo
In the demonstration scenario, we simulate a critical stockout event for "Oat Barista Blend."

1.  **The Trigger:** The user asks the system: *"Check stock for Oat Barista Blend."*
2.  **The Analysis:** The **Shelf Monitor** queries the database and reports a critical status: only 0.8 days of supply remain.
3.  **The Delegation:** The Orchestrator automatically activates the **Procurement Agent** to resolve the shortage.
4.  **The Action:** The Procurement Agent consults its long-term memory for price targets ($3.40) and identifies "Clark Distributing" as a potential vendor. It initiates an **A2A handshake** over HTTP.
5.  **The Negotiation:** The agent autonomously negotiates. It rejects the initial list price and counters with a 10% discount based on volume.
6.  **The Result:** The vendor accepts the offer, and the deal is secured without human intervention.

Refer to the recorded video: [Click here to watch the video](https://www.youtube.com/watch?v=PIEEjxroJ-0)

## The Build
VeganFlow was built using a modern, agent-native stack designed for production reliability:

* **Framework:** **Google Agent Development Kit (ADK)** for the core agent runtime, tool definitions, and Agent-to-Agent (A2A) protocol support.
* **Models:**
    * **Gemini 2.5 Pro:** Used for the Orchestrator to handle complex reasoning and delegation logic.
    * **Gemini 2.5 Flash:** Used for specialized workers and vendor agents to minimize latency and cost.
* **State Management:** **SQLite** for the retail database simulation and **ADK Session/Memory** for maintaining conversation context.
* **Evaluation:** **ADK Eval** CLI for systematic regression testing of agent behaviors against a "Golden Dataset."
* **Deployment:** The core agent logic is containerized and deployed on **Google Cloud Vertex AI Agent Engine**, while the vendor ecosystem runs on **Cloud Run** to simulate a distributed network.

## If I Had More Time
While VeganFlow is a fully functional prototype, I envision several key enhancements for V2:

* **Human-in-the-Loop (HITL) for Price Thresholds:** Currently, the agent acts autonomously. I would implement a "Supervisor Check" pattern where deals exceeding a certain variance from the target price (e.g., >15% higher) automatically pause execution and request human approval via a notification system.
* **Central Vendor Registry:** Instead of hardcoding vendor ports, I would build a dynamic **Vendor Agent Registry**. This would act as a "Yellow Pages" for agents, allowing new suppliers to register their Agent Cards dynamically. The Procurement Agent could then discover new market participants at runtime, fostering a truly open marketplace.
* **Predictive Inventory Modeling:** I would upgrade the Inventory Agent from reactive (alerting on low stock) to predictive. By integrating a time-series forecasting model, the agent could order stock *before* levels get low based on seasonal trends and sales velocity.
* **Multi-Modal Product Inspection:** I would add a vision capability to the Inventory Agent, allowing it to analyze images from shelf cameras to detect spoilage or visual stock discrepancies that data alone might miss.