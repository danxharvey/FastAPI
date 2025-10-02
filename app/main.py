# Import libraries
from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.auth.main import router as user_endpoints
import yaml
import os

# Load config.yaml
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    full_config = yaml.safe_load(f)
    config = full_config[full_config.get("current_env")]

# Load endpoints YAML
ep_path = os.path.join(os.path.dirname(__file__), "endpoints.yaml")
with open(ep_path) as f:
    ep_config = yaml.safe_load(f)["endpoints"]

# Initialize FastAPI app using config.yaml settings
app = FastAPI(
    title=config["title"],
    description=config["description"],
    version=config["version"],
    docs_url=config["docs_url"],
    redoc_url=config["redoc_url"])
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



# Homepage route with login/logout message support
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, msg: str = None):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "api_title": app.title,
            "api_description": app.description,
            "api_version": app.version,
            "endpoints": ep_config
        }
    )

# Register the users router
app.include_router(user_endpoints)

# Health check route
@app.get("/health", response_class=JSONResponse)
def health_check():
    # Check if template directory exists as a simple health indicator
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    templates_ok = os.path.isdir(templates_dir)
    return {
        "status": "ok" if templates_ok else "error",
        "app": config["title"],
        "version": config["version"],
        "templates_dir": "ok" if templates_ok else "missing"
    }