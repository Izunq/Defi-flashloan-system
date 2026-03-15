"""
Artemis AI Core - Google Gemini Implementation
AI-powered conversational interface for DeFi flash loan arbitrage system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import google.generativeai as genai
import openai
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "8192"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./artemis.db")
ARTEMIS_PORT = int(os.getenv("ARTEMIS_PORT", "8082"))
ARTEMIS_HOST = os.getenv("ARTEMIS_HOST", "0.0.0.0")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-please-change-in-production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Initialize AI services
if AI_PROVIDER == "gemini" and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel(GEMINI_MODEL)
    logger = logging.getLogger(__name__)
    logger.info(f"Initialized Gemini AI with model: {GEMINI_MODEL}")
elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger = logging.getLogger(__name__)
    logger.info("Initialized OpenAI API")
else:
    logger = logging.getLogger(__name__)
    logger.warning("No AI API key configured. AI functionality will be limited.")

# Initialize FastAPI app
app = FastAPI(title="Artemis AI Core", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ArtemisMessage:
    id: str
    type: str  # 'user', 'artemis', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class DatabaseConnector:
    """Handles database connections and queries for context retrieval"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
    
    async def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trade data for context"""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT strategy_id, profit_usd, gas_cost, timestamp, success
                    FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT $1
                """, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    async def get_strategy_performance(self, strategy_id: str = None) -> Dict:
        """Get strategy performance metrics"""
        if not self.pool:
            return {}
        
        try:
            async with self.pool.acquire() as conn:
                if strategy_id:
                    query = """
                        SELECT 
                            strategy_id,
                            COUNT(*) as total_trades,
                            SUM(profit_usd) as total_profit,
                            AVG(profit_usd) as avg_profit,
                            COUNT(*) FILTER (WHERE success = true) as successful_trades
                        FROM trades 
                        WHERE strategy_id = $1
                        GROUP BY strategy_id
                    """
                    row = await conn.fetchrow(query, strategy_id)
                else:
                    query = """
                        SELECT 
                            strategy_id,
                            COUNT(*) as total_trades,
                            SUM(profit_usd) as total_profit,
                            AVG(profit_usd) as avg_profit,
                            COUNT(*) FILTER (WHERE success = true) as successful_trades
                        FROM trades 
                        GROUP BY strategy_id
                        ORDER BY total_profit DESC
                    """
                    rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
                
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Error fetching strategy performance: {e}")
            return {}

class ArtemisRAG:
    """Retrieval-Augmented Generation for context-aware responses"""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector
        
        # Initialize AI based on provider
        if AI_PROVIDER == "gemini" and GOOGLE_API_KEY:
            self.ai_model = genai.GenerativeModel(GEMINI_MODEL)
            logger.info("ArtemisRAG initialized with Gemini")
        elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            self.ai_model = None  # Will use openai directly
            logger.info("ArtemisRAG initialized with OpenAI")
        else:
            self.ai_model = None
            logger.warning("No AI model configured")
        
        # System prompt for Artemis
        self.system_prompt = """
        You are Artemis, an advanced AI assistant for a flash loan arbitrage trading system.
        
        You have access to:
        - Real-time trading data and performance metrics
        - Strategy information and backtesting results  
        - Risk management alerts and system health
        - Smart contract interaction data
        
        Your capabilities:
        - Analyze trading performance and suggest optimizations
        - Explain complex DeFi concepts and strategies
        - Monitor risk and alert to potential issues
        - Generate reports and visualizations
        - Execute read-only queries and simulations
        
        Always be:
        - Precise and data-driven in your analysis
        - Clear in explaining complex financial concepts
        - Proactive in identifying risks and opportunities
        - Helpful in suggesting actionable next steps
        
        When providing numerical data, always include context and significance.
        When suggesting actions, explain the reasoning and potential impact.
        """
    
    async def build_context(self, query: str) -> str:
        """Build contextual information for the query"""
        context_parts = []
        
        # Add recent trades context
        recent_trades = await self.db.get_recent_trades(5)
        if recent_trades:
            context_parts.append(f"Recent Trades: {json.dumps(recent_trades, default=str)}")
          # Add strategy performance context
        strategy_performance = await self.db.get_strategy_performance()
        if strategy_performance:
            context_parts.append(f"Strategy Performance: {json.dumps(strategy_performance, default=str)}")
        
        # Add current timestamp
        context_parts.append(f"Current Time: {datetime.now().isoformat()}")
        
        return "\n\n".join(context_parts)
    
    async def generate_response(self, user_query: str) -> Dict[str, Any]:
        """Generate AI response with context using Gemini or OpenAI"""
        try:
            # Build context from real data
            context = await self.build_context(user_query)
            
            if AI_PROVIDER == "gemini" and self.ai_model:
                # Use Gemini
                full_prompt = f"""
{self.system_prompt}

Current Context:
{context}

User Query: {user_query}

Please provide a helpful and informative response based on the context above.
"""
                
                response = await self.ai_model.generate_content_async(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=GEMINI_MAX_TOKENS,
                        temperature=GEMINI_TEMPERATURE,
                    )
                )
                
                ai_response = response.text
                
            elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
                # Use OpenAI
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": f"Current Context:\n{context}"},
                    {"role": "user", "content": user_query}
                ]
                
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                ai_response = response.choices[0].message.content
                
            else:
                # Fallback response when no AI is configured
                ai_response = f"I received your query: '{user_query}', but I don't have access to AI services at the moment. Please configure either GOOGLE_API_KEY or OPENAI_API_KEY in your .env file."
            
            # Determine if response should include actions
            actions = self._extract_actions(ai_response, user_query)
            
            return {
                "content": ai_response,
                "actions": actions,
                "confidence": 0.85,  # Could be calculated based on context quality
                "sources": ["database", "real-time"],
                "timestamp": datetime.now().isoformat(),
                "provider": AI_PROVIDER
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "content": f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}",
                "actions": [],
                "confidence": 0.0,
                "sources": [],
                "timestamp": datetime.now().isoformat(),
                "provider": AI_PROVIDER
            }
    
    def _extract_actions(self, response: str, query: str) -> List[Dict]:
        """Extract potential actions from AI response"""
        actions = []
        
        # Simple action detection (can be made more sophisticated)
        if "strategy" in query.lower() and "performance" in query.lower():
            actions.append({
                "type": "view_chart",
                "label": "View Performance Chart",
                "endpoint": "/api/charts/strategy-performance"
            })
        
        if "risk" in query.lower() or "alert" in query.lower():
            actions.append({
                "type": "view_risks",
                "label": "View Risk Dashboard",
                "endpoint": "/api/risk/current"
            })
        
        if "execute" in query.lower() or "trade" in query.lower():
            actions.append({
                "type": "simulate",
                "label": "Run Simulation",
                "endpoint": "/api/simulate"
            })
        
        return actions

class ConnectionManager:
    """Manage WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, websocket: WebSocket, message: Dict):
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

# Initialize components
db_connector = DatabaseConnector(DATABASE_URL)
artemis_rag = ArtemisRAG(db_connector)
connection_manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Initialize the service"""
    await db_connector.connect()
    logger.info("Artemis AI Core started successfully")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    if db_connector.pool:
        await db_connector.pool.close()
    logger.info("Artemis AI Core shut down")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "artemis-ai-core",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.websocket("/ws/artemis")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI conversation"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_query = message_data.get("content", "")
            conversation_id = message_data.get("conversation_id", "default")
            
            logger.info(f"Received query: {user_query}")
            
            # Send "thinking" indicator
            await connection_manager.send_message(websocket, {
                "type": "thinking",
                "content": "Artemis is analyzing your query..."
            })
            
            # Generate AI response
            ai_response = await artemis_rag.generate_response(user_query)
            
            # Send AI response
            response_message = {
                "type": "artemis",
                "content": ai_response["content"],
                "metadata": {
                    "actions": ai_response["actions"],
                    "confidence": ai_response["confidence"],
                    "sources": ai_response["sources"]
                },
                "timestamp": ai_response["timestamp"],
                "conversation_id": conversation_id
            }
            
            await connection_manager.send_message(websocket, response_message)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.send_message(websocket, {
            "type": "error",
            "content": f"An error occurred: {str(e)}"
        })

@app.post("/api/query")
async def query_endpoint(query: Dict[str, str]):
    """REST endpoint for AI queries"""
    user_query = query.get("query", "")
    
    if not user_query:
        return {"error": "Query is required"}
    
    response = await artemis_rag.generate_response(user_query)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "artemis_core:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_level="info"
    )
