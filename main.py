from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
  return {"status": "ok"}

@app.get("/")
async def health():
  return {"message": "Hello World"}

@app.get("/render_test")
async def render_test():
  return {"message" : "test completed"}