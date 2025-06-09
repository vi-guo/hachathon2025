import networkx as nx

# ---------- build the graph ----------
G = nx.MultiDiGraph()          # one edge object per relation, even between same pair

# 1. human users
G.add_node("a_foo", kind="user")
G.add_node("a_bar", kind="user")

# 2. functional DB account
G.add_node("db_reader", kind="db_account")

# 3. database & its tables
G.add_node("db-A", kind="database")
G.add_node("table1", kind="table", parent_db="db-A")
G.add_node("table2", kind="table", parent_db="db-A")

# 4. trust & permission edges
#    Users → db_reader           : they can assume/impersonate it
G.add_edge("a_foo", "db_reader", relation="assume")
G.add_edge("a_bar", "db_reader", relation="assume")

#    db_reader → tables          : it can query these objects
#    Add an attribute that lists *which* human users are allowed at each table.
G.add_edge("db_reader", "table1",
           relation="access", allowed_users={"a_foo"})
G.add_edge("db_reader", "table2",
           relation="access", allowed_users={"a_bar"})

# ---------- helper: check effective access ----------
def can_user_access(user: str, table: str, graph: nx.MultiDiGraph) -> bool:
    """
    Return True iff *user* can reach *table* through
    (user --assume--> db_reader --access--> table)
    and is in the allowed_users set for that edge.
    """
    for _, db_acct, data1 in graph.out_edges(user, data=True):
        if data1.get("relation") != "assume":
            continue
        for _, tbl, data2 in graph.out_edges(db_acct, data=True):
            if data2.get("relation") == "access" and tbl == table:
                return user in data2.get("allowed_users", set())
    return False

# ---------- quick verification ----------
print("a_foo → table1 ?", can_user_access("a_foo", "table1", G))  # True
print("a_foo → table2 ?", can_user_access("a_foo", "table2", G))  # False
print("a_bar → table2 ?", can_user_access("a_bar", "table2", G))  # True

import matplotlib.pyplot as plt
nx.draw(G, with_labels=True, node_size=1800, font_size=10)
plt.show()
