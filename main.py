import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import User, get_db, init_db


SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class RegisterModel(BaseModel):
    email: str
    password: str


class PredictInput(BaseModel):
    text: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


app = FastAPI(title="News Authenticity API")


# CORS
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# Serve frontend assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.get("/", response_class=HTMLResponse)
def serve_frontend() -> HTMLResponse:
    frontend_path = os.path.join(BASE_DIR, "frontend.html")
    if not os.path.exists(frontend_path):
        # Basic fallback page
        return HTMLResponse("""
<!DOCTYPE html>
<html>
  <head><meta charset='utf-8'><title>App</title></head>
  <body><h1>Frontend missing</h1><p>Please ensure frontend.html exists.</p></body>
</html>
        """)
    with open(frontend_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/style.css")
def serve_css() -> FileResponse:
    return FileResponse(os.path.join(BASE_DIR, "style.css"))


@app.get("/karthik.js")
def serve_js() -> FileResponse:
    return FileResponse(os.path.join(BASE_DIR, "karthik.js"))


# Authentication routes
@app.post("/auth/register")
def register(user: RegisterModel, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    password_hash = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Predict route (protected)
@app.post("/predict")
def predict(input_data: PredictInput, user: User = Depends(get_current_user)):
    # Placeholder ML logic: simple heuristic by presence of words
    text = input_data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    keywords_fake = ["shocking", "click here", "won't believe", "miracle", "breaking!!!"]
    score = 0
    lowered = text.lower()
    for kw in keywords_fake:
        if kw in lowered:
            score += 1

    confidence = min(0.95, 0.5 + 0.1 * score)
    label = "Fake" if score >= 2 else "Real"
    return {"label": label, "confidence": confidence}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

