user case 1:
```mermaid
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


user case 2
```mermaid
sequenceDiagram
    participant User as "Human User (SID)"
    box rgb(235, 245, 255) MCP Server
        participant DBTool as "DB-Query Tool"
        participant KerbAuth as "Kerberos-Auth Function"
        participant GraphAuth as "Graph-Author Model"
    end
    participant DB as "Database"

    %% 1 ── Client request with Kerberos SPNEGO token
    User->>+DBTool: 1. Request (Kerberos SPNEGO token)

    %% 2 ── Verify Kerberos token
    DBTool->>+KerbAuth: 2. Validate token
    KerbAuth-->>-DBTool: Token valid / SID info

    %% 3 ── Permission check via graph-author
    DBTool->>+GraphAuth: 3. Check permission
    GraphAuth-->>-DBTool: Permission OK

    %% 4 ── Query DB
    DBTool->>+DB: 4. Execute SQL query
    DB-->>-DBTool: Dataset

    %% 5 ── Return results
    DBTool-->>-User: 5. Return dataset
