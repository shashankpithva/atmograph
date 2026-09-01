// 1. Create Countries
MERGE (c_usa:Country {name: 'USA'})
MERGE (c_chn:Country {name: 'China'})
MERGE (c_deu:Country {name: 'Germany'})
MERGE (c_jpn:Country {name: 'Japan'})
MERGE (c_bra:Country {name: 'Brazil'})
MERGE (c_nld:Country {name: 'Netherlands'})
MERGE (c_twn:Country {name: 'Taiwan'})

// 2. Create Ports
MERGE (p_la:Port {name: 'Port of Los Angeles', code: 'USLAX'})
MERGE (p_sh:Port {name: 'Port of Shanghai', code: 'CNSHA'})
MERGE (p_hh:Port {name: 'Port of Hamburg', code: 'DEHAM'})
MERGE (p_rd:Port {name: 'Port of Rotterdam', code: 'NLRTM'})
MERGE (p_ss:Port {name: 'Port of Santos', code: 'BRSSZ'})

// 3. Create Warehouses
MERGE (w_la:Warehouse {name: 'LA Distribution Center', capacity: 50000})
MERGE (w_sh:Warehouse {name: 'Shanghai Hub', capacity: 80000})
MERGE (w_hh:Warehouse {name: 'Hamburg Storage', capacity: 40000})
MERGE (w_rd:Warehouse {name: 'Rotterdam Depot', capacity: 60000})
MERGE (w_ss:Warehouse {name: 'Sao Paulo Warehouse', capacity: 30000})

// 4. Create Manufacturers
MERGE (m_fox:Manufacturer {name: 'Foxconn', type: 'Electronics'})
MERGE (m_tes:Manufacturer {name: 'Tesla', type: 'Automotive'})
MERGE (m_bmw:Manufacturer {name: 'BMW', type: 'Automotive'})
MERGE (m_tyt:Manufacturer {name: 'Toyota', type: 'Automotive'})
MERGE (m_emb:Manufacturer {name: 'Embraer', type: 'Aerospace'})

// 5. Create Suppliers
MERGE (s_tsm:Supplier {name: 'TSMC', sector: 'Semiconductors'})
MERGE (s_bos:Supplier {name: 'Bosch', sector: 'Auto Parts'})
MERGE (s_pan:Supplier {name: 'Panasonic', sector: 'Batteries'})
MERGE (s_byd:Supplier {name: 'BYD', sector: 'Batteries'})
MERGE (s_val:Supplier {name: 'Vale', sector: 'Mining'})

// 6. Create Products
MERGE (pr_chip:Product {name: 'Microchips', category: 'Electronics'})
MERGE (pr_ev:Product {name: 'Electric Vehicles', category: 'Automotive'})
MERGE (pr_sedan:Product {name: 'Luxury Sedans', category: 'Automotive'})
MERGE (pr_hybrid:Product {name: 'Hybrid Cars', category: 'Automotive'})
MERGE (pr_ore:Product {name: 'Iron Ore', category: 'Raw Materials'})
MERGE (pr_plane:Product {name: 'Commercial Aircraft', category: 'Aerospace'})

// --- RELATIONSHIPS ---

// LOCATED_IN (Nodes to Countries)
MERGE (p_la)-[:LOCATED_IN]->(c_usa)
MERGE (p_sh)-[:LOCATED_IN]->(c_chn)
MERGE (p_hh)-[:LOCATED_IN]->(c_deu)
MERGE (p_rd)-[:LOCATED_IN]->(c_nld)
MERGE (p_ss)-[:LOCATED_IN]->(c_bra)
MERGE (w_la)-[:LOCATED_IN]->(c_usa)
MERGE (w_sh)-[:LOCATED_IN]->(c_chn)
MERGE (w_hh)-[:LOCATED_IN]->(c_deu)
MERGE (w_rd)-[:LOCATED_IN]->(c_nld)
MERGE (w_ss)-[:LOCATED_IN]->(c_bra)
MERGE (m_tes)-[:LOCATED_IN]->(c_usa)
MERGE (m_fox)-[:LOCATED_IN]->(c_chn)
MERGE (m_bmw)-[:LOCATED_IN]->(c_deu)
MERGE (m_tyt)-[:LOCATED_IN]->(c_jpn)
MERGE (m_emb)-[:LOCATED_IN]->(c_bra)
MERGE (s_tsm)-[:LOCATED_IN]->(c_twn)
MERGE (s_bos)-[:LOCATED_IN]->(c_deu)
MERGE (s_pan)-[:LOCATED_IN]->(c_jpn)
MERGE (s_byd)-[:LOCATED_IN]->(c_chn)
MERGE (s_val)-[:LOCATED_IN]->(c_bra)

// PRODUCES (Manufacturers/Suppliers to Products)
MERGE (m_fox)-[:PRODUCES]->(pr_chip)
MERGE (m_tes)-[:PRODUCES]->(pr_ev)
MERGE (m_bmw)-[:PRODUCES]->(pr_sedan)
MERGE (m_tyt)-[:PRODUCES]->(pr_hybrid)
MERGE (m_emb)-[:PRODUCES]->(pr_plane)
MERGE (s_val)-[:PRODUCES]->(pr_ore)

// SUPPLIES (Suppliers to Manufacturers)
MERGE (s_tsm)-[:SUPPLIES {volume: 'high'}]->(m_fox)
MERGE (s_bos)-[:SUPPLIES {volume: 'medium'}]->(m_bmw)
MERGE (s_pan)-[:SUPPLIES {volume: 'high'}]->(m_tes)
MERGE (s_byd)-[:SUPPLIES {volume: 'high'}]->(m_tes)
MERGE (s_val)-[:SUPPLIES {volume: 'low'}]->(m_emb)

// SHIPS_TO (Port to Port)
MERGE (p_sh)-[:SHIPS_TO {distance_km: 10500}]->(p_la)
MERGE (p_la)-[:SHIPS_TO {distance_km: 9000}]->(p_rd)
MERGE (p_rd)-[:SHIPS_TO {distance_km: 8000}]->(p_ss)
MERGE (p_hh)-[:SHIPS_TO {distance_km: 10000}]->(p