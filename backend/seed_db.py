# backend/seed_db.py
from database import get_db

def seed_database():
    print("Seeding Neo4j database with mock supply chain data...")
    driver = get_db()
    
    with driver.session() as session:
        print("Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")
        
        print("Creating nodes with baseline LOW risk...")
        session.run("""
        CREATE (c1:Country {name: "USA", risk_level: "LOW", risk_score: 0.1})
        CREATE (c2:Country {name: "China", risk_level: "LOW", risk_score: 0.1})
        CREATE (c3:Country {name: "Germany", risk_level: "LOW", risk_score: 0.1})
        CREATE (c4:Country {name: "Japan", risk_level: "LOW", risk_score: 0.1})
        CREATE (c5:Country {name: "Mexico", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (p1:Port {name: "Port of Los Angeles", risk_level: "LOW", risk_score: 0.1})
        CREATE (p2:Port {name: "Port of Shanghai", risk_level: "LOW", risk_score: 0.1})
        CREATE (p3:Port {name: "Port of Hamburg", risk_level: "LOW", risk_score: 0.1})
        CREATE (p4:Port {name: "Port of Tokyo", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (w1:Warehouse {name: "Warehouse_A", risk_level: "LOW", risk_score: 0.1})
        CREATE (w2:Warehouse {name: "Warehouse_B", risk_level: "LOW", risk_score: 0.1})
        CREATE (w3:Warehouse {name: "Warehouse_C", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (m1:Manufacturer {name: "Manufacturer_1", risk_level: "LOW", risk_score: 0.1})
        CREATE (m2:Manufacturer {name: "Manufacturer_2", risk_level: "LOW", risk_score: 0.1})
        CREATE (m3:Manufacturer {name: "Manufacturer_3", risk_level: "LOW", risk_score: 0.1})
        CREATE (m4:Manufacturer {name: "Manufacturer_4", risk_level: "LOW", risk_score: 0.1})
        CREATE (m5:Manufacturer {name: "Manufacturer_5", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (s1:Supplier {name: "Supplier_A", risk_level: "LOW", risk_score: 0.1})
        CREATE (s2:Supplier {name: "Supplier_B", risk_level: "LOW", risk_score: 0.1})
        CREATE (s3:Supplier {name: "Supplier_C", risk_level: "LOW", risk_score: 0.1})
        CREATE (s4:Supplier {name: "Supplier_D", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (pr1:Product {name: "Product_X", risk_level: "LOW", risk_score: 0.1})
        CREATE (pr2:Product {name: "Product_Y", risk_level: "LOW", risk_score: 0.1})
        CREATE (pr3:Product {name: "Product_Z", risk_level: "LOW", risk_score: 0.1})
        
        CREATE (s1)-[:SUPPLIES]->(m1)
        CREATE (s1)-[:SUPPLIES]->(m2)
        CREATE (s2)-[:SUPPLIES]->(m2)
        CREATE (s2)-[:SUPPLIES]->(m3)
        CREATE (s3)-[:SUPPLIES]->(m3)
        CREATE (s3)-[:SUPPLIES]->(m4)
        CREATE (s4)-[:SUPPLIES]->(m4)
        CREATE (s4)-[:SUPPLIES]->(m5)
        
        CREATE (m1)-[:SHIPS_TO]->(w1)
        CREATE (m2)-[:SHIPS_TO]->(w1)
        CREATE (m2)-[:SHIPS_TO]->(w2)
        CREATE (m3)-[:SHIPS_TO]->(w2)
        CREATE (m4)-[:SHIPS_TO]->(w3)
        CREATE (m5)-[:SHIPS_TO]->(w3)
        
        CREATE (w1)-[:TRANSPORTS_TO]->(p1)
        CREATE (w2)-[:TRANSPORTS_TO]->(p3)
        CREATE (w3)-[:TRANSPORTS_TO]->(p4)
        
        CREATE (p1)-[:LOCATED_IN]->(c1)
        CREATE (p2)-[:LOCATED_IN]->(c2)
        CREATE (p3)-[:LOCATED_IN]->(c3)
        CREATE (p4)-[:LOCATED_IN]->(c4)
        
        CREATE (m1)-[:PRODUCES]->(pr1)
        CREATE (m2)-[:PRODUCES]->(pr1)
        CREATE (m3)-[:PRODUCES]->(pr2)
        CREATE (m4)-[:PRODUCES]->(pr2)
        CREATE (m5)-[:PRODUCES]->(pr3)
        """)
        
        result = session.run("MATCH (n) RETURN count(n) AS count")
        count = result.single()["count"]
        print(f"✅ Successfully seeded database with {count} nodes (all baseline LOW risk)!")

if __name__ == "__main__":
    seed_database()