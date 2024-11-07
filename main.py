from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import summarize
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Pomelo Credit Card Summary API")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Define Pydantic models for input
class Event(BaseModel):
    eventType: str
    eventTime: int
    txnId: str
    amount: Optional[int] = None

class SummaryRequest(BaseModel):
    creditLimit: int
    events: List[Event]

# Define Pydantic model for response
class SummaryResponse(BaseModel):
    available_credit: str
    payable_balance: str
    pending_transactions: List[str]
    settled_transactions: List[str]

@app.post("/summarize", response_model=SummaryResponse)
def summarize_credit_card(request: SummaryRequest):
    try:
        input_json = request.json()
        summary = summarize.summarize(input_json)
        lines = summary.split('\n')
        
        # Extract Available credit and Payable balance
        available_credit_line = lines[0]
        payable_balance_line = lines[1]
        
        # Extract Pending transactions
        pending_transactions = []
        settled_transactions = []
        current_section = None
        for line in lines[3:]:
            if line == "Settled transactions:":
                current_section = "settled"
                continue
            if line.startswith("Settled transactions:"):
                current_section = "settled"
                continue
            if line.startswith("Pending transactions:"):
                current_section = "pending"
                continue
            if current_section == "pending":
                if line.strip() != "":
                    pending_transactions.append(line)
            elif current_section == "settled":
                if line.strip() != "":
                    settled_transactions.append(line)
        
        return SummaryResponse(
            available_credit=available_credit_line.replace("Available credit: ", ""),
            payable_balance=payable_balance_line.replace("Payable balance: ", ""),
            pending_transactions=pending_transactions,
            settled_transactions=settled_transactions
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Root endpoint to serve the web interface
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/info", response_class=HTMLResponse, tags=["info"])
def get_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})
