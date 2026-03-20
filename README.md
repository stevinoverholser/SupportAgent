# Bookly Customer Support Agent

A prototype AI customer support agent for Bookly, a fictional online bookstore.

## Supported workflows
- Order status inquiries
- Return / refund requests
- FAQ support for shipping, returns, and password reset

## Tech stack
- Python
- Streamlit
- OpenAI API
- Mocked backend tools

## Setup

### 1. Create and activate a virtual environment
```
bash
python -m venv venv
venv\Scripts\activate
```
### 1. Create and activate a virtual environment
```
pip install -r requirements.txt
```
### 3. Add environment variables
- Create a `.env` file in project root
```
OPENAI_API_KEY=your_api_key_here
```
### 4. Run the app
```
streamlit run app.py
```
Example prompts
- Where is order 1001?
- I want to return order 1002
- How long does shipping take?
- How do I reset my password?
