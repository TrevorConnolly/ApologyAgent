# 🕊️ Apology Agent

A sophisticated AI-powered system that helps create personalized apology strategies and reconciliation plans for various relationship situations.

## 📖 Overview

The Apology Agent is designed to assist users in crafting meaningful apologies by analyzing the context of a situation, understanding recipient preferences, and generating comprehensive reconciliation strategies that include personalized messages, gift recommendations, and thoughtful gestures.

## ✨ Features

- **🖥️ Beautiful Web Dashboard**: User-friendly interface for creating apologies without coding
- **Personalized Apology Messages**: Generate heartfelt, context-aware apology messages
- **Smart Gift Recommendations**: AI-powered gift suggestions based on recipient preferences
- **Restaurant Booking**: Find and book appropriate dining venues for reconciliation
- **Flower Delivery**: Arrange thoughtful floral arrangements
- **Budget Management**: Work within specified budget constraints
- **Location-Aware Suggestions**: Tailored recommendations based on geographic location

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Required dependencies (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ApologyAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python start.py
```

The server will be available at `http://localhost:8000`

## 🖥️ Dashboard Access

### Web Interface

The Apology Agent includes a beautiful, user-friendly web dashboard for creating apologies without using the command line.

#### Access the Dashboard

1. **Start the server** (if not already running):
   ```bash
   python start.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:8000/
   ```

3. **Alternative dashboard URL**:
   ```
   http://localhost:8000/dashboard
   ```

#### Dashboard Features

- **📝 Apology Details Form** - Easy input for all required fields
- **🎁 Recipient Preferences** - Capture personal details for better recommendations
- **🕊️ One-Click Generation** - Generate apology strategies with a single button
- **✨ Beautiful Response Display** - Formatted, easy-to-read apology plans
- **📱 Responsive Design** - Works perfectly on desktop and mobile devices

#### Using the Dashboard

1. **Fill out the form** with your situation details:
   - What happened (required)
   - Recipient's name (required)
   - Relationship type (required)
   - Severity level 1-10 (required)
   - Budget (required)
   - Location (required)
   - Recipient preferences (optional)

2. **Click "🕊️ Generate Apology Strategy"**

3. **View your personalized apology plan** including:
   - Personalized apology message
   - Strategy explanation
   - Recommended actions with costs
   - Success probability
   - Follow-up suggestions

#### Pre-filled Example

The dashboard comes pre-filled with example data for easy testing. You can modify any field or start with a completely new situation.

## 📡 API Usage

### Create Apology Endpoint

**Endpoint:** `POST /create-apology`

> **💡 Tip:** For a user-friendly interface, use the [Dashboard](#-dashboard-access) instead of direct API calls.

**Request Body:**
```json
{
  "situation": "I forgot our anniversary dinner and made other plans",
  "recipient_name": "Sarah",
  "relationship_type": "romantic",
  "severity": 8,
  "recipient_preferences": {
    "favorite_flowers": "roses",
    "favorite_cuisine": "italian",
    "loves_surprises": true
  },
  "budget": 200.0,
  "location": "New York, NY"
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/create-apology" \
  -H "Content-Type: application/json" \
  -d '{
    "situation": "I forgot our anniversary dinner and made other plans",
    "recipient_name": "Sarah",
    "relationship_type": "romantic",
    "severity": 8,
    "recipient_preferences": {
      "favorite_flowers": "roses",
      "favorite_cuisine": "italian",
      "loves_surprises": true
    },
    "budget": 200.0,
    "location": "New York, NY"
  }'
```

## 🏗️ Architecture

### Core Components

- **Apology Agents**: AI-powered agents that generate apology strategies
- **Models**: Data models for apology context and relationships
- **Tools**: Specialized tools for gift finding, restaurant booking, and more

### Directory Structure

```
ApologyAgent/
├── apology_agents/     # AI agents for apology generation
├── models/             # Data models and schemas
├── tools/              # Utility tools and services
├── app.py              # Main application entry point
├── start.py            # Application startup script
└── requirements.txt    # Python dependencies
```

## 🛠️ Configuration

The system can be configured through environment variables or configuration files. Key settings include:

- API endpoints for external services
- Budget limits and preferences
- Location-based service availability
- AI model parameters

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


## 🔮 Roadmap

- [ ] Enhanced AI models for better apology generation
- [ ] Integration with more gift and service providers
- [ ] Mobile application
- [ ] Multi-language support
- [ ] Advanced analytics and insights

---

**Note:** This is a demonstration project. For production use, please ensure proper security measures and API key management.