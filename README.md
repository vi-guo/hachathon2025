# hachathon2025

sequenceDiagram
    participant Client
    box rgb(235, 245, 255) MCP Server
        participant Tool A as "Tool A (Auth)"
        participant Tool B as "Tool B (Data)"
    end
    participant Token Broker Service
    participant Database

    Client->>+Tool A: 1. Request with Kerberos TGT for Jane Doe
    Note right of Tool A: Tool A receives the user's identity token.
    
    Tool A->>Tool A: 2. Verify token & check permissions
    Note right of Tool A: A mock authorization model confirms <br/>Jane can use the 'db_reader' account.
    
    Tool A->>+Token Broker Service: 3. Request functional token for 'db_reader'
    
    Token Broker Service-->>-Tool A: 4. Return 'db_reader' token
    Note over Tool A, Tool B: Token is now available within the MCP Server's context.
    deactivate Tool A
    
    activate Tool B
    Tool B->>+Database: 5. Authenticate with 'db_reader' token & execute SQL query
    Note left of Database: The connection to the database <br/>uses the functional account, not Jane's.
    
    Database-->>-Tool B: 6. Return dataset
    
    Tool B-->>-Client: 7. Send final results back to the user
    deactivate Tool B

