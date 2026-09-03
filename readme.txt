get in the atmograph directory in terminal and carry out this commands

1. START THE DATABASE (Neo4j)
   Run this Docker command in your terminal:
   
   docker run --name atmograph-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -d neo4j:latest
   
   (Access the Neo4j Browser at http://localhost:7474 with user: neo4j, password: password)

2. START THE BACKEND (FastAPI)
   Open a terminal and run:
   
   cd backend
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   uvicorn main:app --reload
   
   (The API will run at http://127.0.0.1:8000. Swagger docs at http://127.0.0.1:8000/docs)

3. START THE FRONTEND (React)
   Open a NEW terminal and run:
   
   cd frontend
   npm install
   npm run dev
   
   (The app will run at http://localhost:5173)



================================================================================
HOW TO USE THE APPLICATION
================================================================================

1. EXPLORE THE GRAPH:
   - Use your mouse wheel to zoom in/out.
   - Click and drag the background to pan.
   - Click any node to open the Node Details panel on the right.

2. ANALYZE NEWS FOR RISK:
   - Look at the "News Risk Analyzer" box (top-left).
   - Paste a news snippet (e.g., "Workers at the Port of Rotterdam announced a three-week strike causing massive delays.")
   - Click "Analyze News".
   - Watch the graph update! Affected nodes will get a red (HIGH) or orange (MEDIUM) glowing border.

3. CLEAR RISKS:
   - Single Node: Click a risky node, then click the "Clear Risk for This Node" button in its details panel.
   - All Nodes: Click the "Clear All Risks" button in the News Analyzer box (requires confirmation).

================================================================================

GITHUB 
username - shashankpithva
password/personal access token - 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

