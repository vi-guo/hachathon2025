user case 1:
sequenceDiagram
    participant App as "Application (FID)"
    box rgb(235, 245, 255) MCP Server
        participant DBTool as "DB-Query Tool"
    end
    participant DB as "Database"

    %% 1 ── Client request
    App->>+DBTool: Request data

    %% 2 ── Query DB
    DBTool->>+DB: Execute SQL query
    DB-->>-DBTool: Result set

    %% 3 ── Return to client
    DBTool-->>-App: Return dataset
