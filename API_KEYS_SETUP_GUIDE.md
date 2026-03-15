# 🔑 API Keys Setup Guide for Artemis AI Core

## 🚨 Important Security Notice
- **NEVER** commit your actual API keys to version control
- Keep your `.env` file secure and local only
- Use different API keys for development and production
- Regularly rotate your API keys for security

## 📋 Required API Keys

### 1. Google Gemini API Key (REQUIRED - Primary)
**Purpose**: Powers the Artemis AI conversational interface

**Steps to get your key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign up or log in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file:
   ```
   GOOGLE_API_KEY=your-actual-gemini-key-here
   ```

**Cost**: Google Gemini 1.5 Pro pricing:
- Input: $7 per 1M tokens
- Output: $21 per 1M tokens
- **65-70% cheaper than GPT-4!**

**Free tier**: Generous free quota for testing and development.

### 2. OpenAI API Key (ALTERNATIVE)
**Purpose**: Alternative AI provider (if you prefer OpenAI)

**Steps to get your key:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key and add it to your `.env` file:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   AI_PROVIDER=openai
   ```

**Note**: Gemini is recommended due to lower costs and better performance for your use case.

### 2. Database Setup (REQUIRED)
**Current Setup**: Using SQLite for development (no API key needed)

**For Production**: Consider upgrading to PostgreSQL:
1. Set up a PostgreSQL database (locally or cloud)
2. Update `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/flashloan_db
   ```

## 📋 Optional API Keys (For Enhanced Features)

### 3. Infura (Blockchain Data)
**Purpose**: Access Ethereum and other blockchain networks

**Steps:**
1. Visit [Infura.io](https://infura.io/)
2. Create a free account
3. Create a new project
4. Copy your Project ID and Secret
5. Add to `.env`:
   ```
   INFURA_PROJECT_ID=your_project_id
   INFURA_PROJECT_SECRET=your_project_secret
   ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
   ```

**Free tier**: 100,000 requests per day

### 4. Alchemy (Alternative to Infura)
**Purpose**: Alternative blockchain data provider

**Steps:**
1. Visit [Alchemy.com](https://www.alchemy.com/)
2. Create a free account
3. Create a new app
4. Copy your API key
5. Add to `.env`:
   ```
   ALCHEMY_API_KEY=your_alchemy_api_key
   ```

### 5. Redis (Performance Enhancement)
**Purpose**: Caching and performance optimization

**For Development**: Not required, caching is handled in-memory
**For Production**: 
1. Install Redis locally or use cloud service
2. Add to `.env`:
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

## 🛠️ Setting Up Your Environment

### Step 1: Configure Google Gemini (REQUIRED)
1. Open `c:\Users\mahia\New_Flashloan\artemis_core\.env`
2. Replace `your_google_api_key_here` with your actual Google API key
3. Ensure `AI_PROVIDER=gemini` is set
4. Save the file

### Step 2: Test Your Setup
1. Open PowerShell in the project directory
2. Navigate to Artemis Core:
   ```powershell
   cd artemis_core
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start Artemis AI Core:
   ```powershell
   python artemis_ai_core.py
   ```
5. You should see: "Artemis AI Core starting on http://0.0.0.0:8082"

### Step 3: Test the Frontend
1. Open a new PowerShell window
2. Navigate to project root:
   ```powershell
   cd c:\Users\mahia\New_Flashloan
   ```
3. Install Node.js dependencies:
   ```powershell
   npm install
   ```
4. Start the frontend:
   ```powershell
   npm run dev
   ```
5. Open browser to `http://localhost:5173`
6. Navigate to the "Artemis AI" section and test the chat

## 🔍 Troubleshooting

### Gemini API Key Issues:
- **Error**: "Invalid API key"
  - **Solution**: Double-check your API key is correct and has no extra spaces
- **Error**: "Rate limit exceeded"  
  - **Solution**: You've hit your usage limit. Check your Google AI Studio dashboard

### OpenAI API Key Issues (if using as alternative):
- **Error**: "Invalid API key"
  - **Solution**: Double-check your API key is correct and has no extra spaces
- **Error**: "Rate limit exceeded"
  - **Solution**: You've hit your usage limit. Check your OpenAI dashboard

### Connection Issues:
- **Error**: "Cannot connect to Artemis AI Core"
  - **Solution**: Ensure the backend is running on port 8082
- **Error**: "CORS error"
  - **Solution**: Check `ALLOWED_ORIGINS` in `.env` includes your frontend URL

### Database Issues:
- **Error**: "Database connection failed"
  - **Solution**: Check `DATABASE_URL` format and database accessibility

## 💰 Cost Considerations

### Free Tier Usage:
- **Google Gemini**: Generous free quota for development and testing
- **OpenAI**: $5 free credits (if using as alternative)
- **Infura**: 100K requests/day (sufficient for development)
- **Alchemy**: 300M compute units/month free

### Expected Costs for Active Development:
- **Google Gemini**: $5-15/month for moderate usage (65-70% cheaper than OpenAI!)
- **OpenAI**: $10-30/month (if using as alternative)
- **Infura/Alchemy**: Usually free tier sufficient for development
- **Database**: Free (SQLite) or $5-20/month (cloud PostgreSQL)

## 🎯 Next Steps

1. **Immediate**: Set up OpenAI API key and test basic functionality
2. **Short-term**: Add blockchain RPC endpoints for live data
3. **Long-term**: Set up production database and caching layer

## 📞 Support

If you encounter issues:
1. Check the logs in `logs/artemis.log`
2. Verify all required dependencies are installed
3. Ensure your API keys are valid and have sufficient quota
4. Check the console output for specific error messages

Remember: Start with just the OpenAI API key for basic functionality, then gradually add other services as needed.
