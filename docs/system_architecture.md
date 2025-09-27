flowchart LR
  %% System Architecture Overview

  subgraph Sources[External Sources]
    SRC[Market Data Sources]
  end

  subgraph Storage[Storage]
    MarketDB[(SQLite: data/market.db)]
    AppDB[(SQLite: app/data.db)]
  end

  subgraph Agents[Core Agents]
    DC[[Data Collector]]
    PO[[Price Optimizer]]
    GEA[[Governance Execution Agent]]
    AS[[Alert Service]]
  end

  Bus{{Async Event Bus}}

  subgraph UI[User Interface]
    UIBridge[[Pricing UI Integration]]
    Streamlit[[Streamlit App]]
  end

  subgraph Notifiers[Notification Sinks]
    Slack[/Slack/]
    Email[/Email/]
    Webhook[/Webhook/]
    UISink[/UI Alerts/]
  end

  %% Data ingestion
  SRC --> DC
  DC --> MarketDB
  DC -- market.tick --> Bus

  %% Optimization and proposals
  MarketDB --> PO
  PO -- price.proposal --> Bus
  Bus -- price.proposal --> GEA

  %% Governance execution, guardrails, and updates
  AppDB --> GEA
  GEA --> MarketDB
  GEA -- price.update --> Bus

  %% UI integration and settings
  Bus -- price.update --> UIBridge
  UIBridge --> Streamlit
  Streamlit <---> AppDB
  Streamlit --> MarketDB

  %% Alerts
  Bus -- alert.event --> AS
  AS --> Slack
  AS --> Email
  AS --> Webhook
  AS --> UISink
  UISink --> Streamlit

  %% Notes
  classDef db fill:#eef,stroke:#99f,stroke-width:1px;
  class MarketDB,AppDB db;
